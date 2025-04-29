import numpy as np
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..models.crawler import URL
from .tokenizer_service import tokenize, get_token_frequencies


class SearchService:
    def __init__(self, db: Session):
        self.db = db
        self.vocabulary = set()
        self.document_frequency = {}
        self._build_vocabulary()

    def _build_vocabulary(self):
        urls = self.db.query(URL).filter(URL.text_content.isnot(None)).all()
        for url in urls:
            tokens = tokenize(url.text_content)
            self.vocabulary.update(tokens)
            term_freq = get_token_frequencies(tokens)
            for term in term_freq:
                self.document_frequency[term] = self.document_frequency.get(term, 0) + 1

    def _calculate_query_vector(self, query: str) -> np.ndarray:
        tokens = tokenize(query)
        term_frequencies = get_token_frequencies(tokens)
        total_docs = self.db.query(URL).count()

        vector = []
        for term in sorted(self.vocabulary):
            tf = term_frequencies.get(term, 0) / len(tokens) if tokens else 0
            idf = np.log(total_docs / (self.document_frequency.get(term, 0) + 1))
            vector.append(tf * idf)

        vector = np.array(vector)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector

    def _calculate_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        return np.dot(vec1, vec2)

    def _get_snippet(
        self, text: str, query_terms: List[str], max_length: int = 200
    ) -> str:
        text = text.lower()
        query_terms = [term.lower() for term in query_terms]

        # Find the first occurrence of any query term
        positions = []
        for term in query_terms:
            pos = text.find(term)
            if pos != -1:
                positions.append(pos)

        if not positions:
            return text[:max_length] + "..."

        # Get context around the first match
        start_pos = max(0, min(positions) - 50)
        end_pos = min(len(text), start_pos + max_length)

        snippet = text[start_pos:end_pos]
        if start_pos > 0:
            snippet = "..." + snippet
        if end_pos < len(text):
            snippet = snippet + "..."

        return snippet

    def search(self, query: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        query_vector = self._calculate_query_vector(query)
        query_terms = tokenize(query)

        results = []
        urls = (
            self.db.query(URL)
            .filter(URL.text_content.isnot(None), URL.document_vector.isnot(None))
            .all()
        )

        for url in urls:
            doc_vector = np.frombuffer(url.document_vector, dtype=np.float64)
            similarity = self._calculate_cosine_similarity(query_vector, doc_vector)

            if similarity > 0:
                snippet = self._get_snippet(url.text_content, query_terms)
                results.append(
                    {
                        "url": url.url,
                        "title": url.title,
                        "snippet": snippet,
                        "similarity": float(similarity),
                        "meta_description": url.meta_description,
                        "important_headings": url.important_headings,
                    }
                )

        # Sort by similarity score
        results.sort(key=lambda x: x["similarity"], reverse=True)

        # Paginate results
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = results[start_idx:end_idx]

        return {
            "query": query,
            "total_results": len(results),
            "page": page,
            "per_page": per_page,
            "total_pages": (len(results) + per_page - 1) // per_page,
            "results": paginated_results,
        }

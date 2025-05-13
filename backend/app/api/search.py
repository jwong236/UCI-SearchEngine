import numpy as np
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database.models import Document, Term, InvertedIndex
from .tokenizer import tokenize


class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def _get_document_frequency(self, term: str) -> int:
        term_record = self.db.query(Term).filter(Term.term == term).first()
        if term_record and term_record.stats:
            return term_record.stats.document_frequency
        return 0

    def _get_documents_with_term(self, term: str) -> List[Document]:
        term_record = self.db.query(Term).filter(Term.term == term).first()
        if not term_record:
            return []

        doc_ids = [entry.document_id for entry in term_record.inverted_index_entries]
        return self.db.query(Document).filter(Document.id.in_(doc_ids)).all()

    def _get_term_positions(self, term: str, doc_id: int) -> List[int]:
        term_record = self.db.query(Term).filter(Term.term == term).first()
        if not term_record:
            return []

        return [
            entry.position
            for entry in self.db.query(InvertedIndex)
            .filter(
                InvertedIndex.term_id == term_record.id,
                InvertedIndex.document_id == doc_id,
            )
            .all()
        ]

    def _get_snippet(
        self, text: str, query_terms: List[str], max_length: int = 200
    ) -> str:
        text = text.lower()
        query_terms = [term.lower() for term in query_terms]

        positions = []
        for term in query_terms:
            pos = text.find(term)
            if pos != -1:
                positions.append(pos)

        if not positions:
            return text[:max_length] + "..."

        start_pos = max(0, min(positions) - 50)
        end_pos = min(len(text), start_pos + max_length)

        snippet = text[start_pos:end_pos]
        if start_pos > 0:
            snippet = "..." + snippet
        if end_pos < len(text):
            snippet = snippet + "..."

        return snippet

    def search(self, query: str, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        query_terms = tokenize(query)
        if not query_terms:
            return {
                "query": query,
                "total_results": 0,
                "page": page,
                "per_page": per_page,
                "total_pages": 0,
                "results": [],
            }

        all_docs = set()
        for term in query_terms:
            docs = self._get_documents_with_term(term)
            all_docs.update(docs)

        results = []
        total_docs = self.db.query(Document).count() or 1

        for doc in all_docs:
            score = 0
            for term in query_terms:
                positions = self._get_term_positions(term, doc.id)
                tf = (
                    len(positions) / len(tokenize(doc.text_content or ""))
                    if doc.text_content
                    else 0
                )

                df = self._get_document_frequency(term)
                idf = np.log(total_docs / (df + 1))

                score += tf * idf

            if score > 0:
                snippet = self._get_snippet(doc.text_content or "", query_terms)
                results.append(
                    {
                        "url": doc.url,
                        "title": doc.title,
                        "snippet": snippet,
                        "score": float(score),
                    }
                )

        results.sort(key=lambda x: x["score"], reverse=True)

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

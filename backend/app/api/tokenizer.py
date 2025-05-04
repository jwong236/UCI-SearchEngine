import re
from typing import Dict, List


def tokenize(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.split()


def get_token_frequencies(tokens: List[str]) -> Dict[str, int]:
    freq = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1
    return freq


def process_text(text: str) -> Dict[str, int]:
    tokens = tokenize(text)
    return get_token_frequencies(tokens)

import re
from typing import Dict, List


def tokenize(text: str) -> List[str]:
    """
    Tokenize text into words, removing special characters and converting to lowercase.

    Args:
        text: Input text to tokenize

    Returns:
        List of tokens
    """
    # Convert to lowercase
    text = text.lower()

    # Remove special characters and extra whitespace
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Split into tokens
    return text.split()


def get_token_frequencies(tokens: List[str]) -> Dict[str, int]:
    """
    Calculate frequency of each token in the list.

    Args:
        tokens: List of tokens

    Returns:
        Dictionary mapping tokens to their frequencies
    """
    freq = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1
    return freq


def process_text(text: str) -> Dict[str, int]:
    """
    Process text by tokenizing and calculating frequencies.

    Args:
        text: Input text to process

    Returns:
        Dictionary mapping tokens to their frequencies
    """
    tokens = tokenize(text)
    return get_token_frequencies(tokens)

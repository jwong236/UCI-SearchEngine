def _generate_hash(word: str) -> str:
    """
    Using a polynomial hash function (base^(lengthOfWord) * letter_mapping),
    generates an 8-bit hash value.
    Credits to Shindler's ICS 46 for hash function
    """
    base = 37
    mod = 4095  # largest value that can be represented by 12-bits

    hash = 0
    word = word.lower()
    for i in range(len(word)):
        ascii_rep = ord(word[i]) - ord("a") + 1
        ascii_rep %= mod
        temp = base ** len(word)
        temp = temp % mod
        hash += ascii_rep * temp

    return "{0:012b}".format(hash)


def generate_fingerprint(token_freq: dict) -> str:
    """Generate a fingerprint from a dictionary of token frequencies."""
    hash_dict = dict()

    # generating 12-bit hash values
    for token in token_freq.keys():
        hash_dict[token] = _generate_hash(token)

    # vector formed by summing weights
    summing_weights = list()
    for i in range(12):
        sum_weight = 0
        for token in hash_dict.keys():
            _multiplier = 1 if int(hash_dict[token][i]) else -1
            sum_weight += _multiplier * token_freq[token]
        summing_weights.append(sum_weight)

    assert len(summing_weights) == 12, "Incorrect calculation..."

    # 12-bit fingerprint formed from summing_weights
    fingerprint = ""
    for val in summing_weights:
        fingerprint += "1" if val > 0 else "0"

    return fingerprint


def calc_similarity(f1: str, f2: str, threshold: float = 0.96) -> bool:
    """
    Calculate similarity between two fingerprints.

    Args:
        f1: First fingerprint
        f2: Second fingerprint
        threshold: Similarity threshold (default: 0.96)

    Returns:
        bool: True if similarity is above threshold
    """
    assert len(f1) == len(f2), "Fingerprints are not same length"

    similar_count = 0
    for i in range(12):
        if f1[i] == f2[i]:
            similar_count += 1

    return (similar_count / 12) >= threshold

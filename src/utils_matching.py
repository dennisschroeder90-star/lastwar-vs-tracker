import re
from typing import List, Tuple, Optional


# ----------------------------------------
# NAME NORMALIZATION
# ----------------------------------------

def normalize_name(name: str) -> str:
    """
    Normalize player names for comparison:
    - lowercase
    - remove extra spaces
    - strip
    """
    if not name:
        return ""
    name = name.strip().lower()
    name = re.sub(r"\s+", " ", name)
    return name


# ----------------------------------------
# LEVENSHTEIN DISTANCE
# ----------------------------------------

def levenshtein(a: str, b: str) -> int:
    """
    Compute Levenshtein distance between two strings.
    """
    if a == b:
        return 0

    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    prev_row = list(range(len(b) + 1))

    for i, ca in enumerate(a, start=1):
        current_row = [i]
        for j, cb in enumerate(b, start=1):
            insert_cost = current_row[j - 1] + 1
            delete_cost = prev_row[j] + 1
            replace_cost = prev_row[j - 1] + (0 if ca == cb else 1)
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        prev_row = current_row

    return prev_row[-1]


# ----------------------------------------
# SIMILARITY SCORE
# ----------------------------------------

def similarity(a: str, b: str) -> float:
    """
    Returns similarity score between 0 and 1.
    """
    a_norm = normalize_name(a)
    b_norm = normalize_name(b)

    if not a_norm and not b_norm:
        return 1.0

    if not a_norm or not b_norm:
        return 0.0

    dist = levenshtein(a_norm, b_norm)
    max_len = max(len(a_norm), len(b_norm))

    if max_len == 0:
        return 1.0

    return 1.0 - dist / max_len


# ----------------------------------------
# BEST MATCH FINDER
# ----------------------------------------

def best_match_player_name(
    raw_name: str,
    candidates: List[Tuple[int, str, List[str]]],
    threshold: float = 0.85,
) -> Optional[int]:
    """
    candidates format:
    [
        (player_id, current_name, alias_list),
        ...
    ]

    Returns matching player_id or None.
    """

    raw_norm = normalize_name(raw_name)

    # 1️⃣ Exact match pass (fast & safe)
    for player_id, current_name, aliases in candidates:
        if raw_norm == normalize_name(current_name):
            return player_id

        for alias in aliases or []:
            if raw_norm == normalize_name(alias):
                return player_id

    # 2️⃣ Fuzzy match pass
    best_id = None
    best_score = 0.0

    for player_id, current_name, aliases in candidates:
        score = similarity(raw_name, current_name)

        if score > best_score:
            best_score = score
            best_id = player_id

        for alias in aliases or []:
            score_alias = similarity(raw_name, alias)
            if score_alias > best_score:
                best_score = score_alias
                best_id = player_id

    if best_score >= threshold:
        return best_id

    return None
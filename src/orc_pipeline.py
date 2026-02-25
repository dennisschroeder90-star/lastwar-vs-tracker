import re
import numpy as np
import cv2
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Optional OCR engines
_EASYOCR_AVAILABLE = False
_PYTESS_AVAILABLE = False

try:
    import easyocr
    _EASYOCR_AVAILABLE = True
except Exception:
    _EASYOCR_AVAILABLE = False

try:
    import pytesseract
    _PYTESS_AVAILABLE = True
except Exception:
    _PYTESS_AVAILABLE = False


@dataclass
class ParsedLine:
    player_name: str
    points: int
    confidence: float
    raw_line: str
    points_raw: str


# ------------------------------------
# IMAGE PREPROCESSING
# ------------------------------------

def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """
    Basic preprocessing for scoreboard screenshots.
    Works on Streamlit Cloud.
    """
    img_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Could not decode image")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    gray = cv2.medianBlur(gray, 3)

    _, thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return thresh


# ------------------------------------
# OCR EXTRACTION
# ------------------------------------

def ocr_extract_lines(image: np.ndarray) -> List[Tuple[str, float]]:
    """
    Returns list of (text, confidence).
    """

    results = []

    if _EASYOCR_AVAILABLE:
        reader = easyocr.Reader(["en"], gpu=False)
        out = reader.readtext(image, detail=1, paragraph=False)

        for _, text, conf in out:
            text = text.strip()
            if text:
                results.append((text, float(conf)))

        return results

    if _PYTESS_AVAILABLE:
        data = pytesseract.image_to_data(
            image, output_type=pytesseract.Output.DICT
        )

        n = len(data["text"])

        for i in range(n):
            txt = data["text"][i].strip()
            conf = float(data["conf"][i]) / 100 if data["conf"][i] != "-1" else 0.5
            if txt:
                results.append((txt, conf))

        return results

    raise RuntimeError("No OCR engine available.")


# ------------------------------------
# PARSER
# ------------------------------------

_POINTS_REGEX = re.compile(
    r"""
    ^\s*
    (?P<name>.+?)
    \s+
    (?P<points>[0-9][0-9\.,\s]*[0-9])
    \s*$
    """,
    re.VERBOSE,
)


def parse_points(raw: str) -> Optional[int]:
    raw = raw.strip()
    clean = re.sub(r"[^\d]", "", raw)
    if not clean:
        return None
    try:
        return int(clean)
    except Exception:
        return None


def parser_confidence(name: str, points: Optional[int]) -> float:
    """
    Heuristic confidence score.
    """
    if not name or points is None:
        return 0.0

    score = 0.6

    if len(name) >= 3:
        score += 0.15

    if points > 0:
        score += 0.15

    if points > 1000:
        score += 0.1

    return min(score, 1.0)


def parse_ocr_lines(lines: List[Tuple[str, float]]) -> List[ParsedLine]:
    """
    Convert raw OCR lines into structured entries.
    """

    parsed = []

    for raw_text, ocr_conf in lines:
        raw_text = re.sub(r"\s+", " ", raw_text.strip())

        match = _POINTS_REGEX.match(raw_text)
        if not match:
            continue

        name = match.group("name").strip()
        points_raw = match.group("points").strip()
        points = parse_points(points_raw)

        if points is None:
            continue

        p_conf = parser_confidence(name, points)

        combined_conf = 0.6 * ocr_conf + 0.4 * p_conf

        parsed.append(
            ParsedLine(
                player_name=name,
                points=points,
                confidence=float(combined_conf),
                raw_line=raw_text,
                points_raw=points_raw,
            )
        )

    return parsed
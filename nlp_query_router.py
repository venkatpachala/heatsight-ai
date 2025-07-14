"""Simple rule-based query router mapping text to tool categories."""
import re
from typing import Tuple


CATEGORIES = {
    'performance': ['sales', 'revenue', 'conversion'],
    'behavior': ['dwell', 'path', 'journey'],
    'stock': ['stock', 'restock', 'inventory'],
    'prediction': ['predict', 'forecast'],
    'optimization': ['optimize', 'placement', 'layout']
}


def classify_query(text: str) -> Tuple[str, str]:
    text_l = text.lower()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if re.search(rf"\b{kw}\b", text_l):
                return cat, kw
    return 'general', ''

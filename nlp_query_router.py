"""Simple rule-based query router mapping text to tool categories."""
import re
from typing import Tuple


CATEGORIES = {
    'zone': ['zone', 'footfall'],
    'conversion': ['conversion'],
    'relocate': ['relocate'],
    'simulate': ['simulate', 'what-if'],
    'holiday': ['holiday', 'festival'],
    'checkout': ['checkout'],
    'roi': ['roi', 'underperform'],
    'performance': ['sales', 'revenue'],
    'behavior': ['dwell', 'path', 'journey'],
    'stock': ['stock', 'restock', 'inventory'],
    'optimization': ['optimize', 'placement', 'layout']
}


def classify_query(text: str) -> Tuple[str, str]:
    text_l = text.lower()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if re.search(rf"\b{kw}\b", text_l):
                return cat, kw
    return 'general', ''

"""Comptage de tokens.

L'estimation par défaut (environ 4 caractères par token) est volontairement
simple et déterministe. Pour un budget exact, injecter un compteur réel
(tiktoken ou tokenizer du fournisseur) via HeuristicSelector.token_counter.
"""
from __future__ import annotations

import math
from typing import Callable

TokenCounter = Callable[[str], int]


def estimate_tokens(text: str) -> int:
    """Estimation déterministe : environ 4 caractères par token."""
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))

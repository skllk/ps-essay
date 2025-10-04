from __future__ import annotations

import re
from typing import List

WORD_PATTERN = re.compile(r"[A-Za-z']+")


def tokenize(text: str) -> List[str]:
    return WORD_PATTERN.findall(text.lower())


def split_into_sentences(text: str) -> List[str]:
    cleaned = text.replace("\r", "")
    potential = re.split(r"(?<=[.!?])\s+", cleaned)
    sentences = [segment.strip() for segment in potential if segment.strip()]
    if not sentences and text.strip():
        return [text.strip()]
    return sentences


def split_into_paragraphs(text: str) -> List[str]:
    cleaned = text.replace("\r", "")
    paragraphs = [segment.strip() for segment in cleaned.split("\n\n") if segment.strip()]
    if not paragraphs and text.strip():
        return [text.strip()]
    return paragraphs


def count_syllables(word: str) -> int:
    word = word.lower()
    vowels = "aeiouy"
    syllables = 0
    previous_is_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_is_vowel:
            syllables += 1
        previous_is_vowel = is_vowel
    if word.endswith("e") and syllables > 1:
        syllables -= 1
    return max(syllables, 1)


def moving_average(values: List[float], window: int = 2) -> List[float]:
    if window <= 0:
        raise ValueError("Window size must be positive")
    if not values:
        return []
    averaged: List[float] = []
    for index in range(len(values)):
        start = max(0, index - window + 1)
        subset = values[start : index + 1]
        averaged.append(sum(subset) / len(subset))
    return averaged

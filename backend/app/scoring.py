from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from .text import count_syllables, split_into_paragraphs, split_into_sentences, tokenize


@dataclass
class ScoreBreakdown:
    content: float
    structure: float
    language: float
    integrity: float

    def as_percentage(self) -> Dict[str, float]:
        return {
            "content": round(self.content * 100, 2),
            "structure": round(self.structure * 100, 2),
            "language": round(self.language * 100, 2),
            "integrity": round(self.integrity * 100, 2),
        }

    def weighted_total(self, weights: Dict[str, float]) -> float:
        return round(
            (self.content * weights["content"])
            + (self.structure * weights["structure"])
            + (self.language * weights["language"])
            + (self.integrity * weights["integrity"]),
            4,
        )


def min_max_scale(value: float, min_value: float, max_value: float) -> float:
    if max_value - min_value == 0:
        return 0.0
    return max(0.0, min(1.0, (value - min_value) / (max_value - min_value)))


def type_token_ratio(tokens: List[str]) -> float:
    if not tokens:
        return 0.0
    unique_tokens = set(tokens)
    return len(unique_tokens) / len(tokens)


def flesch_reading_ease(sentences: List[str], tokens: List[str]) -> float:
    total_sentences = max(len(sentences), 1)
    total_words = max(len(tokens), 1)
    total_syllables = sum(count_syllables(token) for token in tokens)

    words_per_sentence = total_words / total_sentences
    syllables_per_word = total_syllables / total_words

    return 206.835 - (1.015 * words_per_sentence) - (84.6 * syllables_per_word)


def paragraph_focus(paragraphs: List[str]) -> float:
    focus_scores: List[float] = []
    for paragraph in paragraphs:
        sentences = split_into_sentences(paragraph)
        if not sentences:
            continue
        tokens = tokenize(paragraph)
        ratios = [type_token_ratio(tokenize(sentence)) for sentence in sentences if tokenize(sentence)]
        if not ratios:
            continue
        focus_scores.append(sum(ratios) / len(ratios))
    if not focus_scores:
        return 0.0
    return sum(focus_scores) / len(focus_scores)


def compute_scores(document: str, application_level: str | None = None) -> Tuple[ScoreBreakdown, Dict[str, float], Dict[str, List[Dict[str, float]]]]:
    paragraphs = split_into_paragraphs(document)
    sentences = split_into_sentences(document)
    tokens = tokenize(document)

    paragraph_count = len(paragraphs)
    sentence_count = len(sentences)
    token_count = len(tokens)

    paragraph_length_scores = [len(tokenize(p)) for p in paragraphs if p.strip()]
    avg_paragraph_length = sum(paragraph_length_scores) / len(paragraph_length_scores) if paragraph_length_scores else 0

    # Content score emphasises coverage and richness.
    content_score = min_max_scale(token_count, 200, 900)
    content_score *= 0.7 + 0.3 * min_max_scale(type_token_ratio(tokens), 0.25, 0.6)

    # Structure score rewards balanced paragraphing and sentence count.
    structure_balance = min_max_scale(paragraph_count, 3, 7)
    avg_sentence_length = token_count / max(sentence_count, 1)
    sentence_balance = 1 - abs(avg_sentence_length - 22) / 22
    structure_score = max(0.0, min(1.0, 0.6 * structure_balance + 0.4 * max(0.0, sentence_balance)))

    # Language score uses readability and lexical diversity.
    reading_ease = flesch_reading_ease(sentences, tokens)
    readability_score = min_max_scale(reading_ease, 30, 70)
    lexical_diversity = min_max_scale(type_token_ratio(tokens), 0.3, 0.7)
    language_score = max(0.0, min(1.0, 0.5 * readability_score + 0.5 * lexical_diversity))

    # Integrity score is computed upstream using AI detection; placeholder baseline is neutral 0.7.
    integrity_score = 0.7

    breakdown = ScoreBreakdown(
        content=content_score,
        structure=structure_score,
        language=language_score,
        integrity=integrity_score,
    )

    if application_level == "UG":
        weights = {"content": 0.4, "structure": 0.25, "language": 0.25, "integrity": 0.1}
    elif application_level in {"MS", "PHD"}:
        weights = {"content": 0.35, "structure": 0.25, "language": 0.2, "integrity": 0.2}
    else:
        weights = {"content": 0.35, "structure": 0.25, "language": 0.25, "integrity": 0.15}

    dimension_heatmap = {
        "content": [{"index": idx, "weight": min_max_scale(len(tokenize(p)), 80, 220)} for idx, p in enumerate(paragraphs)],
        "structure": [
            {
                "index": idx,
                "cohesion": min_max_scale(paragraph_focus([p]), 0.2, 0.8),
            }
            for idx, p in enumerate(paragraphs)
        ],
        "language": [
            {
                "index": idx,
                "readability": min_max_scale(
                    flesch_reading_ease(split_into_sentences(p), tokenize(p)),
                    20,
                    80,
                ),
            }
            for idx, p in enumerate(paragraphs)
        ],
    }

    summary_stats = {
        "word_count": token_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "avg_sentence_length": round(avg_sentence_length, 2),
        "avg_paragraph_length": round(avg_paragraph_length, 2),
        "reading_ease": round(reading_ease, 2),
    }

    return breakdown, weights, {"heatmap": dimension_heatmap, "summary": summary_stats}

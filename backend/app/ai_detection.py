from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, List

from .text import split_into_paragraphs, split_into_sentences, tokenize


@dataclass
class SentenceRisk:
    text: str
    start: int
    end: int
    generated_prob: float


@dataclass
class ParagraphRisk:
    index: int
    generated_prob: float


@dataclass
class DocumentRisk:
    completely_generated_prob: float
    overall_variance: float


@dataclass
class DetectionResult:
    document: DocumentRisk
    paragraphs: List[ParagraphRisk]
    sentences: List[SentenceRisk]

    def to_payload(self) -> Dict[str, object]:
        return {
            "document": {
                "completely_generated_prob": round(self.document.completely_generated_prob, 4),
                "overall_variance": round(self.document.overall_variance, 4),
            },
            "paragraphs": [
                {"index": item.index, "completely_generated_prob": round(item.generated_prob, 4)}
                for item in self.paragraphs
            ],
            "sentences": [
                {
                    "text": item.text,
                    "start": item.start,
                    "end": item.end,
                    "generated_prob": round(item.generated_prob, 4),
                }
                for item in self.sentences
            ],
        }


def _calc_sentence_probability(sentence: str) -> float:
    tokens = tokenize(sentence)
    if not tokens:
        return 0.0
    avg_word_length = sum(len(token) for token in tokens) / len(tokens)
    diversity = len(set(tokens)) / len(tokens)
    complex_word_ratio = sum(1 for token in tokens if len(token) > 8) / len(tokens)

    machine_like = 0.4 * (1 - diversity) + 0.4 * max(0.0, 1 - complex_word_ratio * 3) + 0.2 * max(0.0, 1 - avg_word_length / 5)
    return max(0.0, min(1.0, machine_like))


def analyze_document(document: str) -> DetectionResult:
    paragraphs = split_into_paragraphs(document)
    sentences = split_into_sentences(document)

    sentence_results: List[SentenceRisk] = []
    cursor = 0
    for sentence in sentences:
        start_index = document.find(sentence, cursor)
        if start_index == -1:
            start_index = cursor
        end_index = start_index + len(sentence)
        cursor = end_index
        probability = _calc_sentence_probability(sentence)
        sentence_results.append(
            SentenceRisk(text=sentence, start=start_index, end=end_index, generated_prob=probability)
        )

    paragraph_probs: List[ParagraphRisk] = []
    for index, paragraph in enumerate(paragraphs):
        sentences_in_paragraph = split_into_sentences(paragraph)
        if sentences_in_paragraph:
            prob = mean(_calc_sentence_probability(s) for s in sentences_in_paragraph)
        else:
            prob = 0.0
        paragraph_probs.append(ParagraphRisk(index=index, generated_prob=prob))

    sentence_probabilities = [item.generated_prob for item in sentence_results] or [0.0]
    document_prob = mean(sentence_probabilities)
    variance = mean((prob - document_prob) ** 2 for prob in sentence_probabilities)

    document_risk = DocumentRisk(completely_generated_prob=document_prob, overall_variance=variance)

    return DetectionResult(document=document_risk, paragraphs=paragraph_probs, sentences=sentence_results)

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

SAMPLE_TEXT = (
    "I have spent the past four years exploring human-centered design through studio courses, "
    "internships, and independent research. Each project challenged me to translate user insights "
    "into tangible prototypes, from assistive devices to educational platforms. My goal is to "
    "contribute to accessible design research at the graduate level, collaborating with mentors who "
    "champion inclusive technology."
)


client = TestClient(app)


def test_analyze_endpoint_returns_scores_and_detection() -> None:
    response = client.post(
        "/api/analyze",
        json={
            "document": SAMPLE_TEXT,
            "application_level": "MS",
            "target_major": "Human-Computer Interaction",
            "school_preferences": ["CMU", "UW"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "total_score" in payload
    assert set(payload["dimension_scores"].keys()) == {"content", "structure", "language", "integrity"}
    assert payload["ai_detection"]["document"]["completely_generated_prob"] >= 0
    assert payload["insights"]


def test_ai_detect_endpoint_returns_sentence_probabilities() -> None:
    response = client.post("/api/ai-detect", json={"document": SAMPLE_TEXT})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ai_detection"]["sentences"]
    assert all("generated_prob" in sentence for sentence in payload["ai_detection"]["sentences"])


def test_report_endpoint_returns_saved_payload() -> None:
    analyze_response = client.post("/api/analyze", json={"document": SAMPLE_TEXT})
    analysis_id = analyze_response.json()["analysis_id"]

    report_response = client.get(f"/api/report/{analysis_id}")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["payload"]["dimension_scores"]

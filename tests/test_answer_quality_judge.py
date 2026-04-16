import json

import pytest

from src.evaluation import AnswerQualityJudge, create_mock_judge_callable, evaluate_all, parse_judge_response


def test_parse_judge_response_normalizes_scores():
    parsed = parse_judge_response(
        json.dumps(
            {
                "groundedness": 5,
                "correctness": 4,
                "completeness": 3,
                "overall": 4,
                "reasoning": "Mostly solid answer.",
            }
        )
    )

    assert parsed == {
        "groundedness": 1.0,
        "correctness": 0.8,
        "completeness": 0.6,
        "answer_quality": 0.8,
        "judge_reasoning": "Mostly solid answer.",
    }


def test_parse_judge_response_rejects_invalid_payload():
    with pytest.raises(ValueError):
        parse_judge_response('{"groundedness": 6}')


def test_answer_quality_judge_scores_result():
    judge = AnswerQualityJudge(create_mock_judge_callable())
    result = {
        "answer": "The paper reports a strong benchmark result.",
        "retrieved_chunks": [
            {"section": "results", "text": "The model improved benchmark performance.", "metadata": {}}
        ],
    }
    qa_pair = {
        "question": "What was the main result?",
        "gold_answer": "The model improved benchmark performance.",
        "relevant_sections": ["results"],
    }

    scores = judge.score(result, qa_pair)

    assert scores["groundedness"] == 1.0
    assert scores["correctness"] == 0.8
    assert scores["completeness"] == 0.8
    assert scores["answer_quality"] == 0.8
    assert "raw_response" in scores


def test_evaluate_all_includes_answer_quality_aggregate_when_judge_present():
    judge = AnswerQualityJudge(create_mock_judge_callable())
    results = [
        {
            "answer": "The paper reports a strong benchmark result.",
            "retrieved_chunks": [
                {"section": "results", "text": "The model improved benchmark performance.", "metadata": {"source": "paper-a"}}
            ],
        }
    ]
    qa_pairs = [
        {
            "id": "q1",
            "question": "What was the main result?",
            "gold_answer": "The model improved benchmark performance.",
            "relevant_sections": ["results"],
            "source": "paper-a",
        }
    ]

    evaluation = evaluate_all(results, qa_pairs, judge=judge)

    assert evaluation["aggregate"]["answer_quality"] == 0.8
    assert evaluation["aggregate"]["groundedness"] == 1.0
    assert evaluation["per_question"][0]["question_id"] == "q1"
    assert evaluation["per_question"][0]["judge_reasoning"]

from src.evaluation.metrics import evaluate_all, is_refusal_answer


def test_is_refusal_answer_detects_common_abstentions():
    assert is_refusal_answer("I couldn't find any relevant information in the paper.") == 1.0
    assert is_refusal_answer("The paper does not provide this information.") == 1.0
    assert is_refusal_answer("The model uses 8 attention heads.") == 0.0


def test_evaluate_all_reports_answerable_slices_and_refusal_metrics():
    results = [
        {
            "answer": "The model uses 8 attention heads.",
            "retrieved_chunks": [
                {"section": "methods", "text": "The model uses 8 attention heads.", "metadata": {"source": "paper-a"}}
            ],
        },
        {
            "answer": "The paper does not provide the optimizer.",
            "retrieved_chunks": [
                {"section": "methods", "text": "Model architecture details are provided.", "metadata": {"source": "paper-a"}}
            ],
        },
    ]
    qa_pairs = [
        {
            "id": "q1",
            "question": "How many attention heads are used?",
            "gold_answer": "The model uses 8 attention heads.",
            "relevant_sections": ["methods"],
            "source": "paper-a",
            "is_answerable": True,
        },
        {
            "id": "q2",
            "question": "Which optimizer was used?",
            "gold_answer": "The paper does not provide the optimizer.",
            "relevant_sections": [],
            "source": "paper-a",
            "is_answerable": False,
        },
    ]

    evaluation = evaluate_all(results, qa_pairs)

    assert evaluation["aggregate"]["refusal_rate"] == 0.5
    assert evaluation["aggregate"]["refusal_accuracy"] == 1.0
    assert evaluation["aggregate"]["refusal_precision"] == 1.0
    assert evaluation["aggregate"]["refusal_recall"] == 1.0
    assert evaluation["aggregate"]["refusal_f1"] == 1.0
    assert evaluation["aggregate"]["answerable_count"] == 1
    assert evaluation["aggregate"]["unanswerable_count"] == 1
    assert evaluation["aggregate"]["refusal_true_positives"] == 1
    assert evaluation["aggregate"]["refusal_false_positives"] == 0
    assert evaluation["aggregate"]["refusal_false_negatives"] == 0
    assert evaluation["aggregate"]["refusal_true_negatives"] == 1
    assert evaluation["aggregate"]["false_refusal_rate"] == 0.0
    assert evaluation["aggregate"]["missed_refusal_rate"] == 0.0
    assert evaluation["slices"]["answerable"]["count"] == 1
    assert evaluation["slices"]["answerable"]["share"] == 0.5
    assert evaluation["slices"]["answerable"]["refusal_rate"] == 0.0
    assert evaluation["slices"]["answerable"]["refusal_count"] == 0.0
    assert evaluation["slices"]["unanswerable"]["count"] == 1
    assert evaluation["slices"]["unanswerable"]["share"] == 0.5
    assert evaluation["slices"]["unanswerable"]["refusal_rate"] == 1.0
    assert evaluation["slices"]["unanswerable"]["refusal_count"] == 1.0

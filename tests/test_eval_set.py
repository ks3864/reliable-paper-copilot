from data.eval.eval_set import EVAL_QA_PAIRS, SAMPLE_PAPER_CHUNKS


def test_eval_set_expansion_has_first_batch_size():
    assert len(EVAL_QA_PAIRS) >= 18


def test_eval_pair_ids_are_unique():
    ids = [pair["id"] for pair in EVAL_QA_PAIRS]
    assert len(ids) == len(set(ids))


def test_eval_pairs_reference_existing_sections():
    available_sections = {chunk["section"] for chunk in SAMPLE_PAPER_CHUNKS}

    for pair in EVAL_QA_PAIRS:
        assert pair["relevant_sections"]
        assert set(pair["relevant_sections"]).issubset(available_sections)

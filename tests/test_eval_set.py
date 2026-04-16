from data.eval.eval_set import EVAL_QA_PAIRS, SAMPLE_PAPER_CHUNKS


def test_eval_set_expansion_reaches_phase2_target_size():
    assert len(EVAL_QA_PAIRS) >= 30


def test_eval_pair_ids_are_unique():
    ids = [pair["id"] for pair in EVAL_QA_PAIRS]
    assert len(ids) == len(set(ids))


def test_eval_pairs_reference_existing_sections():
    available_sections = {chunk["section"] for chunk in SAMPLE_PAPER_CHUNKS}

    for pair in EVAL_QA_PAIRS:
        assert pair["relevant_sections"]
        assert set(pair["relevant_sections"]).issubset(available_sections)


def test_eval_pairs_reference_existing_sources():
    available_sources = {chunk["metadata"]["source"] for chunk in SAMPLE_PAPER_CHUNKS}

    for pair in EVAL_QA_PAIRS:
        assert pair["source"] in available_sources


def test_eval_set_contains_multiple_papers():
    available_sources = {chunk["metadata"]["source"] for chunk in SAMPLE_PAPER_CHUNKS}
    assert len(available_sources) >= 2

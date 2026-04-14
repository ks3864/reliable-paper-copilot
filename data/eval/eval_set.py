"""Small Evaluation Set for Phase 1 MVP."""

import json
from pathlib import Path
from typing import List, Dict, Any


SAMPLE_PAPER_CHUNKS = [
    {
        "chunk_id": 0,
        "section": "abstract",
        "text": "This paper presents a novel approach to neural machine translation using transformer architectures. We demonstrate significant improvements over previous seq2seq models.",
        "metadata": {"source": "sample_paper"}
    },
    {
        "chunk_id": 1,
        "section": "introduction",
        "text": "Neural machine translation has seen rapid progress with the advent of attention mechanisms. Previous approaches relied on RNNs which struggled with long-range dependencies.",
        "metadata": {"source": "sample_paper"}
    },
    {
        "chunk_id": 2,
        "section": "methods",
        "text": "We use a transformer model with 6 encoder layers and 6 decoder layers. Each layer uses multi-head self-attention with 8 attention heads. The model has 65 million parameters.",
        "metadata": {"source": "sample_paper"}
    },
    {
        "chunk_id": 3,
        "section": "experiments",
        "text": "We evaluate on the WMT English-German translation task. Our model achieves 28.4 BLEU score, improving over the previous best of 25.8 by 2.6 points.",
        "metadata": {"source": "sample_paper"}
    },
    {
        "chunk_id": 4,
        "section": "results",
        "text": "The transformer model outperforms RNN-based models significantly. We observe a 10% reduction in training time due to parallelization across layers.",
        "metadata": {"source": "sample_paper"}
    },
    {
        "chunk_id": 5,
        "section": "conclusions",
        "text": "We have demonstrated that transformer architectures are highly effective for machine translation. Future work will explore multilingual models and larger datasets.",
        "metadata": {"source": "sample_paper"}
    }
]


EVAL_QA_PAIRS = [
    {
        "id": "q1",
        "question": "What does this paper present?",
        "gold_answer": "A novel approach to neural machine translation using transformer architectures that shows significant improvements over previous seq2seq models.",
        "relevant_sections": ["abstract", "introduction"]
    },
    {
        "id": "q2", 
        "question": "What is the BLEU score achieved?",
        "gold_answer": "28.4 BLEU score on the WMT English-German translation task, improving over the previous best of 25.8 by 2.6 points.",
        "relevant_sections": ["experiments"]
    },
    {
        "id": "q3",
        "question": "How many layers and attention heads does the model have?",
        "gold_answer": "The transformer has 6 encoder layers and 6 decoder layers, with multi-head self-attention using 8 attention heads.",
        "relevant_sections": ["methods"]
    },
    {
        "id": "q4",
        "question": "What are the advantages of the transformer over RNNs?",
        "gold_answer": "Transformers address the long-range dependency problem that RNNs struggled with. Additionally, transformers enable parallelization across layers, resulting in 10% reduction in training time.",
        "relevant_sections": ["introduction", "results"]
    },
    {
        "id": "q5",
        "question": "What future work is mentioned?",
        "gold_answer": "Future work will explore multilingual models and larger datasets.",
        "relevant_sections": ["conclusions"]
    },
    {
        "id": "q6",
        "question": "How many parameters does the model have?",
        "gold_answer": "The model has 65 million parameters.",
        "relevant_sections": ["methods"]
    }
]


def save_eval_set(output_dir: str = "data/eval") -> None:
    """Save the evaluation set to files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save chunks
    with open(output_path / "sample_chunks.json", 'w') as f:
        json.dump({"chunks": SAMPLE_PAPER_CHUNKS, "total": len(SAMPLE_PAPER_CHUNKS)}, f, indent=2)
    
    # Save QA pairs
    with open(output_path / "qa_pairs.json", 'w') as f:
        json.dump({"qa_pairs": EVAL_QA_PAIRS, "total": len(EVAL_QA_PAIRS)}, f, indent=2)
    
    print(f"Saved evaluation set to {output_dir}")
    print(f"  - {len(SAMPLE_PAPER_CHUNKS)} chunks")
    print(f"  - {len(EVAL_QA_PAIRS)} QA pairs")


def load_eval_set(input_dir: str = "data/eval") -> Dict[str, Any]:
    """Load the evaluation set from files."""
    input_path = Path(input_dir)
    
    with open(input_path / "sample_chunks.json", 'r') as f:
        chunks_data = json.load(f)
    
    with open(input_path / "qa_pairs.json", 'r') as f:
        qa_data = json.load(f)
    
    return {
        "chunks": chunks_data["chunks"],
        "qa_pairs": qa_data["qa_pairs"]
    }


if __name__ == "__main__":
    save_eval_set()

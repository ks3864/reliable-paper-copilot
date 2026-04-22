"""Expanded synthetic evaluation set for MVP, reliability checks, and regression experiments."""

import json
from pathlib import Path
from typing import Dict, Any, List


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
    },
    {
        "chunk_id": 6,
        "section": "abstract",
        "text": "This paper introduces a graph neural network for predicting molecular properties from 2D molecular structures. The method improves toxicity prediction performance compared with descriptor-based baselines.",
        "metadata": {"source": "molecular_gnn_paper"}
    },
    {
        "chunk_id": 7,
        "section": "introduction",
        "text": "Accurate molecular property prediction is important for early drug discovery. Prior descriptor-engineering pipelines require handcrafted features and can miss relational structure between atoms and bonds.",
        "metadata": {"source": "molecular_gnn_paper"}
    },
    {
        "chunk_id": 8,
        "section": "methods",
        "text": "Our model uses message passing over molecular graphs with 4 graph convolution layers and a hidden size of 128. Node embeddings are pooled with global mean pooling before a two-layer prediction head.",
        "metadata": {"source": "molecular_gnn_paper"}
    },
    {
        "chunk_id": 9,
        "section": "experiments",
        "text": "We evaluate on the Tox21 benchmark with scaffold-based train validation test splits. The proposed graph model achieves an AUROC of 0.842, compared with 0.791 for a random forest baseline.",
        "metadata": {"source": "molecular_gnn_paper"}
    },
    {
        "chunk_id": 10,
        "section": "results",
        "text": "The graph model performs best on toxicity tasks involving aromatic compounds and halogenated molecules. An ablation removing message passing drops AUROC by 0.031, showing relational reasoning is important.",
        "metadata": {"source": "molecular_gnn_paper"}
    },
    {
        "chunk_id": 11,
        "section": "conclusions",
        "text": "We conclude that graph neural networks provide a strong inductive bias for molecular prediction. Future work will incorporate 3D conformer information and uncertainty calibration.",
        "metadata": {"source": "molecular_gnn_paper"}
    }
]


def build_chunking_v1_chunks() -> List[Dict[str, Any]]:
    """Build a coarse chunk set that approximates the original section-level chunking."""
    grouped_sections = [
        ["abstract", "introduction"],
        ["methods", "experiments"],
        ["results", "conclusions"],
    ]

    by_source: Dict[str, List[Dict[str, Any]]] = {}
    for chunk in SAMPLE_PAPER_CHUNKS:
        by_source.setdefault(chunk["metadata"]["source"], []).append(chunk)

    coarse_chunks: List[Dict[str, Any]] = []
    next_chunk_id = 0
    for source, source_chunks in by_source.items():
        for section_group in grouped_sections:
            matching = [chunk for chunk in source_chunks if chunk["section"] in section_group]
            if not matching:
                continue

            coarse_chunks.append(
                {
                    "chunk_id": next_chunk_id,
                    "section": matching[0]["section"],
                    "text": "\n\n".join(chunk["text"] for chunk in matching),
                    "metadata": {
                        "source": source,
                        "chunking_strategy": "section_v1",
                        "merged_sections": [chunk["section"] for chunk in matching],
                    },
                }
            )
            next_chunk_id += 1

    return coarse_chunks


def build_chunking_v2_chunks() -> List[Dict[str, Any]]:
    """Return the current fine-grained chunk set with explicit version metadata."""
    enriched_chunks: List[Dict[str, Any]] = []
    for chunk in SAMPLE_PAPER_CHUNKS:
        enriched_chunks.append(
            {
                **chunk,
                "metadata": {
                    **chunk["metadata"],
                    "chunking_strategy": "section_v2",
                },
            }
        )
    return enriched_chunks


def get_eval_chunks(profile: str = "chunking-v2") -> List[Dict[str, Any]]:
    """Return evaluation chunks for a named chunking profile."""
    normalized = (profile or "chunking-v2").strip().lower()
    if normalized in {"chunking-v1", "v1", "baseline"}:
        return build_chunking_v1_chunks()
    if normalized in {"chunking-v2", "v2", "default"}:
        return build_chunking_v2_chunks()
    raise ValueError(f"Unsupported eval chunk profile: {profile}")


EVAL_QA_PAIRS = [
    {
        "id": "q1",
        "question": "What does this paper present?",
        "gold_answer": "A novel approach to neural machine translation using transformer architectures that shows significant improvements over previous seq2seq models.",
        "relevant_sections": ["abstract", "introduction"],
        "source": "sample_paper"
    },
    {
        "id": "q2",
        "question": "What is the BLEU score achieved?",
        "gold_answer": "28.4 BLEU score on the WMT English-German translation task, improving over the previous best of 25.8 by 2.6 points.",
        "relevant_sections": ["experiments"],
        "source": "sample_paper"
    },
    {
        "id": "q3",
        "question": "How many layers and attention heads does the model have?",
        "gold_answer": "The transformer has 6 encoder layers and 6 decoder layers, with multi-head self-attention using 8 attention heads.",
        "relevant_sections": ["methods"],
        "source": "sample_paper"
    },
    {
        "id": "q4",
        "question": "What are the advantages of the transformer over RNNs?",
        "gold_answer": "Transformers address the long-range dependency problem that RNNs struggled with. Additionally, transformers enable parallelization across layers, resulting in 10% reduction in training time.",
        "relevant_sections": ["introduction", "results"],
        "source": "sample_paper"
    },
    {
        "id": "q5",
        "question": "What future work is mentioned?",
        "gold_answer": "Future work will explore multilingual models and larger datasets.",
        "relevant_sections": ["conclusions"],
        "source": "sample_paper"
    },
    {
        "id": "q6",
        "question": "How many parameters does the model have?",
        "gold_answer": "The model has 65 million parameters.",
        "relevant_sections": ["methods"],
        "source": "sample_paper"
    },
    {
        "id": "q7",
        "question": "Which translation benchmark is used in the experiments?",
        "gold_answer": "The experiments use the WMT English-German translation task.",
        "relevant_sections": ["experiments"],
        "source": "sample_paper"
    },
    {
        "id": "q8",
        "question": "How much does the new model improve over the previous best BLEU score?",
        "gold_answer": "It improves on the previous best BLEU score by 2.6 points, from 25.8 to 28.4.",
        "relevant_sections": ["experiments"],
        "source": "sample_paper"
    },
    {
        "id": "q9",
        "question": "Why did earlier RNN-based approaches struggle?",
        "gold_answer": "Earlier RNN-based approaches struggled with long-range dependencies.",
        "relevant_sections": ["introduction"],
        "source": "sample_paper"
    },
    {
        "id": "q10",
        "question": "What mechanism helped drive rapid progress in neural machine translation?",
        "gold_answer": "The advent of attention mechanisms helped drive rapid progress in neural machine translation.",
        "relevant_sections": ["introduction"],
        "source": "sample_paper"
    },
    {
        "id": "q11",
        "question": "How many total transformer layers are described across encoder and decoder stacks?",
        "gold_answer": "The model uses 12 total layers: 6 encoder layers and 6 decoder layers.",
        "relevant_sections": ["methods"],
        "source": "sample_paper"
    },
    {
        "id": "q12",
        "question": "What kind of attention is used in each layer?",
        "gold_answer": "Each layer uses multi-head self-attention.",
        "relevant_sections": ["methods"],
        "source": "sample_paper"
    },
    {
        "id": "q13",
        "question": "What evidence suggests the model is more efficient to train?",
        "gold_answer": "The results report a 10% reduction in training time due to parallelization across layers.",
        "relevant_sections": ["results"],
        "source": "sample_paper"
    },
    {
        "id": "q14",
        "question": "What baseline family does the transformer outperform?",
        "gold_answer": "The transformer outperforms RNN-based models.",
        "relevant_sections": ["results"],
        "source": "sample_paper"
    },
    {
        "id": "q15",
        "question": "What two future research directions are proposed?",
        "gold_answer": "The paper proposes exploring multilingual models and larger datasets.",
        "relevant_sections": ["conclusions"],
        "source": "sample_paper"
    },
    {
        "id": "q16",
        "question": "What architecture is claimed to be highly effective for machine translation?",
        "gold_answer": "Transformer architectures are claimed to be highly effective for machine translation.",
        "relevant_sections": ["conclusions"],
        "source": "sample_paper"
    },
    {
        "id": "q17",
        "question": "Summarize the model setup and main quantitative result.",
        "gold_answer": "The paper uses a transformer with 6 encoder layers, 6 decoder layers, 8 attention heads, and 65 million parameters, and it achieves 28.4 BLEU on WMT English-German.",
        "relevant_sections": ["methods", "experiments"],
        "source": "sample_paper"
    },
    {
        "id": "q18",
        "question": "What combined benefits does the paper claim over prior seq2seq and RNN approaches?",
        "gold_answer": "The paper claims the transformer improves translation quality over prior seq2seq systems while also avoiding RNN long-range dependency issues and reducing training time through parallelization.",
        "relevant_sections": ["abstract", "introduction", "results"],
        "source": "sample_paper"
    },
    {
        "id": "q19",
        "question": "What problem does the second paper address?",
        "gold_answer": "It addresses molecular property prediction from 2D molecular structures, with a focus on improving toxicity prediction.",
        "relevant_sections": ["abstract", "introduction"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q20",
        "question": "What benchmark is used to evaluate the molecular graph model?",
        "gold_answer": "The model is evaluated on the Tox21 benchmark.",
        "relevant_sections": ["experiments"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q21",
        "question": "What train validation test splitting strategy is used?",
        "gold_answer": "The experiments use scaffold-based train validation test splits.",
        "relevant_sections": ["experiments"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q22",
        "question": "How many graph convolution layers and what hidden size does the model use?",
        "gold_answer": "The model uses 4 graph convolution layers with a hidden size of 128.",
        "relevant_sections": ["methods"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q23",
        "question": "How are node embeddings aggregated before prediction?",
        "gold_answer": "Node embeddings are aggregated using global mean pooling before a two-layer prediction head.",
        "relevant_sections": ["methods"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q24",
        "question": "What AUROC does the graph model achieve, and how does it compare to the baseline?",
        "gold_answer": "The graph model achieves 0.842 AUROC, compared with 0.791 for the random forest baseline.",
        "relevant_sections": ["experiments"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q25",
        "question": "Which baseline is the graph model compared against?",
        "gold_answer": "It is compared against a random forest baseline.",
        "relevant_sections": ["experiments"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q26",
        "question": "On which kinds of molecules does the graph model perform best?",
        "gold_answer": "It performs best on toxicity tasks involving aromatic compounds and halogenated molecules.",
        "relevant_sections": ["results"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q27",
        "question": "What happens when message passing is removed?",
        "gold_answer": "Removing message passing lowers AUROC by 0.031, indicating relational reasoning is important.",
        "relevant_sections": ["results"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q28",
        "question": "Why do the authors argue graph neural networks are a good fit for this task?",
        "gold_answer": "They argue graph neural networks provide a strong inductive bias for molecular prediction.",
        "relevant_sections": ["conclusions"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q29",
        "question": "What limitation of prior descriptor-based pipelines is highlighted?",
        "gold_answer": "Prior descriptor-engineering pipelines require handcrafted features and can miss relational structure between atoms and bonds.",
        "relevant_sections": ["introduction"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q30",
        "question": "What future work is proposed for the molecular prediction model?",
        "gold_answer": "Future work will incorporate 3D conformer information and uncertainty calibration.",
        "relevant_sections": ["conclusions"],
        "source": "molecular_gnn_paper"
    },
    {
        "id": "q31",
        "question": "What optimizer and learning rate were used to train the transformer?",
        "gold_answer": "The paper does not provide the optimizer or learning rate.",
        "relevant_sections": [],
        "source": "sample_paper",
        "is_answerable": False
    },
    {
        "id": "q32",
        "question": "How many molecules are in the Tox21 training split?",
        "gold_answer": "The paper does not provide the training split size.",
        "relevant_sections": [],
        "source": "molecular_gnn_paper",
        "is_answerable": False
    }
]


def save_eval_set(output_dir: str = "data/eval") -> None:
    """Save the evaluation set to files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    v2_chunks = get_eval_chunks("chunking-v2")
    v1_chunks = get_eval_chunks("chunking-v1")

    with open(output_path / "sample_chunks.json", "w") as f:
        json.dump({"chunks": v2_chunks, "total": len(v2_chunks)}, f, indent=2)

    with open(output_path / "sample_chunks_chunking_v1.json", "w") as f:
        json.dump({"chunks": v1_chunks, "total": len(v1_chunks)}, f, indent=2)

    with open(output_path / "sample_chunks_chunking_v2.json", "w") as f:
        json.dump({"chunks": v2_chunks, "total": len(v2_chunks)}, f, indent=2)

    with open(output_path / "qa_pairs.json", "w") as f:
        json.dump({"qa_pairs": EVAL_QA_PAIRS, "total": len(EVAL_QA_PAIRS)}, f, indent=2)

    print(f"Saved evaluation set to {output_dir}")
    print(f"  - {len(v2_chunks)} default chunks")
    print(f"  - {len(EVAL_QA_PAIRS)} QA pairs")


def load_eval_set(input_dir: str = "data/eval") -> Dict[str, Any]:
    """Load the evaluation set from files."""
    input_path = Path(input_dir)

    with open(input_path / "sample_chunks.json", "r") as f:
        chunks_data = json.load(f)

    with open(input_path / "qa_pairs.json", "r") as f:
        qa_data = json.load(f)

    return {
        "chunks": chunks_data["chunks"],
        "qa_pairs": qa_data["qa_pairs"],
    }


if __name__ == "__main__":
    save_eval_set()

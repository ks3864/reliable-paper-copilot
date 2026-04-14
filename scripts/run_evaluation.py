#!/usr/bin/env python3
"""Evaluation script for Reliable Scientific Paper Copilot.

This script runs the evaluation metrics on the sample paper using the eval set.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.eval.eval_set import SAMPLE_PAPER_CHUNKS, EVAL_QA_PAIRS, save_eval_set
from src.retrieval import create_retriever
from src.answering import SimpleAnswerGenerator
from src.evaluation import evaluate_all


def main():
    print("=" * 60)
    print("Reliable Scientific Paper Copilot - Evaluation")
    print("=" * 60)
    
    # Ensure eval data is saved
    save_eval_set()
    
    print(f"\nLoading {len(SAMPLE_PAPER_CHUNKS)} chunks and {len(EVAL_QA_PAIRS)} QA pairs...")
    
    # Build retriever from sample chunks
    print("\nBuilding retrieval index...")
    retriever = create_retriever(SAMPLE_PAPER_CHUNKS)
    
    # Create answer generator
    generator = SimpleAnswerGenerator(retriever)
    
    # Run evaluation
    print("\nRunning evaluation...")
    results = []
    
    for qa in EVAL_QA_PAIRS:
        print(f"\n  [{qa['id']}] Q: {qa['question']}")
        result = generator.answer(qa["question"])
        
        # Truncate answer for display
        answer_preview = result["answer"][:100] + "..." if len(result["answer"]) > 100 else result["answer"]
        print(f"      A: {answer_preview}")
        print(f"      Sources: {result['sources']}")
        
        results.append(result)
    
    # Compute metrics
    print("\n" + "=" * 60)
    print("EVALUATION RESULTS")
    print("=" * 60)
    
    eval_results = evaluate_all(results, EVAL_QA_PAIRS)
    
    print("\nAggregate Metrics:")
    agg = eval_results["aggregate"]
    print(f"  Exact Match:     {agg['exact_match']:.2%}")
    print(f"  F1 Score:         {agg['f1']:.2%}")
    print(f"  Retrieval Hit:    {agg['retrieval_hit']:.2%}")
    print(f"  Retrieval MRR:    {agg['retrieval_mrr']:.2%}")
    
    print("\nPer-Question Breakdown:")
    for m in eval_results["per_question"]:
        print(f"  [{m['question_id']}] EM={m['exact_match']:.2f} F1={m['f1']:.2f} Hit={m['retrieval_hit']:.2f} MRR={m['retrieval_mrr']:.2f}")
    
    return eval_results


if __name__ == "__main__":
    main()

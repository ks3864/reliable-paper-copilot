"""Answering Module - Generate grounded answers with citations."""

from typing import Dict, Any, List, Optional, Callable
import json

from .prompting import build_answer_prompt, build_citation


class AnswerGenerator:
    """
    Generate answers to questions about papers using retrieval + generation.
    
    This is a thin wrapper that:
    1. Takes a retriever to fetch relevant chunks
    2. Builds a prompt with the retrieved context
    3. Calls an LLM to generate the answer
    
    The actual LLM call is delegated to a provided callable.
    """
    
    def __init__(self, retriever, llm_callable: Callable[[str], str]):
        """
        Initialize answer generator.
        
        Args:
            retriever: Retriever instance for fetching relevant chunks
            llm_callable: Function that takes a prompt string and returns generated text
        """
        self.retriever = retriever
        self.llm_callable = llm_callable
    
    def answer(self, question: str, top_k: int = 5, include_citations: bool = True) -> Dict[str, Any]:
        """
        Answer a question about the paper.
        
        Args:
            question: User's question
            top_k: Number of chunks to retrieve
            include_citations: Whether to add citation info to answer
            
        Returns:
            Dictionary containing:
            - answer: The generated answer
            - retrieved_chunks: The chunks used for generation
            - question: The original question
        """
        # Retrieve relevant chunks
        retrieved_chunks = self.retriever.retrieve(question, top_k=top_k)
        
        if not retrieved_chunks:
            return {
                "answer": "I couldn't find any relevant information in the paper to answer your question.",
                "retrieved_chunks": [],
                "question": question,
                "sources": []
            }
        
        # Build prompt
        prompt = build_answer_prompt(question, retrieved_chunks)
        
        # Generate answer
        generated_text = self.llm_callable(prompt)
        
        if include_citations:
            generated_text = build_citation(generated_text, retrieved_chunks)
        
        # Extract source sections
        sources = list(dict.fromkeys(
            chunk.get("section", "unknown") for chunk in retrieved_chunks
        ))
        
        return {
            "answer": generated_text,
            "retrieved_chunks": retrieved_chunks,
            "question": question,
            "sources": sources,
            "num_chunks_retrieved": len(retrieved_chunks)
        }


def create_mock_llm_callable() -> Callable[[str], str]:
    """
    Create a mock LLM callable for testing without an actual LLM.
    
    Returns a function that simulates LLM responses based on the prompt.
    """
    def mock_call(prompt: str) -> str:
        # Simple heuristic-based response for testing
        if "accuracy" in prompt.lower():
            return "Based on the paper, they achieved 95% accuracy on the benchmark dataset."
        elif "method" in prompt.lower():
            return "The paper presents a new method for machine learning using deep neural networks."
        elif "abstract" in prompt.lower():
            return "This paper presents a new method for machine learning."
        else:
            return "Based on the provided context, I can answer your question using the information from the paper."
    
    return mock_call


class SimpleAnswerGenerator(AnswerGenerator):
    """
    Simple answer generator with built-in mock LLM for testing.
    
    Use this when you don't have access to an actual LLM API.
    """
    
    def __init__(self, retriever):
        super().__init__(retriever, create_mock_llm_callable())


if __name__ == "__main__":
    from src.retrieval import create_retriever
    
    # Test with sample data
    test_chunks = [
        {"chunk_id": 0, "section": "abstract", "text": "This paper presents a new method for machine learning.", "metadata": {}},
        {"chunk_id": 1, "section": "methods", "text": "Our approach uses deep neural networks with attention mechanisms.", "metadata": {}},
        {"chunk_id": 2, "section": "results", "text": "We achieved 95% accuracy on the benchmark dataset.", "metadata": {}},
    ]
    
    retriever = create_retriever(test_chunks)
    generator = SimpleAnswerGenerator(retriever)
    
    result = generator.answer("What accuracy did they achieve?")
    print(f"Q: {result['question']}")
    print(f"A: {result['answer']}")
    print(f"Sources: {result['sources']}")

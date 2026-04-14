"""Prompting Module - Templates for grounded answer generation."""

from typing import List, Dict, Any


DEFAULT_ANSWER_TEMPLATE = """You are a research assistant helping answer questions about a scientific paper.

Answer the question based ONLY on the provided context from the paper. If the context doesn't contain enough information to fully answer the question, say so.

**Context from the paper:**
{context}

**Question:** {question}

**Instructions:**
1. Answer based only on the provided context
2. Include specific citations when referencing information (e.g., "According to the paper...")
3. If the answer cannot be fully derived from the context, acknowledge what is missing
4. Be precise and cite the specific section(s) when possible

**Answer:**"""


DEFAULT_SUMMARIZE_TEMPLATE = """Summarize the following section from a scientific paper:

{section_name}

{context}

Provide a concise summary focusing on the key findings or methods described."""


def build_answer_prompt(question: str, retrieved_chunks: List[Dict[str, Any]], 
                       template: str = None) -> str:
    """
    Build a prompt for answering a question with retrieved context.
    
    Args:
        question: User's question
        retrieved_chunks: List of chunks from retriever
        template: Optional custom template
        
    Returns:
        Formatted prompt string
    """
    if template is None:
        template = DEFAULT_ANSWER_TEMPLATE
    
    # Build context from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        section = chunk.get("section", "unknown")
        text = chunk.get("text", "")
        context_parts.append(f"[Section: {section}]\n{text}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    return template.format(context=context, question=question)


def build_citation(answer: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Add citation references to an answer.
    
    Args:
        answer: Generated answer text
        retrieved_chunks: Chunks used to generate the answer
        
    Returns:
        Answer with citation references
    """
    sections = [chunk.get("section", "unknown") for chunk in retrieved_chunks]
    unique_sections = list(dict.fromkeys(sections))  # Preserve order, remove dups
    
    citation = "Based on: " + ", ".join(unique_sections)
    return f"{answer}\n\n[{citation}]"


class PromptBuilder:
    """Configurable prompt builder."""
    
    def __init__(self, answer_template: str = None, summarize_template: str = None):
        self.answer_template = answer_template or DEFAULT_ANSWER_TEMPLATE
        self.summarize_template = summarize_template or DEFAULT_SUMMARIZE_TEMPLATE
    
    def build(self, prompt_type: str, **kwargs) -> str:
        """Build a prompt by type."""
        if prompt_type == "answer":
            return build_answer_prompt(kwargs["question"], kwargs["retrieved_chunks"], 
                                       self.answer_template)
        elif prompt_type == "summarize":
            return build_summarize_prompt(kwargs["section_name"], kwargs["context"],
                                         self.summarize_template)
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")


def build_summarize_prompt(section_name: str, context: str, template: str = None) -> str:
    """Build a prompt for summarizing a section."""
    if template is None:
        template = DEFAULT_SUMMARIZE_TEMPLATE
    return template.format(section_name=section_name, context=context)


if __name__ == "__main__":
    # Test
    test_chunks = [
        {"chunk_id": 0, "section": "abstract", "text": "This paper presents a new method for machine learning.", "metadata": {}},
        {"chunk_id": 1, "section": "results", "text": "We achieved 95% accuracy on the benchmark dataset.", "metadata": {}},
    ]
    
    prompt = build_answer_prompt("What accuracy did they achieve?", test_chunks)
    print(prompt)

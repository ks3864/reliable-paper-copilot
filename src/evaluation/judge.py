"""LLM-as-judge answer quality scoring."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List


DEFAULT_JUDGE_TEMPLATE = """You are grading an answer to a question about a scientific paper.
Score the answer using the gold answer and retrieved context.

Question: {question}
Gold answer: {gold_answer}
Model answer: {model_answer}

Retrieved context:
{context}

Return strict JSON with this schema:
{{
  "groundedness": <int 1-5>,
  "correctness": <int 1-5>,
  "completeness": <int 1-5>,
  "overall": <int 1-5>,
  "reasoning": "<brief explanation>"
}}

Scoring rubric:
- groundedness: is the answer supported by the retrieved context?
- correctness: does it match the gold answer without introducing false claims?
- completeness: does it cover the main expected points?
- overall: overall answer quality considering the above.
"""


@dataclass
class AnswerQualityJudge:
    """Thin LLM-as-judge wrapper with strict JSON parsing."""

    llm_callable: Callable[[str], str]
    template: str = DEFAULT_JUDGE_TEMPLATE

    def build_prompt(self, result: Dict[str, Any], qa_pair: Dict[str, Any]) -> str:
        context_lines: List[str] = []
        for chunk in result.get("retrieved_chunks", []):
            section = chunk.get("section", "unknown")
            text = chunk.get("text", "")
            context_lines.append(f"[Section: {section}]\n{text}")

        context = "\n\n---\n\n".join(context_lines) if context_lines else "No retrieved context."
        return self.template.format(
            question=qa_pair["question"],
            gold_answer=qa_pair["gold_answer"],
            model_answer=result["answer"],
            context=context,
        )

    def score(self, result: Dict[str, Any], qa_pair: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self.build_prompt(result, qa_pair)
        raw_response = self.llm_callable(prompt)
        parsed = parse_judge_response(raw_response)
        parsed["raw_response"] = raw_response
        return parsed


def parse_judge_response(raw_response: str) -> Dict[str, Any]:
    """Parse and validate strict JSON judge output."""
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Judge response was not valid JSON: {raw_response}") from exc

    required_scores = ["groundedness", "correctness", "completeness", "overall"]
    for key in required_scores:
        if key not in payload:
            raise ValueError(f"Judge response missing required score: {key}")
        if not isinstance(payload[key], int) or not 1 <= payload[key] <= 5:
            raise ValueError(f"Judge score for {key} must be an integer between 1 and 5")

    reasoning = payload.get("reasoning", "")
    if not isinstance(reasoning, str):
        raise ValueError("Judge reasoning must be a string")

    return {
        "groundedness": payload["groundedness"] / 5.0,
        "correctness": payload["correctness"] / 5.0,
        "completeness": payload["completeness"] / 5.0,
        "answer_quality": payload["overall"] / 5.0,
        "judge_reasoning": reasoning.strip(),
    }


def create_mock_judge_callable() -> Callable[[str], str]:
    """Return a simple deterministic mock judge for local testing."""

    def mock_call(prompt: str) -> str:
        lower_prompt = prompt.lower()
        if "couldn't find" in lower_prompt or "no retrieved context" in lower_prompt:
            return json.dumps(
                {
                    "groundedness": 4,
                    "correctness": 2,
                    "completeness": 1,
                    "overall": 2,
                    "reasoning": "The answer is cautious but does not address the gold answer well.",
                }
            )

        return json.dumps(
            {
                "groundedness": 5,
                "correctness": 4,
                "completeness": 4,
                "overall": 4,
                "reasoning": "The answer is mostly correct, grounded, and reasonably complete.",
            }
        )

    return mock_call

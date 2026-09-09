from google import genai
from .retry import call_with_retry


_investigation_qa_prompt: str = "You have already completed a research investigation. You will be given the full evidence gathered during that investigation (the research plan, findings, and fact-checking from every iteration) followed by a follow-up question about it. Answer the question using only the evidence provided - reference the specific findings your answer relies on. If the evidence doesn't address the question, say so rather than guessing beyond it."


def investigation_qa_agent(client: genai.Client, investigation_context: str, question: str) -> str:
    """Answers a follow-up question about a completed research investigation, grounded in the
    full evidence gathered during that investigation (not just the final summary).
    Args:
        client <genai.Client>: The shared client for this session
        investigation_context <str>: The full evidence from the completed investigation (plan, research, fact-checking across every iteration)
        question <str>: The user's follow-up question
    Returns:
        <str>: An answer grounded in the provided evidence
    """
    contents_for_model = f"### INVESTIGATION EVIDENCE\n{investigation_context}\n\n### FOLLOW-UP QUESTION\n{question}"
    interaction = call_with_retry(lambda: client.interactions.create(
        model="gemini-3.1-flash-lite",
        system_instruction=_investigation_qa_prompt,
        input=contents_for_model,
    ), stage="investigation_qa_agent")
    return interaction.output_text

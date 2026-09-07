from src.agents.agent_type_enum import AgentType
from src.agents.research_step import ResearchStep
from src.agents.research_utils import research_history_to_text


def test_research_history_to_text_formats_each_step_with_its_agent_type():
    steps = [
        ResearchStep(AgentType.RESEARCH_PLANNER, "plan text"),
        ResearchStep(AgentType.RESEARCHER, "research text"),
    ]
    text = research_history_to_text(steps)
    assert text.startswith("### RESEARCH CYCLES ALREADY PERFORMED\n")
    assert "# plan\nplan text\n" in text
    assert "# research\nresearch text\n" in text


def test_research_history_to_text_preserves_step_order():
    steps = [
        ResearchStep(AgentType.RESEARCH_PLANNER, "first"),
        ResearchStep(AgentType.RESEARCHER, "second"),
        ResearchStep(AgentType.FACT_CHECKING, "third"),
    ]
    text = research_history_to_text(steps)
    assert text.index("first") < text.index("second") < text.index("third")


def test_research_history_to_text_empty_list_still_has_header():
    assert research_history_to_text([]) == "### RESEARCH CYCLES ALREADY PERFORMED\n"

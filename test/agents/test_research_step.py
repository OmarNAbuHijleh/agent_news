from src.agents.agent_type_enum import AgentType
from src.agents.research_step import ResearchStep


def test_research_step_holds_agent_type_and_content():
    step = ResearchStep(AgentType.FACT_CHECKING, "some content")
    assert step.agent_type is AgentType.FACT_CHECKING
    assert step.content == "some content"


def test_research_step_equality_is_by_value():
    assert ResearchStep(AgentType.RESEARCHER, "x") == ResearchStep(AgentType.RESEARCHER, "x")
    assert ResearchStep(AgentType.RESEARCHER, "x") != ResearchStep(AgentType.RESEARCHER, "y")
    assert ResearchStep(AgentType.RESEARCHER, "x") != ResearchStep(AgentType.FACT_CHECKING, "x")

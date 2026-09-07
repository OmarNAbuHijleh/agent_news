from dataclasses import dataclass
from .agent_type_enum import AgentType


@dataclass
class ResearchStep:
    """A single recorded step in a research session: which agent produced it and what it produced."""
    agent_type: AgentType
    content: str

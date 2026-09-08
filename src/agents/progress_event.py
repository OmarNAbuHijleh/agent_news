from dataclasses import dataclass


@dataclass
class ProgressEvent:
    """A single update emitted while a research session runs, so a caller (e.g. the API layer)
    can stream progress to a user instead of waiting silently for the whole pipeline to finish.
    Args:
        stage <str>: Which step produced this event (e.g. "planning", "plan", "researching",
            "research_result", "fact_checking", "fact_check_result", "synthesizing", "final",
            "cache_hit")
        content <str>: The status text or actual content for this stage
        done <bool>: True only on the final event, which carries the finished result
    """
    stage: str
    content: str
    done: bool = False

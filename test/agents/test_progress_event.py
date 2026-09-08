from src.agents.progress_event import ProgressEvent


def test_progress_event_defaults_done_to_false():
    event = ProgressEvent(stage="planning", content="Creating a research plan...")
    assert event.done is False


def test_progress_event_holds_stage_content_and_done():
    event = ProgressEvent(stage="final", content="the report", done=True)
    assert event.stage == "final"
    assert event.content == "the report"
    assert event.done is True

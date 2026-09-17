from src.agents.tool_call_budget import ToolCallBudget


def test_try_consume_returns_true_while_budget_remains():
    budget = ToolCallBudget(max_calls=2)
    assert budget.try_consume() is True
    assert budget.try_consume() is True


def test_try_consume_returns_false_once_exhausted():
    budget = ToolCallBudget(max_calls=1)
    assert budget.try_consume() is True
    assert budget.try_consume() is False


def test_zero_max_calls_never_allows_a_call():
    budget = ToolCallBudget(max_calls=0)
    assert budget.try_consume() is False

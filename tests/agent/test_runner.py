from agent.harness.runner import investigate

def test_correction_changes_investigation_order():
    first = investigate("INC-1", "timeouts", correction=None)
    second = investigate("INC-2", "timeouts", correction="check deploy diffs first")
    assert first.actions[0].startswith("query_metrics")
    assert second.actions[0].startswith("get_deployments")


from agent.memory.consolidation import consolidate

def test_feedback_is_durable_memory():
    result = consolidate("INC-1", "root", "fix", [], "check deploys first")
    assert result[-1].type == "human_feedback"
    assert result[-1].provenance.author == "human"


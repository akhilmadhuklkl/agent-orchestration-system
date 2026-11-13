from app.graph import build_graph


def test_executor_can_use_registered_word_count_tool():
    result = build_graph().invoke({"description": "Count words in this sentence", "require_approval": False})
    assert "Tool result" in result["result"]
    assert result["status"] == "completed"

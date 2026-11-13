from app.graph import build_graph


def test_routing_evaluation_cases():
    graph = build_graph()
    cases = [("Research market trends", "Research Agent"), ("Draft a launch plan", "Writing Agent"), ("Analyze monthly revenue", "Analysis Agent")]
    for description, expected_agent in cases:
        result = graph.invoke({"description": description, "require_approval": False})
        assert expected_agent in result["plan"][1]

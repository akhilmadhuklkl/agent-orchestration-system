from app.config import settings
from app.graph import build_graph


def test_routing_evaluation_cases():
    graph = build_graph()
    cases = [("Research market trends", "Research Agent"), ("Draft a launch plan", "Writing Agent"), ("Analyze monthly revenue", "Analysis Agent")]
    for description, expected_agent in cases:
        result = graph.invoke({"description": description, "require_approval": False})
        assert expected_agent in result["plan"][1]

def test_deterministic_model_mode_is_available():
    assert settings.model_mode == "deterministic"

def test_ollama_endpoint_has_a_local_default():
    assert settings.ollama_base_url.startswith("http://localhost")

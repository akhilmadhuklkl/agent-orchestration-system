from .agents import choose_agent
from .config import settings


def generate_plan(description: str) -> list[str]:
    agent = choose_agent(description)
    fallback = ["Understand the request", f"Delegate to {agent.role}", "Produce and validate the result"]
    if settings.model_mode != "openai" or not settings.openai_api_key:
        return fallback
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(model=settings.model_name, input=f"Create exactly three concise execution steps for this task. Return one step per line, with no numbering. Task: {description}")
        steps = [line.strip(" -") for line in response.output_text.splitlines() if line.strip()]
        return steps[:3] if steps else fallback
    except Exception:  # noqa: BLE001 - model failures fall back to deterministic planning
        return fallback

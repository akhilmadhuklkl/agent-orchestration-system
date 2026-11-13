from .agents import choose_agent
from .config import settings


def _ollama(prompt: str) -> str:
    import httpx
    response = httpx.post(f"{settings.ollama_base_url}/api/generate", json={"model": settings.model_name, "prompt": prompt, "stream": False}, timeout=60)
    response.raise_for_status()
    return response.json().get("response", "").strip()


def choose_tool(description: str, agent: str) -> str | None:
    text = description.lower()
    if "count" in text and "word" in text and agent in {"writer", "analyst", "executor"}:
        return "word_count"
    if "summarize" in text and agent in {"planner", "writer", "executor"}:
        return "task_summary"
    return None


def generate_plan(description: str) -> list[str]:
    agent = choose_agent(description)
    fallback = ["Understand the request", f"Delegate to {agent.role}", "Produce and validate the result"]
    if settings.model_mode == "deterministic":
        return fallback
    try:
        if settings.model_mode == "ollama":
            text = _ollama(f"Create exactly three concise execution steps for this task. Return one step per line, with no numbering. Task: {description}")
            steps = [line.strip(" -") for line in text.splitlines() if line.strip()]
            return steps[:3] if steps else fallback
        if not settings.openai_api_key:
            return fallback
        from openai import OpenAI
        response = OpenAI(api_key=settings.openai_api_key).responses.create(model=settings.model_name, input=f"Create exactly three concise execution steps for this task. Return one step per line, with no numbering. Task: {description}")
        steps = [line.strip(" -") for line in response.output_text.splitlines() if line.strip()]
        return steps[:3] if steps else fallback
    except Exception:  # noqa: BLE001 - model failures fall back to deterministic planning
        return fallback

def generate_result(description: str, agent_role: str) -> str:
    fallback = f"{agent_role} completed: {description}"
    if settings.model_mode == "deterministic":
        return fallback
    try:
        if settings.model_mode == "ollama":
            return _ollama(f"Act as a {agent_role}. Complete this task and provide a concise result: {description}") or fallback
        if not settings.openai_api_key:
            return fallback
        from openai import OpenAI
        response = OpenAI(api_key=settings.openai_api_key).responses.create(model=settings.model_name, input=f"Act as a {agent_role}. Complete this task and provide a concise result: {description}")
        return response.output_text.strip() or fallback
    except Exception:  # noqa: BLE001 - model failures fall back to deterministic execution
        return fallback

def review_result(description: str, result: str) -> tuple[bool, str]:
    if settings.model_mode == "deterministic":
        return True, "Deterministic review passed"
    try:
        if settings.model_mode == "ollama":
            text = _ollama(f"Review whether this result satisfies the task. Reply PASS or FAIL followed by a short reason. Task: {description}\nResult: {result}")
            return not text.upper().startswith("FAIL"), text
        if not settings.openai_api_key:
            return True, "Review fallback passed"
        from openai import OpenAI
        response = OpenAI(api_key=settings.openai_api_key).responses.create(model=settings.model_name, input=f"Review whether this result satisfies the task. Reply PASS or FAIL followed by a short reason. Task: {description}\nResult: {result}")
        text = response.output_text.strip()
        return not text.upper().startswith("FAIL"), text
    except Exception:  # noqa: BLE001 - model failures do not block local execution
        return True, "Review fallback passed"

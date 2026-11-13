from dataclasses import dataclass


@dataclass(frozen=True)
class Agent:
    name: str
    role: str
    capabilities: tuple[str, ...]

AGENTS = (
    Agent("researcher", "Research Agent", ("research", "search", "find", "investigate")),
    Agent("writer", "Writing Agent", ("write", "draft", "document", "summarize")),
    Agent("analyst", "Analysis Agent", ("analyze", "compare", "evaluate", "report")),
    Agent("executor", "General Execution Agent", ("run", "execute", "perform", "complete")),
)

def choose_agent(description: str) -> Agent:
    text = description.lower()
    for agent in AGENTS:
        if any(capability in text for capability in agent.capabilities):
            return agent
    return next(agent for agent in AGENTS if agent.name == "executor")

def list_agents() -> list[Agent]:
    return list(AGENTS)

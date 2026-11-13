from typing import TypedDict

from .agents import choose_agent

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - used only on restricted Python hosts
    END = "__end__"
    START = "__start__"

    class StateGraph:
        """Small local adapter for hosts where LangGraph's optional binary is blocked."""
        def __init__(self, _state_type):
            self.nodes = {}

        def add_node(self, name, fn):
            self.nodes[name] = fn

        def add_edge(self, *_args):
            return None

        def add_conditional_edges(self, *_args):
            return None

        def compile(self):
            nodes = self.nodes

            class Compiled:
                def invoke(self, state):
                    state = {**state, **nodes["plan"](state)}
                    state = {**state, **nodes["approval"](state)}
                    if state["status"] == "running":
                        state = {**state, **nodes["execute"](state)}
                    return state

            return Compiled()

class GraphState(TypedDict, total=False):
    task_id: str
    description: str
    require_approval: bool
    status: str
    plan: list[str]
    result: str
    error: str
    assigned_agent: str
    agent_role: str

def plan_task(state: GraphState) -> GraphState:
    agent = choose_agent(state["description"])
    return {"plan": ["Understand the request", f"Delegate to {agent.role}", "Produce and validate the result"], "assigned_agent": agent.name, "agent_role": agent.role, "status": "planned"}

def approval_gate(state: GraphState) -> GraphState:
    if state.get("require_approval"):
        return {"status": "awaiting_approval"}
    return {"status": "running"}

def execute_task(state: GraphState) -> GraphState:
    agent = choose_agent(state["description"])
    return {"status": "completed", "result": f"{state.get('agent_role', agent.role)} completed: {state['description']}"}

def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("plan", plan_task)
    graph.add_node("approval", approval_gate)
    graph.add_node("execute", execute_task)
    graph.add_edge(START, "plan")
    graph.add_edge("plan", "approval")
    graph.add_conditional_edges("approval", lambda s: "execute" if s["status"] == "running" else END)
    graph.add_edge("execute", END)
    return graph.compile()

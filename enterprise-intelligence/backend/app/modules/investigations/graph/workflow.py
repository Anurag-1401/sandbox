from langgraph.graph import END, START, StateGraph

from app.modules.investigations.graph.nodes import (
    InvestigationNodes,
)
from app.modules.investigations.state import InvestigationState


def build_investigation_graph(
    *,
    db,
    run,
    investigation,
    repository,
    llm,
    retrieval_service,
):
    nodes = InvestigationNodes(
        db=db,
        run=run,
        investigation=investigation,
        repository=repository,
        llm=llm,
        retrieval_service=retrieval_service,
    )

    graph = StateGraph(InvestigationState)

    graph.add_node("planner", nodes.plan)
    graph.add_node("researcher", nodes.research)
    graph.add_node("document_analyst", nodes.analyze)
    graph.add_node("comparator", nodes.compare)
    graph.add_node("verifier", nodes.verify)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "document_analyst")
    graph.add_edge("document_analyst", "comparator")
    graph.add_edge("comparator", "verifier")
    graph.add_edge("verifier", END)

    return graph.compile()
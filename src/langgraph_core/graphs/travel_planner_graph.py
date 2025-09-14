from langgraph.graph import StateGraph, START, END
from src.langgraph_core.state.travel_planner_states import TravelPlannerState
from src.langgraph_core.nodes.travel_planner_nodes import TravelPlannerNode
from src.langgraph_core.tools.tools import get_tools, create_tool_node
from src.langgraph_core.tools.custom_tools import weather_tool
from langgraph.prebuilt import ToolNode

class TravelGraphBuilder:
    def __init__(self, llm):
        self.llm = llm
        self.graph_builder = StateGraph(TravelPlannerState)
        self.travel_planer_node = TravelPlannerNode(self.llm)

    def _add_nodes(self) -> None:
        """Register all nodes in the graph."""
        self.graph_builder.add_node(
            "router_node",
            self.travel_planer_node.router,
        )

        self.graph_builder.add_node(
            "chat_node",
            lambda TravelPlannerState: self.travel_planer_node.chat_node(TravelPlannerState, self.llm),
        )

        # Weather Node (ToolNode)
        weather_node = ToolNode(tools=[weather_tool])
        self.graph_builder.add_node("weather_node", weather_node)

        # Search Node
        tools = get_tools()
        search_node = create_tool_node(tools)  # includes TavilySearchResults
        self.graph_builder.add_node("search_node", search_node)

    def _add_edges(self) -> None:
        """Define execution flow between nodes."""
        self.graph_builder.add_edge(START, "router_node")
        self.graph_builder.add_conditional_edges(
            "router_node",
            lambda state: state.get("route"),
            {
                "chat": "chat_node",
                "weather": "weather_node",
                "search": "search_node",
            }
        )
        self.graph_builder.add_edge("chat_node", END)
        self.graph_builder.add_edge("weather_node", END)
        self.graph_builder.add_edge("search_node", END)

    def build(self):
        """Build and compile the travel planner graph."""
        self._add_nodes()
        self._add_edges()
        compiled_graph = self.graph_builder.compile()
        compiled_graph.get_graph().draw_mermaid_png(output_file_path=r"./logs/custom_routing.png")
        return compiled_graph

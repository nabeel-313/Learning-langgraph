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
            self.travel_planer_node.chat_node
        )

        # Weather Node (ToolNode)
        weather_node = ToolNode(tools=[weather_tool])
        self.graph_builder.add_node("weather_node", weather_node)

        # Search Node
        tools = get_tools()
        search_node = create_tool_node(tools)  # includes TavilySearchResults
        self.graph_builder.add_node("search_node", search_node)

        self.graph_builder.add_node(
            "travel_intent",
            self.travel_planer_node.detect_travel,
        )
        self.graph_builder.add_node(
            "travel_node",
            self.travel_planer_node.travel_node,
        )
        self.graph_builder.add_node(
            "collect_missing_travel_info_node",
            self.travel_planer_node.collect_missing_travel_info,
        )
        self.graph_builder.add_node(
            "flight_node",
            self.travel_planer_node.flight_node,
        )
        self.graph_builder.add_node(
            "hotel_node",
            self.travel_planer_node.hotel_node,
        )

    def _add_edges(self) -> None:
        """Define execution flow between nodes."""
        self.graph_builder.add_edge(START, "router_node")
        self.graph_builder.add_conditional_edges(
            "router_node",
            lambda state: state.get("route"),
            {
                "chat": "travel_intent",
                "weather": "weather_node",
                "search": "search_node",
                # "travel": "travel_node"
            }
        )
        self.graph_builder.add_conditional_edges(
            "travel_intent",
            lambda state: state.get("route"),
            {
                "travel": "travel_node",
                "chat": "chat_node",
            }
        )
        self.graph_builder.add_edge("travel_node",
                                    "collect_missing_travel_info_node")
        self.graph_builder.add_edge("collect_missing_travel_info_node",
                                    "flight_node")
        self.graph_builder.add_edge("flight_node", "hotel_node")
        self.graph_builder.add_edge("chat_node", END)
        self.graph_builder.add_edge("hotel_node", END)
        self.graph_builder.add_edge("weather_node", END)
        self.graph_builder.add_edge("search_node", END)

    def build(self):
        """Build and compile the travel planner graph."""
        self._add_nodes()
        self._add_edges()
        compiled_graph = self.graph_builder.compile()
        # compiled_graph.get_graph().draw_mermaid_png(
        #    output_file_path=r"./logs/travel_routing_2.png")
        return compiled_graph

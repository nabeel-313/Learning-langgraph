from src.langgraph_core.LLMs.load_llms import LoadLLMs
from src.langgraph_core.graphs.travel_planner_graph import TravelGraphBuilder
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.exceptions import ExceptionError
from src.loggers import Logger

# Initialize LLM + Graph
models = LoadLLMs()
llm = models.load_groq_model()
graph_builder = TravelGraphBuilder(llm)
graph = graph_builder.build()

logger = Logger(__name__).get_logger()


def langgraph_chatbot(user_message: str):
    """Handle a single user message with logging and exception handling."""
    try:
        logger.info(f"User message: {user_message}")
        collected_msgs = []

        # Stream responses from graph
        for event in graph.stream({"messages": [
                                    HumanMessage(content=user_message)
                                    ]}):
            for value in event.values():
                # Each node updates state here
                # print("Assistant:", value)
                messages = value.get("messages", [])
                for msg in messages:
                    if isinstance(msg, AIMessage) and msg.content:
                        logger.info(f"Assistant: {msg.content}")
                        lst_msg = msg.content
                        collected_msgs.append(lst_msg)
                        print(collected_msgs)
                        return collected_msgs
                    elif isinstance(msg, ToolMessage):
                        logger.info(f"[Tool Result] {msg.content}")
                        lst_msg = msg.content
                        collected_msgs.append(lst_msg)
                        print(collected_msgs)
                        return collected_msgs
                
    except Exception as e:
        # logger.exception("Chatbot execution failed")
        raise ExceptionError(e)


if __name__ == "__main__":
    print("🤖 Travel Planner Chatbot (type 'quit' to exit)\n")
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            langgraph_chatbot(user_input)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

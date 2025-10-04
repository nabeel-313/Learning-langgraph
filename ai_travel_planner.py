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

conversation_state = {"messages": []}


def langgraph_chatbot(user_message: str):
    """Handle a single user message with logging and exception handling."""
    global conversation_state
    try:
        logger.info(f"User message: {user_message}")

        # Track the current message count BEFORE graph execution
        initial_message_count = len(conversation_state.get("messages", []))

        # Add user message to persisted state
        conversation_state["messages"].append(HumanMessage(content=user_message))

        logger.info(f"DEBUG - State BEFORE graph: awaiting_field = {conversation_state.get('awaiting_field')}")

        # Track only NEW AI messages from this execution
        new_ai_messages = []

        for event in graph.stream(conversation_state):
            for value in event.values():
                conversation_state.update(value)
                logger.info(f"DEBUG - State AFTER update: awaiting_field = {conversation_state.get('awaiting_field')}")

                # Get ALL messages from current state
                all_messages = conversation_state.get("messages", [])

                # Extract only NEW messages added during this execution
                if initial_message_count < len(all_messages):
                    new_messages = all_messages[initial_message_count:]

                    for msg in new_messages:
                        if isinstance(msg, AIMessage) and msg.content:
                            logger.info(f"Assistant: {msg.content}")
                            new_ai_messages.append(msg.content)
                        elif isinstance(msg, ToolMessage) and msg.content:
                            logger.info(f"[Tool Result] {msg.content}")
                            new_ai_messages.append(msg.content)

        # Return only NEW messages from this execution
        return "\n".join(new_ai_messages) if new_ai_messages else "No response."

    except Exception as e:
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

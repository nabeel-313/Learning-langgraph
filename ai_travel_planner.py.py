from src.langgraph_core.LLMs.load_llms import LoadLLMs
from src.langgraph_core.graphs.graph_builder import BasicChatbotGraphBuilder
from src.exceptions import ExceptionError
from src.loggers import logging


models = LoadLLMs()
llm = models.load_gemini_model()
graph_builder = BasicChatbotGraphBuilder(llm)
graph = graph_builder.setup_graph()


def langgraph_chatbot(user_message):
    for event in graph.stream({"messages": ("user", user_message)}):
        print(user_message)
        logging.info(f"User messsage: {user_message}")
        for value in event.values():
            print(value)
            msg = value["messages"]
            print("Assistant:", msg.content)
            logging.info(f"Assistant: {msg.content}")


if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        langgraph_chatbot(user_input)
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

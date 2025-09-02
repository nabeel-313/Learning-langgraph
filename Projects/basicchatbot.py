from src.langgraph_core.LLMs.load_llms import LoadLLMs
from src.langgraph_core.graphs.graph_builder import BasicChatbotGraphBuilder
from src.exceptions import ExceptionError
from src.loggers import logging


def langgraph_chatbot(user_message):
    models = LoadLLMs()
    llm = models.load_gemini_model()
    graph_builder = BasicChatbotGraphBuilder(llm)
    graph = graph_builder.setup_graph()
    for event in graph.stream({"messages": ("user", user_message)}):
        print(user_message)
        logging.info(f"User messsage: {user_message}")
        for value in event.values():
            print(value)
            print("Assistant:", value.content)
            logging.info(f"Assistant: {value.content}")


if __name__ == "__main__":
    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
        langgraph_chatbot(user_input)

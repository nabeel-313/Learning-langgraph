from src.langgraph_core.LLMs.load_llms import LoadLLMs
from src.langgraph_core.graphs.graph_builder import BasicChatbotGraphBuilder
from src.exceptions import ExceptionError
from src.loggers import logging

### not in working condtion don't use as of now
models = LoadLLMs()
llm = models.load_groq_model()
print(llm)
graph_builder=BasicChatbotGraphBuilder(llm)
graph = graph_builder.setup_ainews_graph()
def langgraph_chatbot(user_message):
    
    for event in graph.stream({'messages':("user",user_message)}):
        #print(user_message)
        logging.info(f"User messsage: {user_message}")
        for value in event.values():
            #print(value)
            for msg in value["messages"]:
                # Print only final AI messages that have real content
                if msg.type == "ai" and msg.content:
                    print("Assistant:", msg.content)
                    logging.info(f"Assistant: {msg.content}")
            # msg = value["messages"]
            # print("Assistant:", msg[0].content)
            # logging.info(f"Assistant: {msg[0].content}")
        
if __name__=="__main__":
    while True:
        user_input = input("User: ")
        langgraph_chatbot(user_input)
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        
    
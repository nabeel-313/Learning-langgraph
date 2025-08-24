import uvicorn
from fastapi import FastAPI, Request
from src.langgraph_core.graphs.graph_builder import BasicChatbotGraphBuilder
from src.langgraph_core.LLMs.load_llms import LoadLLMs

import os
from dotenv import load_dotenv
load_dotenv()

app=FastAPI()

print(os.getenv("LANGCHAIN_API_KEY"))

os.environ["LANGSMITH_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")

## API's

@app.post("/blogs")
async def create_blogs(request:Request):
    
    data=await request.json()
    topic= data.get("topic","")

    ## get the llm object

    models = LoadLLMs()
    llm = models.load_groq_model()
    ## get the graph
    graph_builder=BasicChatbotGraphBuilder(llm)
    if topic:
        graph=graph_builder.setup_bloggen_graph(usecase="topic")
        state=graph.invoke({"topic":topic})

    return {"data":state}

if __name__=="__main__":
    uvicorn.run("app:app",host="0.0.0.0",port=8000,reload=True)


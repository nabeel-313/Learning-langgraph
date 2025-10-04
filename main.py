from ai_travel_planner import langgraph_chatbot
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

app = FastAPI(title="Travel AI Assistant", debug=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Renders the main index page.

    :return: The rendered HTML template for the index page.
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.post('/data')
async def get_data(request: Request):
    """
    Handles POST requests to process user data and generate a response.

    :return: A JSON response with the generated output.
        - response: Boolean indicating success.
        - message: The output generated from the user's input.
    """
    data = await request.json()
    text = data.get('data')
    user_input = text
    print(f"User input: {user_input}")

    out = langgraph_chatbot(user_input)

    print("---" * 100)
    print(out)
    print("---" * 100)

    # If output is a dict and includes non-serializable messages, fix it
    if isinstance(out, dict) and "output" in out:
        response_message = out["output"]
    else:
        response_message = str(out)  # Fallback to string

    return JSONResponse({"response": True, "message": response_message})

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)

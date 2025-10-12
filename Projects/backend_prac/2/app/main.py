from fastapi import FastAPI
from app.database import Base, engine
from app.routes import users, travel

app = FastAPI(title="AI Travel Assistant")

Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(travel.router)


@app.get("/")
def root():
    return {"message": "Welcome to AI Travel Assistant API!"}

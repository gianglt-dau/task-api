from fastapi import FastAPI
import os

app = FastAPI()

@app.get("/")
def root():
    return {
        "message": "task-api is running",
        "env": os.getenv("APP_ENV", "dev")
    }

@app.get("/tasks")
def get_tasks():
    return [
        {"id": 1, "title": "Learn Docker"},
        {"id": 2, "title": "Deploy with WSL runner"}
    ]
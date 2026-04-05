from fastapi import FastAPI
from routes import user

app = FastAPI(title="Jachacks-2026")

@app.get("/")
def read_root():
    return {"message": "Welcome to Jachacks-2026 API"}

app.include_router(user.router, prefix="/users", tags=["users"])

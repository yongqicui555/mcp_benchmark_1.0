from fastapi import FastAPI, APIRouter

app = FastAPI()
users = APIRouter(prefix="/users")


@users.get("/")
def list_users():
    return []


@users.get("/{id}")
def get_user(id: str):
    return {"id": id}


@users.post("/")
def create_user():
    return {}


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(users, prefix="/api")

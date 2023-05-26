from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routers import auth, users, admin

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins= ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


models.Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return "copy and the past the link 'http://127.0.0.1:8000/docs#/' in the url"

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)


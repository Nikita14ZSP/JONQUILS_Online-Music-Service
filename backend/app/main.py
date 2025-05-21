from fastapi import FastAPI
from app import models, database
from app.routes import music, users
from fastapi.middleware.cors import CORSMiddleware

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Online Music Service")

# Разрешаем доступ с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роуты
app.include_router(music.router, prefix="/music", tags=["Music"])
app.include_router(users.router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"message": "Welcome to Online Music Service API"}

from fastapi import FastAPI
from database import Base, engine
from routers import user_router, wallet_router, task_router
#pip install pydantic[email]
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user_router)
app.include_router(wallet_router)
app.include_router(task_router)


if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="127.0.0.1", port=8000,reload=True)
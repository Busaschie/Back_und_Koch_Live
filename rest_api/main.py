from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
#from fastapi_offline import FastAPIOffline as FastAPI
from database import Base, engine
from routers import user_router, wallet_router, task_router, waren_router, bestellung_router
Base.metadata.create_all(bind=engine)

app = FastAPI(docs_url=None, redoc_url=None)

# Falls du statische Swagger-JS/CSS-Dateien lokal im Ordner 'static' hast:
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

app.include_router(user_router)
app.include_router(wallet_router)
app.include_router(task_router)
app.include_router(waren_router)
app.include_router(bestellung_router)

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="127.0.0.1", port=8000,reload=True)
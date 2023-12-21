import ast
import logging
from contextlib import asynccontextmanager

import dotenv
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from api import configs, routes
from api._logger import load_logging


@asynccontextmanager
async def main_api_lifespan(app: FastAPI):
    dotenv.load_dotenv()
    load_logging()
    logging.debug("Starting `api.app:app` FastAPI instance.")
    yield
    logging.debug("Shuting Down `api.app:app` FastAPI instance.")


app = FastAPI(lifespan=main_api_lifespan)


@app.middleware("logging")
async def logging_middleware(request: Request, call_next):
    logging.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response


@app.middleware("handle_exception")
async def handle_exception(request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        logging.exception(e)
        if isinstance(e, HTTPException):
            return JSONResponse(e.detail, e.status_code, e.headers)
        try:
            message = ast.literal_eval(str(e))
        except (ValueError, SyntaxError):
            message = str(e)
        return JSONResponse({"error": message, "errorType": type(e).__name__}, 400)


@app.get("/")
async def root():
    return {
        "author": {
            "github": "https://github.com/arv-anshul/",
            "linkedin": "https://linkedin.com/in/arv-anshul/",
        },
        "docs": f"{configs.API_HOST_URL}/docs",
        "message": "🙏 Namaste!",
    }


app.include_router(routes.db.db_route)
app.include_router(routes.youtube.yt_route)

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host=configs.API_HOST,
        port=configs.API_PORT,
        reload=configs.API_RELOAD,
    )

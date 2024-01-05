import ast
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from api import configs, routes
from api.logger import load_logging


@asynccontextmanager
async def main_api_lifespan(app: FastAPI):
    load_logging()
    logging.debug("Starting FastAPI app instance.")
    yield
    logging.debug("Shuting down FastAPI app instance.")


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
app.include_router(routes.ml.router)

if __name__ == "__main__":
    import uvicorn

    if not configs.API_PORT:
        raise ValueError("Provide `API_PORT` as environment variable.")
    if not configs.API_HOST:
        raise ValueError("Provide 'API_HOST' as environment variable.")

    uvicorn.run(
        app,
        host=configs.API_HOST,
        port=int(configs.API_PORT),
    )

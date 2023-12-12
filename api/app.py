from contextlib import asynccontextmanager

import dotenv
import uvicorn
from fastapi import FastAPI

from api import configs, routes


@asynccontextmanager
async def main_api_lifespan(app: FastAPI):
    dotenv.load_dotenv()
    yield


app = FastAPI(lifespan=main_api_lifespan)


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

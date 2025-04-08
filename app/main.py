from fastapi import FastAPI
from starlette.responses import RedirectResponse
from app.api.v1 import user_router

app = FastAPI()
# uvicorn app.main:app --reload
app.include_router(user_router.router, prefix="/api/v1/users", tags=["users"])

@app.get("/")
def redirect_to_docs():
    return RedirectResponse(url="/docs")

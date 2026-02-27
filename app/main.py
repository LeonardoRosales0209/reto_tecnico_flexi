from fastapi import FastAPI
from app.api.routes.subscriptions import router as subscriptions_router
from app.api.routes.events import router as events_router
from app.api.routes.deliveries import router as deliveries_router

app = FastAPI(title="hookshot")

app.include_router(subscriptions_router)
app.include_router(events_router)
app.include_router(deliveries_router)


@app.get("/health")
def health():
    return {"status": "ok"}
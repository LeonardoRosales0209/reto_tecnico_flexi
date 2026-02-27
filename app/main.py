from fastapi import FastAPI

app = FastAPI(title="hookshot")

@app.get("/health")
def health():
    return {"status": "ok"}
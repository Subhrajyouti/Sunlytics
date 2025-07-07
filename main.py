# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from calculator_api import run_calculator

app = FastAPI(title="Residential Solar Calculator API", version="1.0")

# 1) CORS: only your site can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://subhrajyoti.online",   # your production site
        "http://localhost:3000",         # for local dev
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2) Request/response model
class InputData(BaseModel):
    state: str
    monthly_units: float
    latlong: str    # e.g. "26.44,91.41"

@app.post("/api/calculate")
def calculate(data: InputData):
    return run_calculator(
        state=data.state,
        mthly=data.monthly_units,
        latlong=data.latlong
    )
    
# 3) Run on $PORT or default 8000
if __name__ == "__main__":
    import os, uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

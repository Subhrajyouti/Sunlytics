from fastapi import FastAPI
from pydantic import BaseModel
from calculator_api import run_calculator  # import your logic here

app = FastAPI()

class InputData(BaseModel):
    state: str
    monthly_units: float
    latitude: float
    longitude: float

@app.post("/api/calculate")
def calculate(data: InputData):
    result = run_calculator(
        data.state,
        data.monthly_units,
        data.latitude,
        data.longitude
    )
    return result

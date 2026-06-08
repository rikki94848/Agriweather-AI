from fastapi import FastAPI
from pydantic import BaseModel
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from datetime import datetime

app = FastAPI(
    title="AgriWeather AI Service",
    description="AI Service untuk prediksi hasil panen padi menggunakan Machine Learning",
    version="1.0.0",
)

# Dataset simulasi awal untuk melatih model
# Format fitur:
# rainfall, temperature, harvest_area, previous_production
X_train = np.array(
    [
        [2200, 27.0, 1000, 6000],
        [2500, 27.5, 1200, 7200],
        [2800, 26.8, 1500, 9000],
        [1800, 28.0, 900, 5000],
        [3100, 29.5, 1100, 6200],
        [1600, 30.0, 800, 4200],
        [2400, 26.5, 1300, 7800],
        [2700, 27.2, 1400, 8500],
        [2000, 28.4, 950, 5600],
        [3000, 26.9, 1600, 9700],
    ]
)

# Target produksi padi
y_train = np.array([6300, 7600, 9300, 5200, 6000, 3900, 8100, 8800, 5700, 10000])

# Model Machine Learning
model = RandomForestRegressor(n_estimators=100, random_state=42)

model.fit(X_train, y_train)


class PredictionInput(BaseModel):
    region: str
    year: int
    rainfall: float
    temperature: float
    harvest_area: float
    previous_production: float


@app.get("/")
def root():
    return {"message": "AgriWeather AI Service", "status": "running"}


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai-service",
        "model": "RandomForestRegressor",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/predict")
def predict_harvest(data: PredictionInput):
    input_data = np.array(
        [[data.rainfall, data.temperature, data.harvest_area, data.previous_production]]
    )

    predicted_production = model.predict(input_data)[0]

    if predicted_production >= data.previous_production:
        risk_level = "Rendah"
        recommendation = (
            "Prediksi hasil panen menunjukkan kondisi baik. "
            "Pertahankan pola tanam, pemantauan cuaca, dan pengelolaan irigasi secara berkala."
        )
    elif predicted_production >= data.previous_production * 0.85:
        risk_level = "Sedang"
        recommendation = (
            "Terdapat potensi penurunan hasil panen. "
            "Disarankan melakukan pemantauan curah hujan, suhu, dan ketersediaan air."
        )
    else:
        risk_level = "Tinggi"
        recommendation = (
            "Risiko penurunan hasil panen cukup tinggi. "
            "Disarankan melakukan penyesuaian jadwal tanam, pengelolaan irigasi, dan mitigasi risiko cuaca."
        )

    return {
        "message": "Prediksi berhasil dibuat oleh AI Service",
        "model": "RandomForestRegressor",
        "input": {
            "region": data.region,
            "year": data.year,
            "rainfall": data.rainfall,
            "temperature": data.temperature,
            "harvest_area": data.harvest_area,
            "previous_production": data.previous_production,
        },
        "result": {
            "region": data.region,
            "year": data.year,
            "predicted_production": round(float(predicted_production), 2),
            "risk_level": risk_level,
            "recommendation": recommendation,
            "created_at": datetime.now().isoformat(),
        },
    }

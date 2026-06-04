from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(
    title="AgriWeather AI Backend API",
    description="Backend API untuk sistem prediksi risiko dan hasil panen padi berbasis Cloud Native",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agriculture_data = [
    {
        "id": 1,
        "region": "Bandung",
        "year": 2024,
        "rainfall": 2500,
        "temperature": 27.5,
        "harvest_area": 1200,
        "production": 7200,
    },
    {
        "id": 2,
        "region": "Garut",
        "year": 2024,
        "rainfall": 2800,
        "temperature": 26.8,
        "harvest_area": 1500,
        "production": 9000,
    },
]

prediction_history = []


class PredictionInput(BaseModel):
    region: str
    year: int
    rainfall: float
    temperature: float
    harvest_area: float
    previous_production: float


@app.get("/")
def root():
    return {"message": "AgriWeather AI Backend API", "status": "running"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "backend-api", "timestamp": datetime.now()}


@app.get("/agriculture-data")
def get_agriculture_data():
    return {"message": "Data pertanian berhasil diambil", "data": agriculture_data}


@app.post("/predict")
def predict_harvest(data: PredictionInput):
    # Untuk Minggu 2, prediksi masih simulasi awal.
    # Nanti pada tahap AI Service, bagian ini akan dihubungkan ke model Scikit-learn.

    rainfall_factor = 1.05 if 1800 <= data.rainfall <= 3000 else 0.90
    temperature_factor = 1.03 if 24 <= data.temperature <= 29 else 0.92
    area_factor = data.harvest_area * 5.8

    predicted_production = (
        ((data.previous_production * 0.5) + (area_factor * 0.5))
        * rainfall_factor
        * temperature_factor
    )

    if predicted_production >= data.previous_production:
        risk_level = "Rendah"
        recommendation = "Kondisi cukup baik. Pertahankan pola tanam dan pemantauan cuaca secara berkala."
    elif predicted_production >= data.previous_production * 0.85:
        risk_level = "Sedang"
        recommendation = "Terdapat potensi penurunan produksi. Perlu pemantauan curah hujan, suhu, dan pengelolaan irigasi."
    else:
        risk_level = "Tinggi"
        recommendation = "Risiko penurunan hasil panen cukup tinggi. Disarankan melakukan penyesuaian jadwal tanam dan pengelolaan air."

    result = {
        "region": data.region,
        "year": data.year,
        "predicted_production": round(predicted_production, 2),
        "risk_level": risk_level,
        "recommendation": recommendation,
        "created_at": datetime.now().isoformat(),
    }

    prediction_history.append(result)

    return {
        "message": "Prediksi hasil panen berhasil dibuat",
        "input": data,
        "result": result,
    }


@app.get("/predictions")
def get_predictions():
    return {"message": "Riwayat prediksi berhasil diambil", "data": prediction_history}


@app.post("/upload-dataset")
async def upload_dataset(file: UploadFile = File(...)):
    # Untuk tahap awal, endpoint ini baru menerima file.
    # Pada tahap berikutnya akan dihubungkan ke Google Cloud Storage.

    return {
        "message": "File dataset berhasil diterima",
        "filename": file.filename,
        "content_type": file.content_type,
        "note": "Integrasi Google Cloud Storage akan ditambahkan pada tahap berikutnya.",
    }

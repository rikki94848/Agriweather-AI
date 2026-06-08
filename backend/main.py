from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import httpx

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

AI_SERVICE_URL = "http://localhost:8001"


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
async def predict_harvest(data: PredictionInput):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AI_SERVICE_URL}/predict", json=data.dict(), timeout=10.0
            )

        response.raise_for_status()
        ai_response = response.json()

        result = ai_response["result"]
        prediction_history.append(result)

        return {
            "message": "Prediksi berhasil dibuat melalui integrasi Backend API dan AI Service",
            "source": "AI Service",
            "input": data,
            "result": result,
        }

    except httpx.ConnectError:
        return {
            "message": "Gagal terhubung ke AI Service",
            "error": "Pastikan AI Service berjalan di http://localhost:8001",
        }

    except Exception as e:
        return {"message": "Terjadi kesalahan saat memproses prediksi", "error": str(e)}


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


@app.get("/ai-health")
async def check_ai_service():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{AI_SERVICE_URL}/health", timeout=10.0)

        response.raise_for_status()

        return {
            "message": "AI Service berhasil terhubung",
            "ai_service": response.json(),
        }

    except httpx.ConnectError:
        return {
            "message": "Gagal terhubung ke AI Service",
            "error": "Pastikan AI Service berjalan di http://localhost:8001",
        }

    except Exception as e:
        return {
            "message": "Terjadi kesalahan saat mengecek AI Service",
            "error": str(e),
        }

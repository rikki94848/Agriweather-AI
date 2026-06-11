from google.cloud import storage
import uuid
from sqlalchemy import text
from database import engine
from database import SessionLocal
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
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

load_dotenv()

GCS_PROJECT_ID = os.getenv("GCS_PROJECT_ID", "project-b47a591b-d513-4f00-b43")
GCS_BUCKET_NAME = os.getenv(
    "GCS_BUCKET_NAME", "agriweather-ai-datasets-rikki-152022055"
)

AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8001")


class PredictionInput(BaseModel):
    region: str
    year: int
    rainfall: float
    temperature: float
    harvest_area: float
    previous_production: float


class PredictAutoRequest(BaseModel):
    region: str
    year: int


def get_weather_from_nasa_power(latitude: float, longitude: float, year: int):
    """
    Mengambil data cuaca tahunan dari NASA POWER berdasarkan koordinat.
    Data yang dipakai:
    - T2M: suhu rata-rata 2 meter
    - PRECTOTCORR: total curah hujan/presipitasi
    """

    url = "https://power.larc.nasa.gov/api/temporal/daily/point"

    params = {
        "parameters": "T2M,PRECTOTCORR",
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": f"{year}0101",
        "end": f"{year}1231",
        "format": "JSON",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()
    parameter_data = data["properties"]["parameter"]

    temperature_values = [
        value
        for value in parameter_data["T2M"].values()
        if value is not None and value != -999
    ]

    rainfall_values = [
        value
        for value in parameter_data["PRECTOTCORR"].values()
        if value is not None and value != -999
    ]

    if not temperature_values or not rainfall_values:
        raise ValueError(
            "Data cuaca dari NASA POWER tidak tersedia untuk wilayah/tahun tersebut"
        )

    avg_temperature = sum(temperature_values) / len(temperature_values)
    total_rainfall = sum(rainfall_values)

    return {
        "temperature": round(avg_temperature, 2),
        "rainfall": round(total_rainfall, 2),
        "source": "NASA POWER",
    }


@app.get("/")
def root():
    return {"message": "AgriWeather AI Backend API", "status": "running"}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "backend-api", "timestamp": datetime.now()}


@app.get("/agriculture-data")
def get_agriculture_data():
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT 
                    agriculture_data.id,
                    regions.name AS region,
                    regions.province,
                    agriculture_data.year,
                    agriculture_data.rainfall,
                    agriculture_data.temperature,
                    agriculture_data.harvest_area,
                    agriculture_data.production
                FROM agriculture_data
                JOIN regions ON agriculture_data.region_id = regions.id
                ORDER BY agriculture_data.year DESC
            """)).mappings().all()

        return {
            "message": "Data pertanian berhasil diambil dari database",
            "data": [dict(row) for row in rows],
        }

    except Exception as e:
        return {"message": "Gagal mengambil data pertanian", "error": str(e)}


@app.get("/regions")
def get_regions():
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id, name, province, latitude, longitude
            FROM regions
            ORDER BY name ASC
        """))

        regions = []
        for row in result:
            regions.append(
                {
                    "id": row.id,
                    "name": row.name,
                    "province": row.province,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                }
            )

        return {
            "message": "Data wilayah berhasil diambil dari database",
            "data": regions,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Gagal mengambil data wilayah",
            "error": str(e),
        }

    finally:
        db.close()


@app.get("/weather")
def get_weather(region: str, year: int):
    db = SessionLocal()
    try:
        result = db.execute(
            text("""
            SELECT id, name, province, latitude, longitude
            FROM regions
            WHERE name = :region
            LIMIT 1
        """),
            {"region": region},
        )

        region_data = result.fetchone()

        if not region_data:
            return {"status": "error", "message": "Wilayah tidak ditemukan di database"}

        if region_data.latitude is None or region_data.longitude is None:
            return {"status": "error", "message": "Koordinat wilayah belum tersedia"}

        weather = get_weather_from_nasa_power(
            latitude=region_data.latitude, longitude=region_data.longitude, year=year
        )

        return {
            "message": "Data cuaca berhasil diambil dari NASA POWER",
            "region": region_data.name,
            "province": region_data.province,
            "year": year,
            "latitude": region_data.latitude,
            "longitude": region_data.longitude,
            "weather": weather,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Gagal mengambil data cuaca",
            "error": str(e),
        }

    finally:
        db.close()


@app.post("/predict-auto")
def predict_auto(request: PredictAutoRequest):
    db = SessionLocal()

    try:
        # Ambil data wilayah dan koordinat
        region_result = db.execute(
            text("""
            SELECT id, name, province, latitude, longitude
            FROM regions
            WHERE name = :region
            LIMIT 1
        """),
            {"region": request.region},
        )

        region_data = region_result.fetchone()

        if not region_data:
            return {"status": "error", "message": "Wilayah tidak ditemukan di database"}

        if region_data.latitude is None or region_data.longitude is None:
            return {"status": "error", "message": "Koordinat wilayah belum tersedia"}

        # Ambil data pertanian terakhir sebelum tahun prediksi
        agriculture_result = db.execute(
            text("""
            SELECT 
                ad.year,
                ad.harvest_area,
                ad.production
            FROM agriculture_data ad
            JOIN regions r ON ad.region_id = r.id
            WHERE r.name = :region
              AND ad.year < :prediction_year
            ORDER BY ad.year DESC
            LIMIT 1
        """),
            {"region": request.region, "prediction_year": request.year},
        )

        agriculture_data = agriculture_result.fetchone()

        if not agriculture_data:
            return {
                "status": "error",
                "message": "Data pertanian sebelumnya belum tersedia untuk wilayah tersebut",
            }

        # Data cuaca diambil berdasarkan tahun data pertanian sebelumnya
        weather_year = agriculture_data.year

        weather = get_weather_from_nasa_power(
            latitude=region_data.latitude,
            longitude=region_data.longitude,
            year=weather_year,
        )

        # Payload otomatis untuk AI Service
        ai_payload = {
            "region": region_data.name,
            "year": request.year,
            "rainfall": weather["rainfall"],
            "temperature": weather["temperature"],
            "harvest_area": agriculture_data.harvest_area,
            "previous_production": agriculture_data.production,
        }

        ai_response = requests.post(
            f"{AI_SERVICE_URL}/predict", json=ai_payload, timeout=30
        )
        ai_response.raise_for_status()

        raw_ai_result = ai_response.json()
        ai_result = raw_ai_result.get("result", raw_ai_result)

        predicted_production = ai_result.get("predicted_production")
        risk_level = ai_result.get("risk_level")
        recommendation = ai_result.get("recommendation")

        # Simpan hasil prediksi ke database
        db.execute(
            text("""
            INSERT INTO predictions 
            (region_id, year, predicted_production, risk_level, recommendation)
            VALUES 
            (:region_id, :year, :predicted_production, :risk_level, :recommendation)
        """),
            {
                "region_id": region_data.id,
                "year": request.year,
                "predicted_production": predicted_production,
                "risk_level": risk_level,
                "recommendation": recommendation,
            },
        )

        db.commit()

        return {
            "message": "Prediksi otomatis berhasil dibuat",
            "mode": "automatic",
            "input_source": {
                "region": "database",
                "weather": weather["source"],
                "agriculture_data": "database",
            },
            "region": {
                "name": region_data.name,
                "province": region_data.province,
                "latitude": region_data.latitude,
                "longitude": region_data.longitude,
            },
            "weather_year": weather_year,
            "auto_input": ai_payload,
            "result": {
                "region": region_data.name,
                "year": request.year,
                "predicted_production": predicted_production,
                "risk_level": risk_level,
                "recommendation": recommendation,
            },
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "message": "Gagal membuat prediksi otomatis",
            "error": str(e),
        }

    finally:
        db.close()


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
        with engine.begin() as conn:
            region = conn.execute(
                text("SELECT id FROM regions WHERE name = :name"), {"name": data.region}
            ).fetchone()

            if region:
                region_id = region[0]
            else:
                insert_region = conn.execute(
                    text(
                        "INSERT INTO regions (name, province) VALUES (:name, :province)"
                    ),
                    {"name": data.region, "province": "Jawa Barat"},
                )
                region_id = insert_region.lastrowid

            conn.execute(
                text("""
                    INSERT INTO predictions 
                    (region_id, year, predicted_production, risk_level, recommendation)
                    VALUES 
                    (:region_id, :year, :predicted_production, :risk_level, :recommendation)
                """),
                {
                    "region_id": region_id,
                    "year": result["year"],
                    "predicted_production": result["predicted_production"],
                    "risk_level": result["risk_level"],
                    "recommendation": result["recommendation"],
                },
            )
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
    try:
        with engine.connect() as conn:
            rows = conn.execute(text("""
                SELECT 
                    predictions.id,
                    regions.name AS region,
                    predictions.year,
                    predictions.predicted_production,
                    predictions.risk_level,
                    predictions.recommendation,
                    predictions.created_at
                FROM predictions
                JOIN regions ON predictions.region_id = regions.id
                ORDER BY predictions.created_at DESC
            """)).mappings().all()

        return {
            "message": "Riwayat prediksi berhasil diambil dari database",
            "data": [dict(row) for row in rows],
        }

    except Exception as e:
        return {"message": "Gagal mengambil riwayat prediksi", "error": str(e)}


@app.post("/upload-dataset")
async def upload_dataset(file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(".csv"):
            return {"status": "error", "message": "File harus berformat CSV"}

        storage_client = storage.Client(project=GCS_PROJECT_ID)
        bucket = storage_client.bucket(GCS_BUCKET_NAME)

        unique_filename = f"datasets/{uuid.uuid4()}-{file.filename}"
        blob = bucket.blob(unique_filename)

        file_content = await file.read()

        blob.upload_from_string(file_content, content_type=file.content_type)

        return {
            "status": "success",
            "message": "Dataset berhasil diunggah ke Google Cloud Storage",
            "bucket": GCS_BUCKET_NAME,
            "filename": file.filename,
            "object_name": unique_filename,
            "gcs_path": f"gs://{GCS_BUCKET_NAME}/{unique_filename}",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Gagal mengunggah dataset ke Google Cloud Storage",
            "error": str(e),
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


@app.get("/db-health")
def db_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "service": "mysql-database",
            "message": "Database berhasil terhubung",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Database gagal terhubung",
            "error": str(e),
        }

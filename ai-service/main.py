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

# Dataset training berdasarkan skala data resmi Jawa Barat 2025
# Format fitur:
# rainfall, temperature, harvest_area, previous_production
base_data = np.array(
    [
        [2819.16, 24.99, 59502, 345984],  # Bogor
        [3278.78, 24.11, 122485, 660107],  # Sukabumi
        [3278.78, 24.11, 137496, 800735],  # Cianjur
        [3294.84, 21.74, 55849, 353307],  # Bandung
        [3285.92, 23.03, 94041, 555727],  # Garut
        [4379.37, 24.31, 97519, 524895],  # Tasikmalaya
        [4379.37, 24.31, 58549, 331255],  # Ciamis
        [3396.71, 25.15, 48264, 249686],  # Kuningan
        [3269.07, 28.10, 93883, 568548],  # Cirebon
        [3285.92, 23.03, 89930, 496250],  # Majalengka
        [3285.92, 23.03, 55012, 294027],  # Sumedang
        [3028.29, 26.71, 239498, 1583260],  # Indramayu
        [2831.21, 25.66, 184319, 1094780],  # Subang
        [2831.21, 25.66, 33459, 188774],  # Purwakarta
        [2831.21, 25.66, 202293, 1194710],  # Karawang
        [2925.18, 27.63, 97547, 500189],  # Bekasi
        [3294.84, 21.74, 37006, 215065],  # Bandung Barat
        [3516.63, 25.60, 30469, 160944],  # Pangandaran
        [2819.16, 24.99, 141, 805],  # Kota Bogor
        [3278.78, 24.11, 2721, 15835],  # Kota Sukabumi
        [3294.84, 21.74, 1010, 6978],  # Kota Bandung
        [3269.07, 28.10, 125, 676],  # Kota Cirebon
        [2925.18, 27.63, 184, 897],  # Kota Bekasi
        [2819.16, 24.99, 10, 52],  # Kota Depok
        [3294.84, 21.74, 97, 575],  # Kota Cimahi
        [4379.37, 24.31, 8571, 50779],  # Kota Tasikmalaya
        [3516.63, 25.60, 5321, 31808],  # Kota Banjar
    ],
    dtype=float,
)


def estimate_target(row):
    rainfall, temperature, harvest_area, previous_production = row

    # Faktor cuaca sederhana:
    # Curah hujan cukup dan suhu sedang dianggap lebih mendukung produksi.
    weather_factor = 1.0

    if 2500 <= rainfall <= 3800:
        weather_factor += 0.03
    elif rainfall < 1800 or rainfall > 4500:
        weather_factor -= 0.08

    if 22 <= temperature <= 27:
        weather_factor += 0.02
    elif temperature > 29:
        weather_factor -= 0.05

    # Faktor luas panen: wilayah dengan luas panen besar cenderung stabil.
    if harvest_area >= 50000:
        weather_factor += 0.01

    estimated_production = previous_production * weather_factor
    return estimated_production


# Augmentasi data agar model mengenali kondisi rendah, normal, dan baik
X_train = []
y_train = []

for row in base_data:
    rainfall, temperature, harvest_area, previous_production = row

    # kondisi aktual
    X_train.append(row)
    y_train.append(estimate_target(row))

    # skenario cuaca kurang baik
    X_train.append(
        [rainfall * 0.75, temperature + 2, harvest_area, previous_production]
    )
    y_train.append(previous_production * 0.90)

    # skenario cuaca baik
    X_train.append([rainfall * 1.05, temperature, harvest_area, previous_production])
    y_train.append(previous_production * 1.05)

X_train = np.array(X_train, dtype=float)
y_train = np.array(y_train, dtype=float)

model = RandomForestRegressor(n_estimators=200, random_state=42, max_depth=8)

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
        "dataset_scale": "Jawa Barat 2025 official-scale data",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/predict")
def predict_harvest(data: PredictionInput):
    input_data = np.array(
        [
            [
                data.rainfall,
                data.temperature,
                data.harvest_area,
                data.previous_production,
            ]
        ],
        dtype=float,
    )

    predicted_production = model.predict(input_data)[0]

    # Safety rule agar prediksi tidak keluar terlalu jauh dari skala produksi sebelumnya
    min_reasonable = data.previous_production * 0.80
    max_reasonable = data.previous_production * 1.20
    predicted_production = max(
        min_reasonable, min(predicted_production, max_reasonable)
    )

    if predicted_production >= data.previous_production:
        risk_level = "Rendah"
        recommendation = (
            "Prediksi hasil panen menunjukkan kondisi baik. "
            "Pertahankan pola tanam, pemantauan cuaca, dan pengelolaan irigasi secara berkala."
        )
    elif predicted_production >= data.previous_production * 0.90:
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

    if risk_level == "Rendah":
        margin = 0.05
    elif risk_level == "Sedang":
        margin = 0.10
    else:
        margin = 0.15

    prediction_min = predicted_production * (1 - margin)
    prediction_max = predicted_production * (1 + margin)

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
            "prediction_range": {
                "min": round(float(prediction_min), 2),
                "max": round(float(prediction_max), 2),
                "margin_percent": int(margin * 100),
            },
            "risk_level": risk_level,
            "recommendation": recommendation,
            "created_at": datetime.now().isoformat(),
        },
    }

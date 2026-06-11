import React, { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [backendStatus, setBackendStatus] = useState("-");
  const [aiStatus, setAiStatus] = useState("-");
  const [dbStatus, setDbStatus] = useState("-");
  const [agricultureData, setAgricultureData] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [predictionResult, setPredictionResult] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [regions, setRegions] = useState([]);
  const [autoMessage, setAutoMessage] = useState("");

  const [form, setForm] = useState({
    region: "Bandung",
    year: 2025,
    rainfall: 2600,
    temperature: 27,
    harvest_area: 1200,
    previous_production: 7200,
  });

  const [autoForm, setAutoForm] = useState({
    region: "Bandung",
    year: 2025,
  });

  useEffect(() => {
    fetchHealth();
    fetchRegions();
    fetchAgricultureData();
    fetchPredictions();
  }, []);

  const fetchHealth = async () => {
    try {
      const backend = await fetch(`${API_URL}/health`).then((res) =>
        res.json(),
      );
      setBackendStatus(backend.status || "ok");

      const ai = await fetch(`${API_URL}/ai-health`).then((res) => res.json());
      setAiStatus(ai.ai_service?.status || "ok");

      const db = await fetch(`${API_URL}/db-health`).then((res) => res.json());
      setDbStatus(db.status || "ok");
    } catch (error) {
      console.error(error);
    }
  };

  const fetchRegions = async () => {
    try {
      const response = await fetch(`${API_URL}/regions`);
      const result = await response.json();
      setRegions(result.data || []);
    } catch (error) {
      console.error(error);
    }
  };

  const fetchAgricultureData = async () => {
    try {
      const response = await fetch(`${API_URL}/agriculture-data`);
      const result = await response.json();
      setAgricultureData(result.data || []);
    } catch (error) {
      console.error(error);
    }
  };

  const fetchPredictions = async () => {
    try {
      const response = await fetch(`${API_URL}/predictions`);
      const result = await response.json();
      setPredictions(result.data || []);
    } catch (error) {
      console.error(error);
    }
  };

  const handleChange = (event) => {
    setForm({
      ...form,
      [event.target.name]: event.target.value,
    });
  };

  const handleAutoChange = (event) => {
    setAutoForm({
      ...autoForm,
      [event.target.name]: event.target.value,
    });
  };

  const handlePredict = async (event) => {
    event.preventDefault();

    const payload = {
      region: form.region,
      year: Number(form.year),
      rainfall: Number(form.rainfall),
      temperature: Number(form.temperature),
      harvest_area: Number(form.harvest_area),
      previous_production: Number(form.previous_production),
    };

    try {
      const response = await fetch(`${API_URL}/predict`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json();

      setPredictionResult({
        ...result.result,
        mode: "manual",
      });

      fetchPredictions();
    } catch (error) {
      console.error(error);
    }
  };

  const handleAutoPredict = async (event) => {
    event.preventDefault();
    setAutoMessage("Mengambil data cuaca dan membuat prediksi otomatis...");

    const payload = {
      region: autoForm.region,
      year: Number(autoForm.year),
    };

    try {
      const response = await fetch(`${API_URL}/predict-auto`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json();

      if (result.status === "error") {
        setAutoMessage(result.message || "Prediksi otomatis gagal");
        return;
      }

      setPredictionResult({
        ...result.result,
        mode: "automatic",
        auto_input: result.auto_input,
        input_source: result.input_source,
        weather_year: result.weather_year,
      });

      setAutoMessage("Prediksi otomatis berhasil dibuat.");
      fetchPredictions();
    } catch (error) {
      console.error(error);
      setAutoMessage("Prediksi otomatis gagal.");
    }
  };

  const handleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/upload-dataset`, {
        method: "POST",
        body: formData,
      });

      const result = await response.json();
      setUploadMessage(result.message || "File berhasil diunggah");
    } catch (error) {
      console.error(error);
      setUploadMessage("Upload gagal");
    }
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>AgriWeather AI</h1>
          <p>
            Sistem Prediksi Risiko dan Hasil Panen Padi Berbasis Cloud Native
          </p>
        </div>
        <span className="badge">SDGs Ketahanan Pangan</span>
      </header>

      <section className="cards">
        <div className="card">
          <h3>Backend API</h3>
          <p>{backendStatus}</p>
        </div>
        <div className="card">
          <h3>AI Service</h3>
          <p>{aiStatus}</p>
        </div>
        <div className="card">
          <h3>Database</h3>
          <p>{dbStatus}</p>
        </div>
      </section>

      <section className="grid">
        <div className="panel">
          <h2>Prediksi Otomatis</h2>
          <p>
            Pengguna cukup memilih wilayah dan tahun. Sistem akan mengambil data
            cuaca dari NASA POWER serta data pertanian dari database.
          </p>

          <form onSubmit={handleAutoPredict} className="form">
            <label>Wilayah</label>
            <select
              name="region"
              value={autoForm.region}
              onChange={handleAutoChange}
            >
              {regions.length > 0 ? (
                regions.map((region) => (
                  <option key={region.id} value={region.name}>
                    {region.name} - {region.province}
                  </option>
                ))
              ) : (
                <>
                  <option value="Bandung">Bandung</option>
                  <option value="Garut">Garut</option>
                </>
              )}
            </select>

            <label>Tahun Prediksi</label>
            <input
              name="year"
              type="number"
              value={autoForm.year}
              onChange={handleAutoChange}
            />

            <button type="submit">Prediksi Otomatis</button>
          </form>

          <p>{autoMessage}</p>
        </div>

        <div className="panel">
          <h2>Form Prediksi Manual</h2>
          <p>
            Mode manual digunakan untuk pengujian teknis dengan input curah
            hujan, suhu, luas panen, dan produksi sebelumnya.
          </p>

          <form onSubmit={handlePredict} className="form">
            <label>Wilayah</label>
            <input name="region" value={form.region} onChange={handleChange} />

            <label>Tahun</label>
            <input
              name="year"
              type="number"
              value={form.year}
              onChange={handleChange}
            />

            <label>Curah Hujan</label>
            <input
              name="rainfall"
              type="number"
              value={form.rainfall}
              onChange={handleChange}
            />

            <label>Suhu Rata-rata</label>
            <input
              name="temperature"
              type="number"
              value={form.temperature}
              onChange={handleChange}
            />

            <label>Luas Panen</label>
            <input
              name="harvest_area"
              type="number"
              value={form.harvest_area}
              onChange={handleChange}
            />

            <label>Produksi Sebelumnya</label>
            <input
              name="previous_production"
              type="number"
              value={form.previous_production}
              onChange={handleChange}
            />

            <button type="submit">Prediksi Manual</button>
          </form>
        </div>
      </section>

      <section className="grid">
        <div className="panel">
          <h2>Hasil Prediksi AI</h2>
          {predictionResult ? (
            <div className="result">
              <h3>
                {predictionResult.region} - {predictionResult.year}
              </h3>

              <p>
                <b>Mode Prediksi:</b>{" "}
                {predictionResult.mode === "automatic" ? "Otomatis" : "Manual"}
              </p>

              <p>
                <b>Prediksi Produksi:</b>{" "}
                {predictionResult.predicted_production} ton
              </p>

              <p>
                <b>Kategori Risiko:</b> {predictionResult.risk_level}
              </p>

              <p>
                <b>Rekomendasi:</b> {predictionResult.recommendation}
              </p>

              {predictionResult.mode === "automatic" &&
                predictionResult.auto_input && (
                  <div>
                    <h4>Data Otomatis yang Digunakan</h4>
                    <p>
                      <b>Sumber Cuaca:</b>{" "}
                      {predictionResult.input_source?.weather}
                    </p>
                    <p>
                      <b>Tahun Data Cuaca:</b> {predictionResult.weather_year}
                    </p>
                    <p>
                      <b>Curah Hujan:</b> {predictionResult.auto_input.rainfall}
                    </p>
                    <p>
                      <b>Suhu Rata-rata:</b>{" "}
                      {predictionResult.auto_input.temperature}
                    </p>
                    <p>
                      <b>Luas Panen:</b>{" "}
                      {predictionResult.auto_input.harvest_area}
                    </p>
                    <p>
                      <b>Produksi Sebelumnya:</b>{" "}
                      {predictionResult.auto_input.previous_production}
                    </p>
                  </div>
                )}
            </div>
          ) : (
            <p>Belum ada hasil prediksi.</p>
          )}
        </div>

        <div className="panel">
          <h2>Upload Dataset</h2>
          <p>
            Upload dataset digunakan oleh admin untuk menyimpan file CSV ke
            Google Cloud Storage sebagai object storage multi-cloud.
          </p>
          <input type="file" accept=".csv" onChange={handleUpload} />
          <p>{uploadMessage}</p>
        </div>
      </section>

      <section className="panel">
        <h2>Data Pertanian dan Cuaca</h2>
        <table>
          <thead>
            <tr>
              <th>Wilayah</th>
              <th>Provinsi</th>
              <th>Tahun</th>
              <th>Curah Hujan</th>
              <th>Suhu</th>
              <th>Luas Panen</th>
              <th>Produksi</th>
            </tr>
          </thead>
          <tbody>
            {agricultureData.map((item) => (
              <tr key={item.id}>
                <td>{item.region}</td>
                <td>{item.province}</td>
                <td>{item.year}</td>
                <td>{item.rainfall}</td>
                <td>{item.temperature}</td>
                <td>{item.harvest_area}</td>
                <td>{item.production}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Riwayat Prediksi</h2>
        <table>
          <thead>
            <tr>
              <th>Wilayah</th>
              <th>Tahun</th>
              <th>Prediksi Produksi</th>
              <th>Risiko</th>
              <th>Waktu</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map((item) => (
              <tr key={item.id}>
                <td>{item.region}</td>
                <td>{item.year}</td>
                <td>{item.predicted_production}</td>
                <td>{item.risk_level}</td>
                <td>{item.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

export default App;

# Containerized BioSignal Processing Pipeline

A production-grade, test-driven FastAPI microservice designed to ingest 48kHz audio signals, execute downsampling, apply digital bandpass filters, and calculate breathing rates (BPM) using epoch processing and peak detection. 

This repository is architected to mirror enterprise MLOps standards, featuring isolated software environments, structural unit testing, containerization, and fully automated cloud CI/CD pipelines.

---

## 🏗️ System Architecture & Data Flow

```text
 [ Client Layer ]              [ Infrastructure Boundary ]        [ Isolated Container Core ]
+────────────────+            +───────────────────────────+      +───────────────────────────+

|                |            |                           |      |  [ Docker Linux Sandbox ] |
|  Web Browser   |            |   GCP Cloud Run / WSL     |      |                           |
|       or       |            |                           |      |     +─────────────────+   |
|   API Client   |            |                           |      |     |   FastAPI App   |   |
|  (Swagger UI)  |            |                           |      |     |    (main.py)    |   |
|                |            |                           |      |     +────────┬────────+   |
+───────┬────────+            +─────────────┬─────────────+      |              │            |
        │                                   │                    |              │ Imports    |
        │ HTTP POST Request                 │ Tunnels Traffic    |              ▼            |
        │ /analyze-breathing-rate           │ Via Port Mapping   |     +─────────────────+   |
        └───────────────────────────────────┼───────────────────►│     | Signal Pipelines|   |
                                            │    -p 8080:8080    |     |   (utils.py)    |   |
                                            │                    |     +────────┬────────+   |
                                            │                    |              │            |
                                            │                    |              │ Math APIs  |
                                            │                    |              ▼            |
                                            │                    |     +─────────────────+   |
                                            │                    |     |  SciPy & NumPy  |   |
                                            │                    |     +─────────────────+   |
                                            +────────────────────+───────────────────────────+
```

### Data Transformation Workflow
1. **Validation (FastAPI & Pydantic):** Ingestion requests are validated at the gateway. Signals under 48,000 samples (1 second at 48kHz) are short-circuited with an HTTP 400 Bad Request to defend downstream compute resources.
2. **Resampling (SciPy):** Native 48kHz acoustic signals are dynamically downsampled to 100Hz using Fourier calculations to lower computational footprints.
3. **Bandpass Filtering (SciPy):** A 1st-order digital Butterworth filter cuts off out-of-band noise, isolating frequencies between 0.1Hz and 1.5Hz using forward-backward zero-phase filtering (`filtfilt`).
4. **Epoch Analytics:** Cleansed data is bucketed into 60-second windows where moving averages, percentile thresholding, and peak distances extract clean breath periods to generate localized BPM arrays.

---

## 🛠️ Tech Stack & Dependencies

* **Language:** Python 3.10
* **API Gateway:** FastAPI & Uvicorn (Asynchronous Python Web Server Framework)
* **Mathematical Operations:** NumPy, SciPy (Signal Processing Submodules)
* **Automation & Engine Execution:** Docker, GitHub Actions (CI/CD Workflows)
* **Testing Infrastructure:** Pytest, HTTPX, Starlette TestClient

---

## 🚀 Local Deployment Instructions

### Running Natively via Python Virtual Environment
1. Activate your local virtual environment:
   ```bash
   # Windows:
   .\myenv\Scripts\activate
   # Linux/WSL:
   source myenv/bin/activate
   ```
2. Run the automated testing suite to verify system health:
   ```bash
   python -m pytest tests/ --disable-warnings
   ```
3. Boot the local server session:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Explore the interactive documentation layout via: `http://127.0.0`

### Running via Isolated Docker Container
1. Compile the production container snapshot:
   ```bash
   docker build -t biosignal-api:latest .
   ```
2. Deploy the isolated container layer locally:
   ```bash
   docker run -p 8080:8080 biosignal-api:latest
   ```
3. Send a ping to verify container health: `http://localhost:8080/health`

---

## 🔄 CI/CD Automation Matrix
This system includes an integrated GitHub Actions pipeline (`.github/workflows/ci-pipeline.yml`). Upon every push or pull request to the `main` branch, the cloud server automatically:
* Lints and validates dependencies code.
* Executes structural unit tests and integration tests via `pytest`.
* Verifies container isolation by compiling a unique Docker build.

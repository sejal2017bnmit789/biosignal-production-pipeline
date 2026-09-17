import pytest
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.utils import resample_signal, bandpass_filter, calculate_breathing_rate

# Initialize the FastAPI TestClient
client = TestClient(app)

# ==========================================
# 1. ALGORITHM & MATH UNIT TESTS (utils.py)
# ==========================================

def test_resample_signal_dimensions():
    """
    Test that resampling a 48kHz signal correctly 
    downsamples it to 100Hz while retaining shape attributes.
    """
    # Create 2 seconds of mock audio signal at 48000 Hz sample rate
    original_sr = 48000
    duration_seconds = 2
    mock_signal = np.sin(2 * np.pi * 10 * np.linspace(0, duration_seconds, original_sr * duration_seconds))
    
    downsampled_audio, target_sr = resample_signal(mock_signal)
    
    assert target_sr == 100
    # 2 seconds at 100Hz should equal exactly 200 samples
    assert len(downsampled_audio) == 200


def test_bandpass_filter_execution():
    """
    Ensures that the bandpass filter successfully processes arrays
    without crashing or altering the data dimensions.
    """
    sr = 100
    mock_audio = np.random.normal(0, 1, 500) # 5 seconds of mock data
    
    filtered_audio = bandpass_filter(mock_audio, sr)
    
    assert len(filtered_audio) == len(mock_audio)
    assert isinstance(filtered_audio, np.ndarray)


def test_calculate_breathing_rate_zero_edgecase():
    """
    Tests edge cases like completely flat arrays (no breathing detected).
    The algorithm should handle this smoothly and return 0 instead of throwing an error.
    """
    sr = 100
    flat_signal = np.zeros(6000) # 60 seconds (1 epoch) of absolute silence
    
    rates = calculate_breathing_rate(flat_signal, sr)
    
    assert len(rates) == 1
    assert rates[0] == 0


# ==========================================
# 2. API INTEGRATION TESTS (main.py)
# ==========================================

def test_api_health_endpoint():
    """
    Ensures the health endpoint works properly. 
    Crucial for GCP Cloud Run health checks.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_api_analyze_breathing_rate_success():
    """
    Simulates a successful client HTTP POST request hitting the /analyze-breathing-rate route.
    """
    # 1 second of mock data (48,000 points) to fulfill minimum endpoint restrictions
    mock_payload_signal = np.random.normal(0, 1, 48000).tolist()
    
    response = client.post(
        "/analyze-breathing-rate",
        json={"signal": mock_payload_signal}
    )
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "calculated_rates_bpm" in response.json()


def test_api_analyze_breathing_rate_too_short_validation():
    """
    Validates that the API correctly rejects payloads that don't have enough data
    with an HTTP 400 Bad Request error.
    """
    short_signal = [0.1, 0.2, 0.3] # Way too short for 48kHz calculations
    
    response = client.post(
        "/analyze-breathing-rate",
        json={"signal": short_signal}
    )
    
    # Asserting standard HTTP 400 Bad Request
    assert response.status_code == 400 
    assert "Signal length is too short" in response.json()["detail"]

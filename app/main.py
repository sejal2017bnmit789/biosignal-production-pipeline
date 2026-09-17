from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from app.utils import process_pipeline_from_array

app = FastAPI(
    title="Biosignal Signal Processing Pipeline API",
    description="Clean, production-decoupled API handling breathing rate transformations.",
    version="1.1.0"
)

class AudioSignalPayload(BaseModel):
    signal: list[float] = Field(..., description="Raw audio signal array data (48kHz sampling expected).")

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}

@app.post("/analyze-breathing-rate", status_code=status.HTTP_200_OK)
async def analyze_breathing(payload: AudioSignalPayload):
    try:
        # --- ENTERPRISE FIX ---
        # If data is shorter than 1 second (48000 points), fail with a clean 400 Bad Request
        if len(payload.signal) < 48000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signal length is too short to accurately parse breathing windows."
            )
            
        calculated_rates = process_pipeline_from_array(payload.signal)
        
        return {
            "success": True,
            "calculated_rates_bpm": calculated_rates,
            "epochs_processed": len(calculated_rates)
        }
        
    except HTTPException as http_err:
        # Re-raise explicit HTTP exceptions so FastAPI returns the correct status code (e.g. 400)
        raise http_err
    except Exception as e:
        # Catch unexpected math/runtime failures as a 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline processing execution broken: {str(e)}"
        )

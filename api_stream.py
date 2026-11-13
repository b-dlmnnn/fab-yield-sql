from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Fab Unified Telemetry & Cross-Validation API")

class WaferEvent(BaseModel):
    wafer_id: str
    tool_id: str
    sensor_risk_score: float   # SiliconGuard AI ciktisi (0.0 - 1.0)
    vision_defect_count: int   # Vision Inspector kamera kusur sayisi

@app.post("/ingest-telemetry")
def evaluate_wafer_stream(event: WaferEvent):
    """
    SiliconGuard AI (sensor) ve Vision Inspector (kamera) sinyallerini
    gercek zamanli capraz dogrulamaya sokar ve anlik hat karari uretir.
    """
    high_sensor = event.sensor_risk_score >= 0.65
    high_vision = event.vision_defect_count > 0

    if high_sensor and high_vision:
        action = "CRITICAL_HALT_AND_QUARANTINE"
        reason = "Confirmed Dual-Modal Failure (Sensor + Optical Defect)"
    elif high_sensor or high_vision:
        action = "SECONDARY_INSPECTION_FLAG"
        reason = "Single-Modal Anomaly Detected (Cross-Check Required)"
    else:
        action = "PASS_TO_NEXT_STAGE"
        reason = "Nominal Sensor & Optical Telemetry"

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "wafer_id": event.wafer_id,
        "tool_id": event.tool_id,
        "decision": action,
        "root_cause": reason
    }

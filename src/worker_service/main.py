import os
from datetime import datetime, timezone
from typing import Dict, List

from fastapi import FastAPI
from pydantic import BaseModel, Field

SERVICE_NAME = os.getenv("SERVICE_NAME", "notification-sender-worker")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")

app = FastAPI(
    title="FIT4110 Lab 05 - Notification Sender Worker",
    version=SERVICE_VERSION,
    description="Mock worker that represents email/SMS/push providers for Notification Service.",
)


class SendRequest(BaseModel):
    notification_id: str
    channels: List[str] = Field(default_factory=list)
    message: str


@app.get("/health")
def health() -> Dict:
    return {"status": "ok", "service": SERVICE_NAME, "version": SERVICE_VERSION}


@app.post("/send")
def send(payload: SendRequest) -> Dict:
    sent_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "notification_id": payload.notification_id,
        "status": "sent",
        "sent_at": sent_at,
        "attempts": [
            {"channel": channel, "status": "sent", "provider_message_id": f"mock-{channel}-{payload.notification_id}"}
            for channel in payload.channels
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

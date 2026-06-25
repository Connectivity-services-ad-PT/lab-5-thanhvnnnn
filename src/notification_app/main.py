import os
from datetime import datetime, timezone
from enum import Enum
from http import HTTPStatus
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator

SERVICE_NAME = os.getenv("SERVICE_NAME", "notification")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")

app = FastAPI(
    title="FIT4110 - Notification Service",
    version=SERVICE_VERSION,
    description="Smart Campus Notification Service for Core Business alert events.",
)


class NotificationChannel(str, Enum):
    email = "email"
    sms = "sms"
    push = "push"
    in_app = "in_app"


class NotificationPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"


class NotificationStatus(str, Enum):
    queued = "queued"
    sent = "sent"
    failed = "failed"
    duplicate = "duplicate"


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int = Field(..., ge=400, le=599)
    detail: str
    instance: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    dependencies: Dict[str, str] = Field(default_factory=dict)


class DeliveryTarget(BaseModel):
    kind: str = Field(..., examples=["user"])
    user_id: Optional[str] = Field(default=None, examples=["staff-security-01"])
    email: Optional[str] = Field(default=None, examples=["security@example.edu.vn"])
    phone: Optional[str] = Field(default=None, examples=["+84901234567"])
    device_token: Optional[str] = Field(default=None, examples=["fcm-token-demo-001"])

    @model_validator(mode="after")
    def validate_target(self):
        if self.kind == "user" and not self.user_id:
            raise ValueError("target.user_id is required when kind=user")
        if self.kind == "email" and not self.email:
            raise ValueError("target.email is required when kind=email")
        if self.kind == "phone" and not self.phone:
            raise ValueError("target.phone is required when kind=phone")
        if self.kind == "device" and not self.device_token:
            raise ValueError("target.device_token is required when kind=device")
        if self.kind not in {"user", "email", "phone", "device"}:
            raise ValueError("target.kind must be one of user, email, phone, device")
        return self


class NotificationCreate(BaseModel):
    alert_id: str = Field(..., pattern=r"^ALERT-[A-Za-z0-9\-]+$", examples=["ALERT-20260617-0001"])
    target: DeliveryTarget
    channels: List[NotificationChannel] = Field(..., min_length=1, examples=[["push", "sms", "email"]])
    priority: NotificationPriority = Field(..., examples=["critical"])
    title: str = Field(..., min_length=3, max_length=120)
    message: str = Field(..., min_length=5, max_length=1000)
    dedupe_key: Optional[str] = Field(default=None, min_length=8, max_length=160)
    template_code: Optional[str] = Field(default=None, pattern=r"^[a-z0-9_\-]{3,60}$")
    metadata: Dict = Field(default_factory=dict)

    @field_validator("channels")
    @classmethod
    def unique_channels(cls, channels: List[NotificationChannel]):
        if len(set(channels)) != len(channels):
            raise ValueError("channels must be unique")
        return channels


class NotificationAccepted(BaseModel):
    notification_id: str
    alert_id: str
    status: NotificationStatus
    accepted_channels: List[NotificationChannel]
    dedupe_key: Optional[str] = None
    queued_at: str
    trace_id: Optional[str] = None


class RetryAccepted(BaseModel):
    notification_id: str
    retry_count: int
    status: NotificationStatus
    queued_at: str


NOTIFICATIONS: Dict[str, Dict] = {}
DEDUPE_INDEX: Dict[str, str] = {}
RETRY_COUNT: Dict[str, int] = {}
TEMPLATES: Dict[str, Dict] = {
    "security_motion_v1": {
        "template_code": "security_motion_v1",
        "channels": ["push", "sms", "email"],
        "locale": "vi-VN",
        "subject_template": "[Smart Campus] {{title}}",
        "body_template": "{{message}}",
        "active": True,
    },
    "sensor_high_temperature_v1": {
        "template_code": "sensor_high_temperature_v1",
        "channels": ["email", "push"],
        "locale": "vi-VN",
        "subject_template": "[Smart Campus] Cảnh báo cảm biến",
        "body_template": "{{message}}",
        "active": True,
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def next_notification_id() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"NTF-{today}-{len(NOTIFICATIONS) + 1:04d}"


def recipient_id(target: DeliveryTarget) -> Optional[str]:
    return target.user_id or target.email or target.phone or target.device_token


def build_problem(status_code: int, title: str, detail: str, instance: Optional[str] = None, problem_type: str = "about:blank") -> Dict:
    data = {"type": problem_type, "title": title, "status": status_code, "detail": detail}
    if instance:
        data["instance"] = instance
    return data


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        problem = exc.detail
    else:
        try:
            title = HTTPStatus(exc.status_code).phrase
        except ValueError:
            title = "HTTP Error"
        problem = build_problem(exc.status_code, title, str(exc.detail), str(request.url.path))
    problem.setdefault("instance", str(request.url.path))
    return JSONResponse(status_code=exc.status_code, content=problem, media_type="application/problem+json", headers=getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(item) for item in first_error.get("loc", []))
    message = first_error.get("msg", "Request validation error")
    detail = f"{location}: {message}" if location else message
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_problem(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Validation error",
            detail,
            str(request.url.path),
            "https://smart-campus.local/problems/validation-error",
        ),
        media_type="application/problem+json",
    )


def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> None:
    expected = f"Bearer {AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status.HTTP_401_UNAUTHORIZED,
                "Unauthorized",
                "Missing or invalid bearer token",
                problem_type="https://smart-campus.local/problems/unauthorized",
            ),
        )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        dependencies={"queue": "ready", "sender": "ready", "db": "ready"},
    )


@app.post(
    "/notifications",
    response_model=NotificationAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_bearer_token)],
    responses={401: {"model": ProblemDetails}, 422: {"model": ProblemDetails}, 429: {"model": ProblemDetails}},
)
def create_notification(payload: NotificationCreate, response: Response, x_trace_id: Optional[str] = Header(default=None, alias="X-Trace-Id")) -> NotificationAccepted:
    if payload.dedupe_key and payload.dedupe_key in DEDUPE_INDEX:
        notification_id = DEDUPE_INDEX[payload.dedupe_key]
        item = NOTIFICATIONS[notification_id]
        response.status_code = status.HTTP_200_OK
        return NotificationAccepted(
            notification_id=notification_id,
            alert_id=item["alert_id"],
            status=NotificationStatus.duplicate,
            accepted_channels=item["channels"],
            dedupe_key=item.get("dedupe_key"),
            queued_at=item["created_at"],
            trace_id=x_trace_id,
        )

    notification_id = next_notification_id()
    created_at = now_iso()
    channels = [channel.value for channel in payload.channels]
    item = {
        "notification_id": notification_id,
        "alert_id": payload.alert_id,
        "status": NotificationStatus.queued.value,
        "channels": channels,
        "priority": payload.priority.value,
        "recipient_id": recipient_id(payload.target),
        "target": payload.target.model_dump(exclude_none=True),
        "title": payload.title,
        "message": payload.message,
        "dedupe_key": payload.dedupe_key,
        "template_code": payload.template_code,
        "metadata": payload.metadata,
        "created_at": created_at,
        "attempts": [
            {"channel": channel, "status": "queued", "attempted_at": created_at, "provider_message_id": None, "error": None}
            for channel in channels
        ],
    }
    NOTIFICATIONS[notification_id] = item
    if payload.dedupe_key:
        DEDUPE_INDEX[payload.dedupe_key] = notification_id

    return NotificationAccepted(
        notification_id=notification_id,
        alert_id=payload.alert_id,
        status=NotificationStatus.queued,
        accepted_channels=payload.channels,
        dedupe_key=payload.dedupe_key,
        queued_at=created_at,
        trace_id=x_trace_id,
    )


@app.get("/notifications", dependencies=[Depends(verify_bearer_token)])
def list_notifications(
    recipient_id: Optional[str] = Query(default=None, min_length=3),
    status_filter: Optional[NotificationStatus] = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
) -> Dict[str, List[Dict]]:
    items = list(NOTIFICATIONS.values())
    if recipient_id:
        items = [item for item in items if item.get("recipient_id") == recipient_id]
    if status_filter:
        items = [item for item in items if item.get("status") == status_filter.value]
    summaries = [
        {
            "notification_id": item["notification_id"],
            "alert_id": item["alert_id"],
            "status": item["status"],
            "channels": item["channels"],
            "priority": item["priority"],
            "recipient_id": item.get("recipient_id"),
            "created_at": item["created_at"],
        }
        for item in items[-limit:]
    ]
    return {"items": summaries}


@app.get("/notifications/{notification_id}", dependencies=[Depends(verify_bearer_token)])
def get_notification(notification_id: str) -> Dict:
    if notification_id not in NOTIFICATIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=build_problem(
                status.HTTP_404_NOT_FOUND,
                "Not found",
                f"Notification {notification_id} does not exist",
                problem_type="https://smart-campus.local/problems/not-found",
            ),
        )
    return NOTIFICATIONS[notification_id]


@app.post("/notifications/{notification_id}/retry", response_model=RetryAccepted, status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(verify_bearer_token)])
def retry_notification(notification_id: str) -> RetryAccepted:
    if notification_id not in NOTIFICATIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=build_problem(status.HTTP_404_NOT_FOUND, "Not found", f"Notification {notification_id} does not exist"),
        )
    item = NOTIFICATIONS[notification_id]
    if item["status"] == NotificationStatus.sent.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=build_problem(status.HTTP_409_CONFLICT, "Conflict", "Notification is already sent and cannot be retried"),
        )
    retry_count = RETRY_COUNT.get(notification_id, 0) + 1
    RETRY_COUNT[notification_id] = retry_count
    item["status"] = NotificationStatus.queued.value
    queued_at = now_iso()
    item["attempts"].append({"channel": "in_app", "status": "queued", "attempted_at": queued_at, "provider_message_id": None, "error": None})
    return RetryAccepted(notification_id=notification_id, retry_count=retry_count, status=NotificationStatus.queued, queued_at=queued_at)


@app.get("/templates/{template_code}", dependencies=[Depends(verify_bearer_token)])
def get_template(template_code: str) -> Dict:
    if template_code not in TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=build_problem(status.HTTP_404_NOT_FOUND, "Not found", f"Template {template_code} does not exist"),
        )
    return TEMPLATES[template_code]


@app.get("/core-alerts/{alert_id}")
def get_core_alert_mock(alert_id: str) -> Dict:
    return {
        "alert_id": alert_id,
        "severity": "critical",
        "source_service": "core-business",
        "policy_id": "POLICY-AFTER-HOURS",
        "message": "Motion detected after hours",
        "occurred_at": "2026-06-17T21:00:00+07:00",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("APP_HOST", "0.0.0.0"), port=int(os.getenv("APP_PORT", "8000")))

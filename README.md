# FIT4110 Lab 05 - Docker Compose Readiness cho Notification Service

## 1. Service của nhóm

- Service: **Notification Service** (`team-notify`)
- Vai trò: nhận alert từ Core Business và gửi thông báo đa kênh
- Cơ chế: Queue async, trong lab mô phỏng bằng API + sender worker + database

## 2. Stack Docker Compose

```text
api             Notification FastAPI service, publish port 8000
sender-worker   Worker mock đại diện email/SMS/push gateway, publish port 9000
db              PostgreSQL lưu trạng thái/log notification
team-internal   Network nội bộ
class-net       Network để sẵn sàng nối nhóm khác
```

## 3. Endpoint demo

| Method | Endpoint | Ghi chú |
|---|---|---|
| GET | `/health` | Không cần token, dùng để partner test |
| POST | `/notifications` | Cần `Authorization: Bearer local-dev-token` |
| GET | `/notifications` | Xem danh sách |
| GET | `/notifications/{notification_id}` | Xem chi tiết |
| POST | `/notifications/{notification_id}/retry` | Retry |
| GET | `/templates/{template_code}` | Template |

## 4. Chạy stack

```bash
cp .env.example .env
docker compose up -d --build --wait
```

Kiểm tra:

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:9000/health
```

## 5. Chạy test

```bash
npm install
npm run test:compose
```

## 6. Evidence cần có

- `docker compose ps`.
- Screenshot `GET /health` local.
- Screenshot partner gọi `/health` qua IP lớp.
- Log `docker compose logs api`.
- Newman report trong `reports/`.
- Checklist readiness đã tick tối thiểu 6 mục.

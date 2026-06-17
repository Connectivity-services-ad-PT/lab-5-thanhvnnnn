# Readiness Checklist - Lab 05 Notification

- [x] API container chạy bằng Docker Compose.
- [x] Database PostgreSQL có healthcheck `pg_isready`.
- [x] Sender worker có `/health` ở port 9000.
- [x] API có `/health` ở port 8000.
- [x] API phụ thuộc DB và worker bằng `depends_on: condition: service_healthy`.
- [x] Có `.env.example`, không commit secret thật.
- [x] Có network `team-internal` cho giao tiếp nội bộ.
- [x] Có network `class-net` để sẵn sàng nối nhóm khác.
- [x] Có Postman/Newman collection cho test compose.
- [x] Có hướng dẫn chạy trong `RUN_COMPOSE.md`.
- [ ] Đã chạy `docker compose ps` và lưu screenshot thật.
- [ ] Đã test partner gọi `/health` qua IP lớp.

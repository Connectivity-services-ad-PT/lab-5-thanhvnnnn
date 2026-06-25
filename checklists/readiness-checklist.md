# Readiness Checklist - Lab 05 Notification

- [x] API container runs with Docker Compose.
- [x] PostgreSQL database has `pg_isready` healthcheck.
- [x] Sender worker exposes `/health` on port `9000`.
- [x] API exposes `/health` on container port `8000`.
- [x] API depends on DB and worker with `depends_on: condition: service_healthy`.
- [x] `.env.example` exists and does not contain real secrets.
- [x] `team-internal` network exists for internal service traffic.
- [x] `class-net` network exists for partner-group testing.
- [x] Postman/Newman collection exists for Compose testing.
- [x] `RUN_COMPOSE.md` explains how to run the stack.
- [x] Real `docker compose ps`, health and logs evidence saved in `reports/lab05-compose-evidence.md`.
- [x] Newman XML/HTML reports generated in `reports/`.
- [ ] Partner group has called `/health` through the real class network IP.

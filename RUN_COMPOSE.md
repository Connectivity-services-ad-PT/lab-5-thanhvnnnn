# Run Compose - Lab 05 Notification

## 1. Prepare `.env`

```bash
cp .env.example .env
```

If host port `8000` is already used, keep `APP_PORT=8000` and change only
`HOST_PORT`, for example:

```bash
HOST_PORT=8015
```

## 2. Build and start the stack

```bash
docker compose up -d --build --wait
```

The stack contains:

- `api`: Notification API on container port `8000`.
- `sender-worker`: mock sender worker on port `9000`.
- `db`: PostgreSQL with `pg_isready` healthcheck.
- `team-internal`: private network for internal calls.
- `class-net`: network prepared for partner groups.

## 3. Check containers

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:9000/health
```

If you changed `HOST_PORT`, use that port for the API health check.

## 4. Run Newman end-to-end tests

```bash
npm install
npm run test:compose
```

Reports are written to:

```text
reports/newman-lab05-compose.xml
reports/newman-lab05-compose.html
```

## 5. Stop the stack

```bash
docker compose down -v
```

## 6. Partner testing

Ask the other group to call:

```text
http://<your-machine-ip>:<HOST_PORT>/health
```

After `/health` works, they can test the protected `/notifications` endpoint
with `Authorization: Bearer local-dev-token`.

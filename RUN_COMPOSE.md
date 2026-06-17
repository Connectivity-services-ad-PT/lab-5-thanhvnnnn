# RUN COMPOSE - Lab 05 Notification

## 1. Chuẩn bị `.env`

```bash
cp .env.example .env
```

## 2. Build và chạy stack

```bash
docker compose up -d --build --wait
```

## 3. Kiểm tra container

```bash
docker compose ps
curl http://localhost:8000/health
curl http://localhost:9000/health
```

## 4. Chạy Newman end-to-end

```bash
npm install
npm run test:compose
```

## 5. Dừng stack

```bash
docker compose down -v
```

## 6. Khi nối với nhóm khác trên mạng lớp

- Sửa `.env` nếu port/token thay đổi.
- Đảm bảo `APP_PORT=8000` được publish.
- Cho nhóm khác gọi `http://<IP-cua-may-ban>:8000/health` trước.
- Nếu gọi được `/health` rồi mới test `/notifications`.

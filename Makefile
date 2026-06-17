install:
	npm install

compose-up:
	cp -n .env.example .env || true
	docker compose up -d --build --wait

compose-down:
	docker compose down -v

ps:
	docker compose ps

logs:
	docker compose logs --tail=200

test-compose:
	npm run test:compose

.PHONY: setup run test down logs

# One-time: create .env and build images.
setup:
	cp -n .env.example .env || true
	docker compose build

# Start the stack (db + backend + frontend). Backend auto-migrates and loads stations.
run:
	docker compose up

# Run the backend test suite inside the container.
test:
	docker compose exec backend python manage.py test api

down:
	docker compose down

logs:
	docker compose logs -f

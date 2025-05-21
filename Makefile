start:
	docker-compose up --build

stop:
	docker-compose down

migrate:
	docker exec -it backend alembic upgrade head

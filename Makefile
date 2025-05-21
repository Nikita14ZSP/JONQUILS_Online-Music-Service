.PHONY: install-backend install-frontend run-backend run-frontend migrate

install-backend:
	pip install -r backend/requirements.txt

install-frontend:
	cd frontend && npm install

run-backend:
	cd backend && uvicorn main:app --reload

run-frontend:
	cd frontend && npm run dev

migrate:
	alembic upgrade head

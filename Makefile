PY ?= python3
PIP ?= pip3
PORT ?= 8001

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)

test:
	pytest -q

docker-build:
	docker build -t askadb/nl-query:local .

docker-run:
	docker run --rm -p $(PORT):$(PORT) --env-file ../askadb-infra/.env askadb/nl-query:local


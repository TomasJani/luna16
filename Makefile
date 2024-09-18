.PHONY: format lint precommit

.DEFAULT_GOAL := lint

format:
	ruff format luna16

lint: format
	ruff check luna16 --fix  --select I


mlflow-server:
	mlflow ui --port 8080 --backend-store-uri sqlite:///mlruns.db
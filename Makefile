.PHONY: all
all: ## Show the available make targets.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

.PHONY: clean
clean: ## Clean the temporary files.
	rm -rf .mypy_cache
	rm -rf .ruff_cache	

# Make does not like interpreting : in the target name, so we use a variable
API_CMD=poetry run uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload

run-api: ## Run the API
	$(API_CMD)

run-docs: ## Run the mkdocs
	poetry run mkdocs serve

check-python: ## Format the python code (auto fix)
	poetry run isort . --verbose
	poetry run black .
	poetry run ruff check . --fix
	poetry run mypy --follow-untyped-imports  . 
	poetry run pylint --verbose .
	poetry run bandit .

check-python-nofix: ## Format the python code (no fix)
	poetry run isort . --check --verbose
	poetry run black . --check
	poetry run ruff check .
	poetry run mypy --follow-untyped-imports  . 
	poetry run pylint --verbose .
	poetry run bandit .

black: ## Run black
	poetry run black .

unit-tests: ## Run the example unit tests
	poetry run pytest -m utils --cov=utils --cov-report=term-missing --cov-fail-under=80 --cov-config=.coveragerc

api-tests: ## Run the example API tests
	poetry run pytest -m api --cov=api --cov-report=term-missing --cov-fail-under=80 --cov-config=.coveragerc

all-tests:
	poetry run pytest  --cov=. --cov-report=term-missing --cov-fail-under=80 --cov-config=.coveragerc
	
install: ## Install the dependencies
	poetry install --only main --no-root

install-dev: ## Install the dev dependencies
	poetry install --no-root

.PHONY: colima-start
colima-start: ## Start Colima
	colima start --cpu 2 --memory 4 --disk 100

.PHONY: colima-stop
colima-stop: ## Stop Colima
	colima stop

.PHONY: docker-build
docker-build: ## Build the Docker image
	#UPDATE#DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock" docker build -t ai-assist-builder .

.PHONY: docker-run
docker-run: ## Run the Docker container
	#UPDATE#DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock" docker run \
		-p 8000:8000 \
		-e FLASK_SECRET_KEY=FLASK_SECRET_KEY \
		-e FLASK_ENV=production \
		ai-assist-builder

.PHONY: docker-clean
docker-clean: ## Clean Docker resources
	DOCKER_HOST="unix://${HOME}/.colima/default/docker.sock" docker system prune -f

.PHONY: colima-status
colima-status: ## Check Colima status
	colima status

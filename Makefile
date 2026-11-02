.PHONY: setup format format-check lint typecheck test docs-check secret-scan audit security check

UV_RUN = uv run --all-packages

setup:
	uv sync --all-packages --locked
	$(UV_RUN) pre-commit install

format:
	$(UV_RUN) ruff format .

format-check:
	$(UV_RUN) ruff format --check .

lint:
	$(UV_RUN) ruff check .

typecheck:
	$(UV_RUN) mypy

test:
	$(UV_RUN) pytest --cov=rag_core --cov=indonesian_labor_regulations --cov=tools --cov-report=term-missing --cov-fail-under=70

docs-check:
	$(UV_RUN) python tools/check_docs.py

secret-scan:
	$(UV_RUN) detect-secrets-hook --baseline .secrets.baseline $$(git ls-files -co --exclude-standard ':!.secrets.baseline')

audit:
	$(UV_RUN) pip-audit --skip-editable

security: secret-scan audit

check: format-check lint typecheck test docs-check security

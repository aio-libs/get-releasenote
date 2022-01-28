install:
	pip install -r requirements.txt
	pip install -e .
	pre-commit install

lint:
# CI env-var is set by GitHub actions
ifdef CI
	python -m pre_commit run --all-files --show-diff-on-failure
else
	python -m pre_commit run --all-files
endif
	python -m mypy  --show-error-codes --strict get_releasenote.py tests


test:
	python -m pytest tests

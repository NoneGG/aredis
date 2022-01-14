lint:
	black --check
	#mypy coredis
	flake8 coredis tests

lint-fix:
	black tests coredis
	#mypy coredis
	isort -r --profile=black tests coredis
	autoflake8 -i -r tests coredis

generate-compatibility-docs:
	rm -rf docs/source/compatibility.rst
	python scripts/command_coverage.py > docs/source/compatibility.rst

lint:
	black --check coredis tests
	#mypy coredis
	flake8 coredis tests

lint-fix:
	black coredis tests
	#mypy coredis
	isort -r --profile=black tests coredis
	autoflake8 -i -r tests coredis

generate-compatibility-docs:
	rm -rf docs/source/compatibility.rst
	python scripts/command_coverage.py > docs/source/compatibility.rst

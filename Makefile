PYTHON := python3

.PHONY = test run
.DEFAULT_GOAL = prod

test:
	@echo "Running tests..."
	@${PYTHON} -m pytest -q -x --ff tests

dev: test
	@${PYTHON} bot.py

prod: test
	@${PYTHON} -O bot.py

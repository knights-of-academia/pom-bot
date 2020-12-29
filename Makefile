PYTHON := python3

.PHONY = test run
.DEFAULT_GOAL = prod

lint:
	@echo "Linting..."
	@${PYTHON} -m pylint \
		bot.py \
		pombot/*.py \
		pombot/**/*.py \
		tests/*.py

test:
	@echo "Testing..."
	@${PYTHON} -m pytest -x --ff tests

dev: lint test
	@echo "Launching..."

	@# Run without optimization. Python's -O will set __debug__ to False and
	@# apply production protections. On a development machine, it should be
	@# possible to, say, delete all tables on startup.
	@${PYTHON} bot.py

prod: lint test
	@echo "Launching..."

	@# Use a single -O here because, with -OO, Python will remove docstrings
	@# which discord.py relies on for !help messages.
	@${PYTHON} -O bot.py

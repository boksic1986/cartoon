.PHONY: install test run-all clean

install:
	pip install -e ".[dev]"

test:
	pytest

run-all:
	idiom-video run-all data/idioms/shou-zhu-dai-tu.json --providers mock

clean:
	python -c "import shutil, pathlib; p=pathlib.Path('outputs'); shutil.rmtree(p) if p.exists() else None"


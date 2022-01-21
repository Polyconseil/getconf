# Don't call it "docs" otherwise Makefile confuses it with the "docs/" directory.
doc:
	SPHINXOPTS=-W $(MAKE) -C docs html

release:
	fullrelease

test:
	pytest

update:
	pip install -r requirements_dev.txt

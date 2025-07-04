.PHONY: run clean

run:
	python3 pulse.py

clean:
	find . -name "*.pyc" -delete

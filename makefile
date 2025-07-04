.PHONY: run clean

run:
	python3 pulse/pulse.py

clean:
	find . -name "*.pyc" -delete

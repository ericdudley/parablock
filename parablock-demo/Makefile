.PHONY: process run test

process:
	poetry run python -m parablock.processor --package demo

process-watch:
	poetry run python -m parablock.processor --package demo --watch

run:
	poetry run python -m demo.main

setup:
	poetry install

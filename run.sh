#! /usr/bin/env bash

poetry run poe codegen
poetry run python src/main.py
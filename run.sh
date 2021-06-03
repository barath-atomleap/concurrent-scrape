#! /usr/bin/env bash

poetry install
poetry run poe codegen
poetry run poe start
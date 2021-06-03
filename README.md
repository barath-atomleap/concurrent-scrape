# Concurrent scraping

The `main.py` contains all the required code.
The task is to scrape 14000 news articles as quickly as possible. The data is in the `.data` folder.

# Usage

  1. Run `poetry install`
  2. Run `poetry run poe codegen`
  3. Run `poetry run poe start`

  Or you can just run `./run.sh`

# Results
The results are stored in the `./.data/scraped` directory. Errors are logged in `./.data/errors.json`
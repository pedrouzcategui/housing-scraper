# Housing Scraper

This is a simple python scraper that scrapes apartments from MercadoLibre.com.ve, stores some fields (such as apartment slug, apartment price) of the information in a SQLite file, and offers average price information per state and city down to the squared foot of land, said apartments over time are categorized as "hot deal", "new", "above market price". It categorizes them by "apartment", "house", or "studio".

There is an A.I summary generated that is offered to the users that categorizes the apartment as good deals or not.

This app sends notifications when there are price changes and it tracks the evolution of each of the apartments, sold apartments are disabled from the system.

## Technologies Used

- Python 3.10
- Playwright
- SQLite
- FastAPI
- UV package manager

#### Notes:

- I am using `uv` as a python package manager, so commands must be run with `uv run`, and installed with `uv add`.

#### RUNNING IN DEBUG MODE:

If you want to run the program in DEBUG mode, use this:

```powershell
$env:PWDEBUG=1; uv run main.py
```

In debug mode the app will recreate the SQLite table on startup and re-raise scrape exceptions after logging.

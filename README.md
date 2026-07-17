# Steam Store Scraper

A pure web-scraping tool (no Steam Web API used) that lets you filter Steam store
listings by tag and price, and view results either in the terminal or in a simple
Tkinter GUI.

Prices are pulled from Steam's Indian store region (`cc=in`), so results are shown
in INR (₹).

## Files

- `steam_scraper.py` — Tkinter GUI version. Scrapes Steam's search results filtered
  by tag and price, with checkboxes for tags, an entry field for max price, and a
  results table you can double-click to open a game's Steam page.
- `requirements.txt` — Python package dependencies.

## Requirements

- Python 3.8+
- Tkinter (only needed for the GUI version) — ships with most standard Python
  installs. On some Linux distros you may need to install it separately, e.g.:
  ```bash
  sudo apt install python3-tk
  ```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python steam_scraper.py
```

1. Check the tags you want to filter by.
2. Enter a max price (INR) and number of pages to scrape.
3. Click **Scrape**.
4. Double-click any result row to open that game's Steam store page in your browser.
5. Click **Save to CSV** to export the results.

## Notes

- **Rate limiting**: the script waits 1.5 seconds between page requests to avoid
  being blocked by Steam. Please don't remove this delay.
- **Tag IDs**: Steam occasionally changes its internal tag ID numbers. If a tag
  filter stops returning expected results, check the tag's current ID by selecting
  it on the live Steam search page and inspecting the resulting URL's `tags=`
  parameter.
- **Region pricing**: prices depend on Steam's detected region for the `cc=in`
  parameter. Occasional formatting differences (e.g. games with decimal prices vs.
  whole prices) are handled by the price-parsing logic, but edge cases may still
  slip through.
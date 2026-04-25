# visa-info

Interactive world map of visa requirements for **Indian passport holders**, with a "visa unlock" feature that highlights additional destinations made accessible by holding visas from major countries (US, Schengen, UK, UAE, Canada, Japan, Australia, New Zealand).

## What's in this repo

| File | Purpose |
| --- | --- |
| `index.html` | Self-contained single-page app. Renders a D3 world map with countries colour-coded by visa category, plus a sidebar of grouped country lists, dark/light theme, and toggle chips for "what other visas do you hold?" |
| `fetch_visa_data.py` | Builds the two JSON data files. Downloads the [Passport Index dataset](https://github.com/ilyankou/passport-index-dataset), filters for Indian passport, normalises categories, and merges in a curated visa-unlock mapping. |
| `india_visa_requirements.json` | Per-country visa category for Indian passport holders. Five categories: `VISA_FREE`, `VISA_ON_ARRIVAL`, `E_VISA`, `VISA_REQUIRED`, `NO_DATA`. |
| `visa_unlock_mapping.json` | For each "key visa" (e.g. `US_VISA`, `SCHENGEN_VISA`), the list of countries that grant additional access to Indian passport holders, with stay duration and notes. |

## Categories

- **VISA_FREE** — entry on passport alone
- **VISA_ON_ARRIVAL** — visa issued at the port of entry
- **E_VISA** — electronic visa / ETA applied online before travel
- **VISA_REQUIRED** — must apply at an embassy/consulate in advance
- **NO_DATA** — no reliable data, not applicable, or no admission

## Running the app

`index.html` is fully static and pulls D3 + topojson from a CDN. Open it directly:

```bash
open index.html
```

…or serve the directory if your browser blocks local `fetch` for the JSON files:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000/
```

## Regenerating the data

```bash
python3 fetch_visa_data.py
```

This re-downloads the upstream CSV, rebuilds `india_visa_requirements.json`, and rewrites `visa_unlock_mapping.json` from the curated tables embedded in the script. No external Python dependencies required (stdlib only).

## Data sources

- Base visa requirements: [ilyankou/passport-index-dataset](https://github.com/ilyankou/passport-index-dataset), which aggregates official government sources via passportindex.org.
- Visa-unlock mapping: curated from passportindiaguide.com, atlys.com, india-evisa.it.com, visahq.com, UAE MOFA (Feb 2025), Singapore ICA, Taiwan BOCA, and joinsherpa.com.

## Caveat

Visa rules change frequently. **Always verify with the destination country's official embassy or immigration site before booking travel.** The unlock mapping was last verified April 2026.

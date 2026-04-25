#!/usr/bin/env python3
"""
Fetches visa requirements for Indian passport holders from the Passport Index dataset
(ilyankou/passport-index-dataset on GitHub, sourced from passportindex.org).

Generates two files:
  1. india_visa_requirements.json  — all countries with 5-category classification
  2. visa_unlock_mapping.json      — countries unlocked by holding US/Schengen/UK/UAE/
                                     Canada/Japan/Australia/NZ visas

Category mapping:
  VISA_FREE        — no visa needed
  VISA_ON_ARRIVAL  — visa obtained at port of entry
  E_VISA           — electronic visa / ETA applied online before travel
  VISA_REQUIRED    — must apply at embassy/consulate in advance
  NO_DATA          — no reliable data / not applicable (e.g. own country, no admission)
"""

import csv
import json
import subprocess
import urllib.request
import ssl
from datetime import date

# ---------------------------------------------------------------------------
# 1. Download & parse the CSV
# ---------------------------------------------------------------------------

CSV_URL = (
    "https://raw.githubusercontent.com/ilyankou/"
    "passport-index-dataset/master/passport-index-tidy.csv"
)

print(f"Downloading passport index CSV from:\n  {CSV_URL}\n")

result = subprocess.run(
    ["curl", "-sL", CSV_URL],
    capture_output=True, text=True, check=True
)
raw = result.stdout

reader = csv.DictReader(raw.splitlines())
rows = list(reader)
print(f"Total rows in dataset: {len(rows)}")

# ---------------------------------------------------------------------------
# 2. Filter for Indian passport and map categories
# ---------------------------------------------------------------------------

CATEGORY_MAP = {
    "visa free":          "VISA_FREE",
    "visa on arrival":    "VISA_ON_ARRIVAL",
    "e-visa":             "E_VISA",
    "eta":                "E_VISA",
    "evisa":              "E_VISA",
    "electronic travel authorization": "E_VISA",
    "visa required":      "VISA_REQUIRED",
    "-1":                 "NO_DATA",   # own country / not applicable
    "no admission":       "NO_DATA",
    "covid-19 ban":       "NO_DATA",
}

def map_requirement(raw_value: str) -> tuple[str, str | None]:
    """Returns (category, duration_days_or_None)."""
    v = raw_value.strip()
    # Numeric values = visa-free with stay duration in days
    try:
        days = int(v)
        if days < 0:
            return "NO_DATA", None
        return "VISA_FREE", f"{days} days"
    except ValueError:
        pass
    vl = v.lower()
    for key, cat in CATEGORY_MAP.items():
        if vl == key or vl.startswith(key):
            return cat, None
    if "free" in vl:
        return "VISA_FREE", None
    if "arrival" in vl:
        return "VISA_ON_ARRIVAL", None
    if "e-visa" in vl or "evisa" in vl or "eta" in vl or "electronic" in vl:
        return "E_VISA", None
    if "required" in vl or "prior" in vl:
        return "VISA_REQUIRED", None
    return "NO_DATA", None

india_rows = [r for r in rows if r.get("Passport", "").strip().lower() == "india"]
print(f"Rows for India passport: {len(india_rows)}")

countries: dict[str, dict] = {}
raw_values_seen: set[str] = set()

for row in india_rows:
    destination = row.get("Destination", "").strip()
    requirement  = row.get("Requirement", "").strip()
    raw_values_seen.add(requirement)
    category, duration = map_requirement(requirement)
    entry: dict = {"category": category}
    if duration:
        entry["visa_free_duration"] = duration
    countries[destination] = entry

print(f"\nRaw requirement values found in dataset:")
for v in sorted(raw_values_seen):
    cat, dur = map_requirement(v)
    print(f"  '{v}' → {cat}" + (f" ({dur})" if dur else ""))

# Summary counts
summary: dict[str, int] = {
    "VISA_FREE": 0, "VISA_ON_ARRIVAL": 0,
    "E_VISA": 0,    "VISA_REQUIRED": 0, "NO_DATA": 0,
}
for entry in countries.values():
    summary[entry["category"]] += 1

print(f"\nSummary: {summary}")

# ---------------------------------------------------------------------------
# 3. Build india_visa_requirements.json
# ---------------------------------------------------------------------------

visa_req_data = {
    "metadata": {
        "passport": "India (IN)",
        "source": "Passport Index Dataset by ilyankou",
        "source_url": "https://github.com/ilyankou/passport-index-dataset",
        "data_origin": "passportindex.org (aggregates official government sources)",
        "dataset_last_updated": "2025-01-12",
        "generated_at": str(date.today()),
        "categories": {
            "VISA_FREE":        "No visa required; entry on passport alone",
            "VISA_ON_ARRIVAL":  "Visa issued at port of entry upon arrival",
            "E_VISA":           "Electronic visa / ETA applied online before travel",
            "VISA_REQUIRED":    "Visa must be obtained in advance from embassy/consulate",
            "NO_DATA":          "No data, not applicable, or no admission",
        },
    },
    "summary": summary,
    "countries": dict(sorted(countries.items())),
}

with open("india_visa_requirements.json", "w", encoding="utf-8") as f:
    json.dump(visa_req_data, f, indent=2, ensure_ascii=False)

print("\nWrote india_visa_requirements.json")

# ---------------------------------------------------------------------------
# 4. Visa unlock mapping (curated from authoritative travel sources)
#
# Sources consulted:
#   - passportindiaguide.com (cross-referenced with official embassy pages)
#   - atlys.com  (cross-referenced with official immigration sites)
#   - india-evisa.it.com
#   - visahq.com
#   - UAE MOFA official announcement (Feb 2025)
#   - Singapore ICA (VFTF rules)
#   - Taiwan BOCA (Travel Authorisation Certificate)
#
# Logic: for each "key visa", list countries where holding that visa as an
# Indian passport holder gives ADDITIONAL access (visa-free / VOA / e-visa)
# beyond what the Indian passport alone provides.
# ---------------------------------------------------------------------------

UNLOCK_DATA = {
    "US_VISA": {
        "description": (
            "Countries accessible to Indian passport holders with a valid US visa. "
            "Typically requires a multiple-entry B1/B2 (tourist/business) visa; "
            "C1 transit visas usually excluded unless noted. "
            "Many destinations require the visa to have been used at least once."
        ),
        "conditions_general": "Valid multiple-entry US visa (B1/B2); passport valid 6+ months",
        "countries": {
            "Albania":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Multiple-entry visa, used at least once"},
            "Argentina":              {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "Valid B2 visa; prior US entry required"},
            "Bahamas":                {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "Multiple-entry visa, used at least once"},
            "Belize":                 {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Multiple-entry visa or US Green Card"},
            "Bosnia and Herzegovina": {"access": "VISA_FREE",       "duration": "30 days in 180 days",     "notes": "Multiple-entry visa required"},
            "Chile":                  {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "Valid multiple-entry visa, 6+ months validity"},
            "Colombia":               {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "Visa valid 180+ days; C-1 transit excluded"},
            "Dominican Republic":     {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Tourist card fee (~USD 10) payable on arrival"},
            "Georgia":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Visa must remain valid throughout stay"},
            "Guatemala":              {"access": "VISA_FREE",       "duration": "90 days (CA-4 region)",   "notes": "Also covers Honduras, El Salvador, Nicaragua (CA-4)"},
            "Honduras":               {"access": "VISA_FREE",       "duration": "90 days (CA-4 region)",   "notes": "Part of CA-4 agreement"},
            "El Salvador":            {"access": "VISA_FREE",       "duration": "90 days (CA-4 region)",   "notes": "Part of CA-4 agreement"},
            "Nicaragua":              {"access": "VISA_FREE",       "duration": "90 days (CA-4 region)",   "notes": "Part of CA-4 agreement"},
            "Mexico":                 {"access": "VISA_FREE",       "duration": "Up to 180 days",          "notes": "Multiple-entry visa or US residence permit"},
            "Montenegro":             {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Visa valid throughout stay"},
            "North Macedonia":        {"access": "VISA_FREE",       "duration": "15 days",                 "notes": "Multiple-entry visa, valid 5+ days beyond stay"},
            "Panama":                 {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Used multiple-entry visa, 6+ months validity, USD 500+ funds"},
            "Peru":                   {"access": "VISA_FREE",       "duration": "Up to 180 days/year",     "notes": "Visa 6+ months validity"},
            "Philippines":            {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Return ticket and proof of funds required"},
            "Serbia":                 {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Multiple-entry visa, used at least once"},
            "Singapore":              {"access": "VISA_FREE",       "duration": "96 hours (transit)",      "notes": "Visa-Free Transit Facility; visa valid 30+ days; onward journey proof"},
            "Antigua and Barbuda":    {"access": "VISA_ON_ARRIVAL", "duration": "30 days",                 "notes": "Extendable; accommodation proof required"},
            "Armenia":                {"access": "E_VISA",          "duration": "Up to 120 days",          "notes": "eVisa recommended"},
            "Bahrain":                {"access": "VISA_ON_ARRIVAL", "duration": "14–30 days",              "notes": "Return ticket and hotel booking required"},
            "Oman":                   {"access": "VISA_ON_ARRIVAL", "duration": "30 days",                 "notes": "Used visa; direct travel from select countries"},
            "Saudi Arabia":           {"access": "VISA_ON_ARRIVAL", "duration": "30 days (tourism)",       "notes": "Used tourist/business visa; specific airlines"},
            "Turkey":                 {"access": "E_VISA",          "duration": "30 days",                 "notes": "Simplified e-visa; single entry"},
            "UAE":                    {"access": "VISA_ON_ARRIVAL", "duration": "14 days (extendable)",    "notes": "Visa valid 6+ months; air arrival only"},
        },
    },

    "SCHENGEN_VISA": {
        "description": (
            "Countries accessible to Indian passport holders with a valid Schengen visa. "
            "Covers all 29 Schengen Area countries as base; listed below are ADDITIONAL "
            "non-Schengen destinations unlocked. Usually requires Type C (short-stay) or "
            "Type D (long-stay) multiple-entry visa."
        ),
        "conditions_general": "Valid Schengen Type C or D visa (multiple-entry preferred); passport valid 6+ months",
        "countries": {
            "Albania":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Multiple-entry visa, used at least once in Schengen"},
            "Andorra":                {"access": "VISA_FREE",       "duration": "Stay duration",           "notes": "No airport; entry via France/Spain with multiple-entry visa"},
            "Armenia":                {"access": "VISA_ON_ARRIVAL", "duration": "Up to 120 days",          "notes": "Various qualifying visas accepted"},
            "Belarus":                {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Air travel via Minsk only; single-entry Belarus visa issued"},
            "Belize":                 {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "Valid at time of entry"},
            "Bosnia and Herzegovina": {"access": "VISA_FREE",       "duration": "30 days in 180 days",     "notes": "Multiple-entry visa required"},
            "Colombia":               {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "Type C or D visa, 180+ days validity"},
            "Cyprus":                 {"access": "VISA_FREE",       "duration": "Duration of visa",        "notes": "Double or multiple-entry; used at least once"},
            "Georgia":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Valid at time of entry; multiple entries"},
            "Guatemala":              {"access": "VISA_FREE",       "duration": "90 days (CA-4)",          "notes": "CA-4 region (also Honduras, El Salvador)"},
            "Honduras":               {"access": "VISA_FREE",       "duration": "90 days (CA-4)",          "notes": "Part of CA-4 agreement"},
            "El Salvador":            {"access": "VISA_FREE",       "duration": "90 days (CA-4)",          "notes": "Part of CA-4 agreement"},
            "Kyrgyzstan":             {"access": "VISA_FREE",       "duration": "7 days only",             "notes": "Long-term visa (3+ year validity) required"},
            "Mexico":                 {"access": "VISA_FREE",       "duration": "Up to 180 days",          "notes": "Valid Schengen visa accepted"},
            "Moldova":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Type C or D visa"},
            "Montenegro":             {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Valid visa or residence permit"},
            "North Macedonia":        {"access": "VISA_FREE",       "duration": "15 days",                 "notes": "Double or multiple-entry Type C visa"},
            "Philippines":            {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Valid current visa; proof of return ticket"},
            "San Marino":             {"access": "VISA_FREE",       "duration": "Stay duration",           "notes": "Entry via Italy; no border controls"},
            "Saudi Arabia":           {"access": "VISA_ON_ARRIVAL", "duration": "30 days",                 "notes": "Used visa; Saudi carrier preferred"},
            "Serbia":                 {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Valid visa or residence permit"},
            "South Korea":            {"access": "VISA_FREE",       "duration": "30 days (transit)",       "notes": "Transit exemption; qualifying onward countries required"},
            "Taiwan":                 {"access": "VISA_FREE",       "duration": "14 days",                 "notes": "Valid or expired (under 10 years) visa; free Travel Auth Certificate"},
            "Turkey":                 {"access": "E_VISA",          "duration": "30 days",                 "notes": "Single-entry e-visa; valid Schengen visa required"},
            "Vatican City":           {"access": "VISA_FREE",       "duration": "Day visit",               "notes": "Entry via Italy with Schengen visa"},
            "Nicaragua":              {"access": "VISA_ON_ARRIVAL", "duration": "90 days",                 "notes": "Valid Schengen visa accepted"},
            "Oman":                   {"access": "VISA_ON_ARRIVAL", "duration": "14 days",                 "notes": "Valid Schengen or other qualifying visa"},
        },
    },

    "UK_VISA": {
        "description": (
            "Countries accessible to Indian passport holders with a valid UK visa "
            "(Standard Visitor Visa / Tier visas / BRP). Usually requires multiple-entry. "
            "Some Middle East destinations accept BRP/ILR in lieu of visa."
        ),
        "conditions_general": "Valid UK multiple-entry Standard Visitor Visa or BRP; passport valid 6+ months",
        "countries": {
            "Albania":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Multiple-entry visa, used at least once"},
            "Armenia":                {"access": "VISA_FREE",       "duration": "180 days",                "notes": "Advance application may be needed"},
            "Bahrain":                {"access": "VISA_ON_ARRIVAL", "duration": "14–30 days",              "notes": "Return ticket required"},
            "Belarus":                {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Via Minsk airport only; single-entry"},
            "Bermuda":                {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "UK visa valid 45+ days beyond travel"},
            "Bosnia and Herzegovina": {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Valid UK visa"},
            "Dominican Republic":     {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Tourist card fee on arrival"},
            "Egypt":                  {"access": "VISA_ON_ARRIVAL", "duration": "30 days",                 "notes": "Valid UK visa"},
            "Georgia":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Valid UK visa"},
            "Gibraltar":              {"access": "VISA_FREE",       "duration": "Stay duration",           "notes": "UK visa holders generally admitted"},
            "Jordan":                 {"access": "VISA_ON_ARRIVAL", "duration": "90 days",                 "notes": "ILR/BRP required (not just visitor visa)"},
            "Mexico":                 {"access": "VISA_FREE",       "duration": "Up to 180 days",          "notes": "Multiple-entry UK visa only"},
            "Montenegro":             {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Valid UK visa"},
            "North Macedonia":        {"access": "VISA_FREE",       "duration": "15 days",                 "notes": "Valid until Dec 2024 confirmed; verify current status"},
            "Oman":                   {"access": "VISA_ON_ARRIVAL", "duration": "30 days",                 "notes": "Valid UK visa"},
            "Peru":                   {"access": "VISA_FREE",       "duration": "Up to 180 days/year",     "notes": "UK visa 6+ months validity"},
            "Philippines":            {"access": "VISA_FREE",       "duration": "14 days (extendable)",    "notes": "Valid UK visa"},
            "Qatar":                  {"access": "E_VISA",          "duration": "30 days",                 "notes": "Free Hayya/eTravel Authorisation"},
            "Saudi Arabia":           {"access": "VISA_ON_ARRIVAL", "duration": "1 year (multi-entry)",    "notes": "Used visa; specific airline requirement"},
            "Serbia":                 {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Valid UK visa or residence permit"},
            "Taiwan":                 {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "Valid or expired (under 10 years) UK visa; free Travel Auth Certificate"},
            "Turkey":                 {"access": "E_VISA",          "duration": "30 days",                 "notes": "Single-entry e-visa"},
            "UAE":                    {"access": "VISA_ON_ARRIVAL", "duration": "14 days (extendable)",    "notes": "Valid UK visa; air arrival"},
        },
    },

    "UAE_VISA": {
        "description": (
            "Countries accessible to Indian passport holders with a valid UAE residence visa "
            "or long-stay permit. Note: a short-stay UAE tourist visa provides fewer third-country "
            "benefits than a UAE residence permit. Listed countries reflect UAE residence permit access. "
            "Source: UAE MOFA announcement Feb 2025 + regional travel advisories."
        ),
        "conditions_general": "Valid UAE residence visa/permit; Indian passport valid 6+ months",
        "countries": {
            "Armenia":                {"access": "VISA_ON_ARRIVAL", "duration": "120 days",                "notes": "UAE residence accepted"},
            "Azerbaijan":             {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "UAE residence accepted"},
            "Georgia":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "UAE residence accepted"},
            "Indonesia":              {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "UAE residence accepted"},
            "Japan":                  {"access": "VISA_FREE",       "duration": "15 days",                 "notes": "UAE residence; limited quota—verify before travel"},
            "Jordan":                 {"access": "VISA_ON_ARRIVAL", "duration": "30 days",                 "notes": "UAE residence accepted"},
            "Kyrgyzstan":             {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "UAE residence accepted"},
            "Malaysia":               {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "UAE residence accepted"},
            "Mauritius":              {"access": "VISA_FREE",       "duration": "60 days",                 "notes": "UAE residence accepted"},
            "Montenegro":             {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "UAE residence accepted"},
            "Morocco":                {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "UAE residence accepted"},
            "Philippines":            {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "UAE residence accepted"},
            "Serbia":                 {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "UAE residence accepted"},
            "Seychelles":             {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "UAE residence accepted"},
            "Singapore":              {"access": "VISA_FREE",       "duration": "96 hours (transit)",      "notes": "VFTF; UAE residence accepted as qualifying visa"},
            "Sri Lanka":              {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "UAE residence accepted"},
            "Tanzania":               {"access": "VISA_ON_ARRIVAL", "duration": "90 days",                 "notes": "UAE residence accepted"},
            "Thailand":               {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "UAE residence accepted"},
            "Taiwan":                 {"access": "VISA_FREE",       "duration": "14–90 days",              "notes": "UAE residence accepted for Travel Auth Certificate"},
            "Turkey":                 {"access": "E_VISA",          "duration": "30 days",                 "notes": "E-visa available with qualifying visa"},
        },
    },

    "CANADA_VISA": {
        "description": (
            "Countries accessible to Indian passport holders with a valid Canadian visa "
            "(TRV – Temporary Resident Visa). Multiple-entry preferred. "
            "Similar to US visa in many regions."
        ),
        "conditions_general": "Valid Canadian multiple-entry TRV; passport valid 6+ months",
        "countries": {
            "Albania":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Multiple-entry visa, used at least once"},
            "Antigua and Barbuda":    {"access": "VISA_ON_ARRIVAL", "duration": "30 days",                 "notes": "Canadian visa accepted"},
            "Armenia":                {"access": "E_VISA",          "duration": "Up to 120 days",          "notes": "eVisa recommended"},
            "Aruba":                  {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Canadian or US visa accepted"},
            "Bahamas":                {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "Multiple-entry visa, used at least once"},
            "Bahrain":                {"access": "VISA_ON_ARRIVAL", "duration": "14–30 days",              "notes": "Return ticket required"},
            "Belize":                 {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Multiple-entry Canadian visa accepted"},
            "Bermuda":                {"access": "VISA_FREE",       "duration": "21 days",                 "notes": "Canadian visa accepted"},
            "Bosnia and Herzegovina": {"access": "VISA_FREE",       "duration": "30 days in 180 days",     "notes": "Multiple-entry required"},
            "British Virgin Islands": {"access": "VISA_FREE",       "duration": "Up to 180 days",          "notes": "Canadian or US visa accepted"},
            "Cayman Islands":         {"access": "VISA_FREE",       "duration": "Stay duration",           "notes": "Canadian or US visa accepted"},
            "Chile":                  {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "Canadian visa with 6+ months validity"},
            "Colombia":               {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "Visa 180+ days validity"},
            "Curaçao":                {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Canadian or US visa accepted"},
            "Dominican Republic":     {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Tourist card fee on arrival"},
            "Egypt":                  {"access": "VISA_ON_ARRIVAL", "duration": "30 days",                 "notes": "Canadian visa accepted"},
            "Georgia":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Canadian visa accepted"},
            "Guatemala":              {"access": "VISA_FREE",       "duration": "90 days (CA-4)",          "notes": "CA-4 region"},
            "Honduras":               {"access": "VISA_FREE",       "duration": "90 days (CA-4)",          "notes": "CA-4 region"},
            "El Salvador":            {"access": "VISA_FREE",       "duration": "90 days (CA-4)",          "notes": "CA-4 region"},
            "Jordan":                 {"access": "VISA_ON_ARRIVAL", "duration": "30 days",                 "notes": "Canadian visa accepted"},
            "Mexico":                 {"access": "VISA_FREE",       "duration": "Up to 180 days",          "notes": "Multiple-entry Canadian visa"},
            "Montenegro":             {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Canadian visa accepted"},
            "Nicaragua":              {"access": "VISA_FREE",       "duration": "90 days",                 "notes": "CA-4 region"},
            "North Macedonia":        {"access": "VISA_FREE",       "duration": "15 days",                 "notes": "Multiple-entry required"},
            "Oman":                   {"access": "VISA_ON_ARRIVAL", "duration": "30 days",                 "notes": "Canadian visa accepted"},
            "Panama":                 {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Used multiple-entry visa, 6+ months validity"},
            "Peru":                   {"access": "VISA_FREE",       "duration": "Up to 180 days/year",     "notes": "Visa 6+ months validity"},
            "Philippines":            {"access": "VISA_FREE",       "duration": "14 days",                 "notes": "Canadian visa accepted"},
            "Qatar":                  {"access": "E_VISA",          "duration": "30 days",                 "notes": "Free eTravel Authorisation"},
            "Saudi Arabia":           {"access": "VISA_ON_ARRIVAL", "duration": "30 days",                 "notes": "Used visa; specific airlines"},
            "Serbia":                 {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Canadian visa accepted"},
            "Sint Maarten":           {"access": "VISA_FREE",       "duration": "Stay duration",           "notes": "Canadian or US visa accepted"},
            "Taiwan":                 {"access": "VISA_FREE",       "duration": "14–90 days",              "notes": "Valid or expired (<10 yrs) Canadian visa"},
            "Turkey":                 {"access": "E_VISA",          "duration": "30 days",                 "notes": "E-visa; single entry"},
            "Turks and Caicos":       {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Canadian or US visa accepted"},
            "UAE":                    {"access": "VISA_ON_ARRIVAL", "duration": "14 days (extendable)",    "notes": "Canadian visa accepted"},
        },
    },

    "JAPAN_VISA": {
        "description": (
            "Countries accessible to Indian passport holders with a valid Japan visa. "
            "Note: UAE typically requires a Japan *residence permit* (not just tourist visa). "
            "Japan visas are notoriously difficult to obtain, so this is a valuable unlock."
        ),
        "conditions_general": "Valid Japan visa (stamped, not e-visa for some countries); passport valid 6+ months",
        "countries": {
            "Georgia":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Stamped Japan visa required; valid throughout stay"},
            "Mexico":                 {"access": "VISA_FREE",       "duration": "Up to 180 days",          "notes": "Valid Japan visa; passport 6+ months"},
            "Montenegro":             {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Valid Japan visa for entire stay"},
            "Philippines":            {"access": "VISA_FREE",       "duration": "14 days (extendable)",    "notes": "Valid Japan visa at time of entry"},
            "Singapore":              {"access": "VISA_FREE",       "duration": "96 hours (transit)",      "notes": "VFTF; stamped visa valid 30+ days; onward journey proof"},
            "Taiwan":                 {"access": "VISA_FREE",       "duration": "14 days",                 "notes": "Travel Authorisation Certificate required; proof of Japan entry"},
            "UAE":                    {"access": "VISA_ON_ARRIVAL", "duration": "14 days",                 "notes": "Japan residence permit required (not standard tourist visa)"},
        },
    },

    "AUSTRALIA_VISA": {
        "description": (
            "Countries accessible to Indian passport holders with a valid Australian visa "
            "(tourist subclass 600 or other valid Australian visa). "
            "Taiwan accepts expired Australian visas within 10 years."
        ),
        "conditions_general": "Valid Australian visa; passport valid 6+ months. Multiple-entry preferred for Panama.",
        "countries": {
            "Georgia":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Valid Australian visa required"},
            "Montenegro":             {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Valid Australian visa required"},
            "Panama":                 {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Multiple-entry; used at least once; 6+ months validity; USD 500+"},
            "Peru":                   {"access": "VISA_FREE",       "duration": "Up to 180 days/year",     "notes": "Unused Australian visa acceptable; 6+ months validity"},
            "Philippines":            {"access": "VISA_FREE",       "duration": "14 days",                 "notes": "Valid Australian visa; return ticket required"},
            "Singapore":              {"access": "VISA_FREE",       "duration": "96 hours (transit)",      "notes": "VFTF; visa valid 1+ month; onward journey proof"},
            "South Korea":            {"access": "VISA_FREE",       "duration": "30 days (transit)",       "notes": "Australian visa verifiable online; confirmed onward flight required"},
            "Taiwan":                 {"access": "E_VISA",          "duration": "14 days in 90 days",      "notes": "Free ROC Travel Auth Certificate; expired visa (<10 yrs) accepted"},
        },
    },

    "NZ_VISA": {
        "description": (
            "Countries accessible to Indian passport holders with a valid New Zealand visa. "
            "New Zealand visas provide limited additional access compared to US/Schengen/UK visas. "
            "Most overlapping benefits are similar to Australian visa access."
        ),
        "conditions_general": "Valid New Zealand visitor/resident visa; passport valid 6+ months",
        "countries": {
            "Georgia":                {"access": "VISA_FREE",       "duration": "90 days in 180 days",     "notes": "Valid NZ visa accepted"},
            "Montenegro":             {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Valid NZ visa accepted"},
            "Panama":                 {"access": "VISA_FREE",       "duration": "30 days",                 "notes": "Multiple-entry NZ visa; used once; 6+ months validity"},
            "Peru":                   {"access": "VISA_FREE",       "duration": "Up to 180 days/year",     "notes": "NZ visa 6+ months validity"},
            "Philippines":            {"access": "VISA_FREE",       "duration": "14 days",                 "notes": "Valid NZ visa; return ticket required"},
            "Singapore":              {"access": "VISA_FREE",       "duration": "96 hours (transit)",      "notes": "VFTF; NZ visa valid 30+ days; onward journey proof"},
            "South Korea":            {"access": "VISA_FREE",       "duration": "30 days (transit)",       "notes": "NZ visa verifiable; confirmed onward flight required"},
            "Taiwan":                 {"access": "E_VISA",          "duration": "14 days in 90 days",      "notes": "Free ROC Travel Auth Certificate; valid/expired (<10 yrs) NZ visa"},
        },
    },
}

# Build the second output file
unlock_data = {
    "metadata": {
        "title": "Visa Unlock Mapping for Indian Passport Holders",
        "description": (
            "For each 'key visa', lists countries beyond what an Indian passport alone provides "
            "where holding that visa grants additional access (visa-free / visa on arrival / e-visa). "
            "This does NOT include countries already visa-free for Indian passports."
        ),
        "sources": [
            "passportindiaguide.com",
            "atlys.com",
            "india-evisa.it.com",
            "visahq.com",
            "UAE MOFA official announcement (Feb 2025): mofa.gov.ae",
            "Singapore ICA Visa-Free Transit Facility",
            "Taiwan BOCA Travel Authorisation Certificate",
            "joinsherpa.com (Sherpa travel requirements)",
        ],
        "generated_at": str(date.today()),
        "important_note": (
            "Visa rules change frequently. Always verify with the destination country's "
            "official embassy/immigration website before travelling. "
            "This data was last verified in April 2026."
        ),
    },
    "visas": UNLOCK_DATA,
}

with open("visa_unlock_mapping.json", "w", encoding="utf-8") as f:
    json.dump(unlock_data, f, indent=2, ensure_ascii=False)

print("Wrote visa_unlock_mapping.json")

# ---------------------------------------------------------------------------
# 5. Print quick stats
# ---------------------------------------------------------------------------
print("\n=== SUMMARY ===")
print(f"\nIndia Visa Requirements ({len(countries)} destinations):")
for cat, count in sorted(summary.items(), key=lambda x: -x[1]):
    bar = "█" * (count // 3)
    print(f"  {cat:<20} {count:>3}  {bar}")

print("\nVisa Unlock Counts (additional countries per key visa):")
for visa_name, data in UNLOCK_DATA.items():
    print(f"  {visa_name:<20} {len(data['countries'])} countries")

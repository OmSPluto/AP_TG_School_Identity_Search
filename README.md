# AP & Telangana School Identity Search — FAST

## Included
- Mandatory State filter
- Dependent District and Village filters
- SQLite FTS5 indexed search
- Top 3 results
- V / M / D result hierarchy
- Clickable school profile
- School information and original Excel fields
- Separate static AP and Telangana district-history dropdowns
- Verified enrichment layer keyed by UDISE code

## Verified enrichment
`data/verified_school_enrichment.csv` is the controlled enrichment layer. It is intentionally empty until official/authorized data is supplied. Do not populate it from guesses or unverified scraping.

Recommended sources include authorized UDISE+ exports/API access or other official state education datasets. UDISE+ is the Ministry of Education's official school-education MIS; current public profile/management pages may require authenticated access and/or CAPTCHA.

The enrichment fields support:
- school category
- management
- class range
- school type
- rural/urban
- LGD block
- LGD panchayat
- LGD village
- verified address
- PIN code
- source, source URL, source year
- verification status and last verified date

Original Excel remains unchanged.

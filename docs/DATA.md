# Data Documentation

## Overview

The SA New Resident Agent uses web-crawled content from three official San Antonio service provider websites. No proprietary datasets are used. All data is publicly available and crawled at runtime.

## Data Sources

### CPS Energy

| Property | Value |
|---|---|
| Source | https://www.cpsenergy.com |
| Type | Public web pages (HTML) |
| License | Public information, no redistribution restrictions |
| Crawl method | Playwright headless browser + BeautifulSoup |
| Pages crawled | ~12 service and rates pages |
| Chunks indexed | ~243 |
| Content | Residential rates, enrollment steps, billing options, contact info |

### SAWS (San Antonio Water System)

| Property | Value |
|---|---|
| Source | https://www.saws.org |
| Type | Public web pages (HTML) |
| License | Public information, no redistribution restrictions |
| Crawl method | Playwright headless browser + BeautifulSoup |
| Pages crawled | ~8 service pages |
| Chunks indexed | ~198 |
| Content | Water service signup, billing, SAWS Cares assistance program |

### City of San Antonio

| Property | Value |
|---|---|
| Source | https://www.sanantonio.gov |
| Type | Public web pages (HTML) |
| License | Public information, no redistribution restrictions |
| Crawl method | Playwright headless browser + BeautifulSoup |
| Pages crawled | ~11 pages |
| Chunks indexed | ~265 |
| Content | Resident registration, permits, trash/recycling, voter registration |

## Vector Store

| Property | Value |
|---|---|
| Store | ChromaDB 0.5.0 |
| Location | `crawler/data/chroma/` (local, not in git) |
| Collection | `sa_resident_knowledge` |
| Total chunks | ~706 |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| Dimensions | 384 |

## Data Freshness

The index is built at runtime by running `python main.py` in the `crawler/` directory. Re-run to refresh content from live websites. The index is not committed to git (see `.gitignore`).

## Privacy

No personally identifiable information (PII) is collected or stored in the vector index. All crawled content is publicly available web page text.

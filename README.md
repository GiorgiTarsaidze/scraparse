# scraparse

Interactive CLI that generates a BeautifulSoup parsing script from a natural-language extraction request.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For dev tooling (pytest/mypy/ruff):

```bash
pip install -e ".[dev]"
```

## Environment

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="..."
```

## Run modes

scraparse supports two ways of running:

1) Wizard mode (default): interactive prompts for missing values.
2) Flags mode: pass core fields as flags and the wizard will only ask for gaps (hybrid).

### Wizard mode

```bash
scraparse
```

### Flags mode (hybrid)

```bash
scraparse --url "https://example.com" --discover --prompt "Extract product_name, price"
```

You can mix flags with the wizard; any missing info will still be prompted.

To clear generated runs:

```bash
scraparse wipe
```

## User flow

1) Provide a URL and discovery preferences.
2) Describe what fields you want to extract.
3) Review and edit the proposed schema.
4) scraparse fetches HTML within the safety limits.
5) scraparse generates a parser script and saves it to `.scraparse/generated/<run_id>/parser.py`.
6) Review the script carefully, then run it manually on your HTML files.

I strongly recommend running generated parsers in a separate virtual environment that contains only the
libraries needed for parsing, so you can keep scraper execution isolated from your main dev environment.

## Discovery strategies

When `--discover` is enabled, choose a strategy with `--discover-mode`:

- `crawl`: BFS over same-domain links from each page. No selector needed.
- `pagination`: follow rel=next and "next" anchors from each fetched page.
  - Optional: `--next-selector` to target the next-page link directly.
- `listing`: fetch the start page, then follow detail links found on that same page.
  - Optional: `--detail-selector` to target product/detail links.

Examples:

```bash
scraparse --url "https://example.com/blog" --discover --discover-mode pagination \
  --next-selector "a[rel='next']"
```

```bash
scraparse --url "https://example.com/blog" --discover --discover-mode pagination
```

```bash
scraparse --url "https://example.com/catalog" --discover --discover-mode listing \
  --detail-selector ".product-card a.title"
```

```bash
scraparse --url "https://example.com/catalog" --discover --discover-mode listing
```

### Selector tips

- `--next-selector` should point to a single anchor or link tag that navigates to the next page.
  Example: `a[rel='next']`, `.pagination a.next`, `link[rel='next']`.
- `--detail-selector` should point to the anchor for each detail page.
  Example: `.card a.title`, `.product-card a[href*='/product/']`.

## Notes

- HTML only (no JS execution).
- Generated scripts are saved under `.scraparse/generated/`.

## Flag glossary

Core inputs:
- `--url`: Target URL to fetch.
- `--prompt`: Extraction request for the schema generator.
- `--context`: Optional context notes to clarify the request.
- `--discover`: Enable discovery (crawl/pagination/listing).
- `--discover-mode`: Discovery strategy: `crawl`, `pagination`, or `listing`.
- `--next-selector`: CSS selector for pagination “next” link.
- `--detail-selector`: CSS selector for detail links on a listing page.
- `--promptpack`: Prompt pack name (defaults to `default`).
- `--save-artifacts`: `true/false` to save HTML/schema artifacts.

Limits (safety):
- `--max-pages`: Max pages fetched in a run.
- `--max-depth`: Max BFS depth (crawl only).
- `--max-consecutive-failures`: Max consecutive fetch failures before abort.
- `--same-domain-only`: `true/false` to restrict discovery to the same host.
- `--timeout-connect-s`: HTTP connect timeout.
- `--timeout-read-s`: HTTP read timeout.
- `--timeout-total-s`: Total request timeout.
- `--retries`: Retry count for failed requests.
- `--backoff-base-s`: Base backoff seconds for retries.
- `--backoff-max-s`: Max backoff seconds for retries.
- `--jitter-s`: Random jitter added to backoff.
- `--rate-limit-rps`: Per-host requests per second.
- `--max-response-bytes`: Max bytes per page.
- `--max-total-bytes`: Max bytes across the whole run.
- `--max-runtime-s`: Max total runtime for a run.
- `--max-html-chars-for-llm`: Max HTML chars sent to the LLM.

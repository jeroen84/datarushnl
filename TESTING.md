# Local Integration Testing

This document describes how to run integration tests locally for the datarush.nl website.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python test.py

# Run specific tests
python test.py --render         # Page rendering tests only
python test.py --links          # Link validation only
python test.py --seo            # SEO validation only
python test.py --rss            # RSS feed validation only
python test.py --titles         # Page title validation only
python test.py --author-meta    # Author meta tag validation only
python test.py --robots         # robots.txt consistency only
python test.py --frontmatter    # Front matter validation only
python test.py --build-warnings # Build warning check only
python test.py --visual         # Visual regression vs baseline
python test.py --visual-live    # Live site vs local build comparison
python test.py --check-deps     # Check dependencies only
```

Or use Make:

```bash
make test              # Run all tests
make test-rss          # Run RSS feed tests
make test-titles       # Run page title tests
make test-robots       # Run robots.txt tests
make test-frontmatter  # Run front matter tests
make test-visual       # Visual regression vs baseline
make test-visual-live  # Live site vs local build comparison
```

## Full Setup

### Prerequisites

1. **Hugo Extended** (for Sass processing)
   ```bash
   brew install hugo
   ```

2. **Dart Sass**
   ```bash
   brew install sass/sass/sass
   ```

3. **Python Packages**
   ```bash
   pip install -r requirements.txt
   ```

### Optional Dependencies

For full test coverage, install these optional dependencies:

- **Visual Regression Tests**: Playwright + Chromium
  ```bash
  pip install playwright
  playwright install chromium
  ```

- **Interaction Tests**: Chrome, chromedriver
  ```bash
  sudo apt-get install -y chromium chromedriver
  ```

## Test Types

### Page Rendering Tests
Verify that all expected pages (11 pages) render correctly with 200 status codes.

```bash
python test.py --render
```

### Link Validation Tests
Crawl all pages and verify that all internal links are valid (not 404).

```bash
python test.py --links
```

### SEO Validation Tests
Check key pages for:
- Canonical tags
- Meta descriptions
- Title tags
- H1 headings
- Sitemap.xml existence
- robots.txt existence

```bash
python test.py --seo
```

### RSS Feed Tests
Validate the RSS feed (`/index.xml`):
- Valid XML with `<rss>` root element
- Non-empty channel `<title>` (catches empty site title config)
- Non-empty `managingEditor` and `webMaster` (catches `[Author]` config regression)
- `atom:link` self-reference present
- Each `<item>` has `<title>`, `<link>`, `<pubDate>`

```bash
python test.py --rss
```

### Page Title Tests
Verify every page's `<title>` tag contains the site name ("Datarush").
Catches regressions where the site title config is emptied or the theme's
title template breaks.

```bash
python test.py --titles
```

### Author Meta Tests
Verify every page has a non-empty `<meta name="author">` tag.
Catches regressions where `params.author` is removed from `config.toml`,
breaking the theme's `head.html` partial.

```bash
python test.py --author-meta
```

### robots.txt Consistency Tests
Verify that `robots.txt` does not disallow any URLs listed in `sitemap.xml`.
Catches contradictions like `Disallow: /author/` while the sitemap advertises
author pages. Also checks that robots.txt references the sitemap.

```bash
python test.py --robots
```

### Front Matter Tests
Scan all blog posts in `content/post/*.md` and verify required front matter
fields: `title`, `date`, `author`, `description`. Warns if any post is marked
`draft = true`. Does not need a running server.

```bash
python test.py --frontmatter
```

### Build Warning Tests
Run `hugo --minify --cleanDestinationDir` and check for `WARN` lines in
stdout/stderr. Catches template errors, config issues, and deprecation
warnings early. Does not need a running server.

```bash
python test.py --build-warnings
```

### Visual Regression Tests
Capture screenshots of key pages and compare against a saved baseline.
Generates before/after/diff images and a report with a conclusion.

**Setup** (one-time):
```bash
pip install playwright
playwright install chromium
```

**Save baseline** (run when the site looks correct):
```bash
python test.py --visual-baseline
# or: make visual-baseline
```

**Run comparison** (after making changes):
```bash
python test.py --visual
# or: make test-visual
```

**Output**:
- `screenshots/baseline/` — saved baseline screenshots
- `screenshots/current/` — current build screenshots
- `screenshots/diff/` — diff images (red highlights changed pixels)
- `screenshots/report.html` — HTML report with side-by-side before/after/diff images
- `screenshots/report.json` — JSON report with structured results

**Pages captured**: homepage, posts list, about, post/dash, post/powerbi (1920x1080, full page)

**Threshold**: 0.1% pixel difference tolerance (configurable in `VISUAL_CONFIG` in `test.py`)

**CI usage** (standalone capture/compare for before/after workflows):
```bash
python test.py --visual-capture screenshots/before    # Capture only
python test.py --visual-capture screenshots/after     # Capture only
python test.py --visual-compare screenshots/before screenshots/after  # Compare only
```

**Note**: Local screenshots are styled via Playwright route interception.
Because `canonifyURLs = true`, the local HTML references all assets via
absolute URLs (`https://www.datarush.nl/...`). The test intercepts those
requests and serves files from the local `public/` directory, so screenshots
have full CSS/JS/images even though the hashed filenames differ from the
live server.

### Live vs Local Visual Comparison

Compare the **live production site** (www.datarush.nl) against the **local
build** (latest commit). This shows exactly what will change visually when
the latest commit is deployed.

```bash
python test.py --visual-live
# or: make test-visual-live
```

**How it works**:
1. Captures screenshots from `https://www.datarush.nl` → `screenshots/before/`
2. Captures styled screenshots from the local build → `screenshots/after/`
3. Compares pixel-by-pixel and generates diff images + report
4. Prints a conclusion with per-page diff percentages

**Output** (same as visual regression):
- `screenshots/before/` — live site screenshots (production)
- `screenshots/after/` — local build screenshots (latest commit)
- `screenshots/diff/` — diff images (red highlights changed pixels)
- `screenshots/report.html` — HTML report with side-by-side images
- `screenshots/report.json` — JSON report with structured results

**Options**:
```bash
python test.py --visual-live --live-url https://staging.datarush.nl  # Custom URL
python test.py --visual-live-capture screenshots/before              # Capture live only (CI)
```

**CI usage** (split capture/compare for parallel jobs):
```bash
python test.py --visual-live-capture screenshots/before              # Live screenshots only
python test.py --no-build --visual-capture screenshots/after         # Local screenshots only
python test.py --visual-compare screenshots/before screenshots/after # Compare only
```

### Interaction Tests
Test browser interactions (navigation, clicks). Requires Chrome and chromedriver.

```bash
python test.py --interaction
```

## CI/CD Integration

The GitHub Actions workflow `.github/workflows/integration-test.yml` runs these tests on:
- Pushes to master
- Pushes to feature/** branches
- Pushes to test/** branches
- Pull requests to master

**CI Jobs**:
- `build` — Hugo build, uploads artifacts
- `page-rendering` — Page rendering + HTML validation
- `link-validation` — Internal link checker
- `seo-validation` — Canonical, meta, sitemap, robots.txt
- `visual-regression` — Before/after comparison (master vs current branch)
- `visual-live-comparison` — Live site (datarush.nl) vs local build comparison
- `regression-tests` — RSS, titles, author meta, robots.txt, front matter
- `build-warnings` — Hugo build warning check
- `interaction-tests` — Selenium browser interaction tests

## Local Development Workflow

1. Make changes to content or configuration
2. Build the site locally:
   ```bash
   hugo server -D
   ```
3. Run tests to verify:
   ```bash
   python test.py
   ```
4. Fix any issues
5. Commit and push

## Troubleshooting

### Dependency Errors

If you get dependency errors, run:
```bash
python test.py --check-deps
```

This will list all missing dependencies with installation instructions.

### Port 8000 in Use

If port 8000 is already in use, modify the `BASE_URL` in `test.py` or kill the existing process:
```bash
lsof -i :8000
kill -9 <PID>
```

### Build Failures

If the Hugo build fails, ensure you have:
- Hugo extended version installed
- All submodules initialized (`git submodule update --init`)
- No syntax errors in content files

## Test Coverage

| Test Type | Pages Tested | Checks |
|-----------|--------------|--------|
| Page Rendering | 11 | HTTP 200 status |
| Link Validation | All crawled pages | No 404 errors |
| SEO Validation | 3 key pages + sitemap + robots.txt | 6 SEO checks per page |
| RSS Feed | /index.xml | Valid XML, channel title, managingEditor, webMaster, atom:link, items |
| Page Titles | 11 | `<title>` contains "Datarush" |
| Author Meta | 11 | `<meta name="author">` non-empty |
| robots.txt | robots.txt + sitemap.xml | No Disallow/sitemap conflicts, sitemap reference |
| Front Matter | All blog posts | title, date, author, description present |
| Build Warnings | N/A | No WARN in hugo output |
| Visual Regression | 5 pages | Pixel diff vs baseline, HTML/JSON report with conclusion |
| Visual (Live vs Local) | 5 pages | Pixel diff: live site vs local build, HTML/JSON report with conclusion |
| Interaction | Home, About, Posts, Blog Post | 7 interaction tests |

## Maintainers

- Dwight (dwight-mta2nxwe) - Local test infrastructure
- See `.github/workflows/integration-test.yml` for full CI test suite

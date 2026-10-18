#!/usr/bin/env python3
"""
Local Integration Tests for datarush.nl

Run with: python test.py [--build] [--render] [--links] [--seo] [--rss]
                         [--titles] [--author-meta] [--robots] [--frontmatter]
                         [--build-warnings] [--visual] [--interaction]
                         [--visual-baseline] [--visual-capture DIR]
                         [--visual-compare BEFORE_DIR AFTER_DIR]
                         [--visual-live] [--visual-live-capture DIR]
                         [--live-url URL]

Requirements:
  - Hugo (extended version)
  - Python packages: requests, beautifulsoup4, pillow
  - For visual tests: playwright (pip install playwright && playwright install chromium)
  - For interaction tests: Chrome, chromedriver

Example:
  python test.py                          # Run all tests
  python test.py --build --render        # Run build and rendering tests only
  python test.py --rss --titles           # Run RSS and title tests only
  python test.py --visual-baseline        # Save visual baseline screenshots
  python test.py --visual                 # Compare against visual baseline
  python test.py --visual-live            # Compare live site vs local build
  python test.py --visual-capture out/    # Capture screenshots only (CI)
  python test.py --visual-compare a/ b/   # Compare two dirs only (CI)
  python test.py --visual-live-capture out/  # Capture live site screenshots (CI)
"""

import argparse
import os
import sys
import subprocess
import time
import re
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import hashlib

# Configuration
BUILD_DIR = 'public'
BASE_URL = 'http://localhost:8000'
LIVE_URL = 'https://www.datarush.nl'
PAGES = [
    '',
    'post/',
    'about/',
    'tags/',
    'categories/',
    'author/',
    'author/jeroen-van-de-erve/',
    'post/dash/',
    'post/powerbi/',
    'post/powerbi-combine/',
    'post/pensioendashboard_en/',
]

# Visual regression configuration
VISUAL_PAGES = [
    ('homepage', ''),
    ('posts', 'post/'),
    ('about', 'about/'),
    ('post-dash', 'post/dash/'),
    ('post-powerbi', 'post/powerbi/'),
]
VISUAL_CONFIG = {
    'viewport_width': 1920,
    'viewport_height': 1080,
    'threshold': 0.001,       # 0.1% pixel difference tolerance
    'pixel_delta': 10,         # Min channel difference to count as changed pixel
    'baseline_dir': 'screenshots/baseline',
    'current_dir': 'screenshots/current',
    'before_dir': 'screenshots/before',
    'after_dir': 'screenshots/after',
    'diff_dir': 'screenshots/diff',
    'report_html': 'screenshots/report.html',
    'report_json': 'screenshots/report.json',
}
SERVER_PROCESS = None


def start_server():
    """Start a local HTTP server serving the public directory."""
    global SERVER_PROCESS
    print("\n🚀 Starting local server on port 8000...")
    SERVER_PROCESS = subprocess.Popen(
        [sys.executable, '-m', 'http.server', '8000', '-d', BUILD_DIR],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)  # Give server time to start
    
    # Verify server is running
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Server is running at http://localhost:8000")
            return True
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        return False
    return True


def stop_server():
    """Stop the local HTTP server."""
    global SERVER_PROCESS
    if SERVER_PROCESS:
        print("\n🛑 Stopping local server...")
        SERVER_PROCESS.terminate()
        SERVER_PROCESS.wait(timeout=5)
        SERVER_PROCESS = None


def build_site():
    """Build the Hugo site."""
    print("\n📦 Building Hugo site...")
    
    # Clean and build
    result = subprocess.run(
        ['hugo', '--minify', '--cleanDestinationDir'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Hugo build successful")
        return True
    else:
        print(f"❌ Hugo build failed:\n{result.stderr}")
        return False


def test_page_rendering():
    """Test that all expected pages render correctly."""
    print("\n=== PAGE RENDERING TESTS ===\n")
    
    if not start_server():
        return False
    
    passed = 0
    failed = 0
    
    for page in PAGES:
        url = f"{BASE_URL}/{page}" if page else BASE_URL
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.string if soup.title else 'No title'
                print(f"✅ {url} - Status: {response.status_code}, Title: {title}")
                passed += 1
            else:
                print(f"❌ {url} - Status: {response.status_code}")
                failed += 1
        except Exception as e:
            print(f"❌ {url} - Error: {str(e)}")
            failed += 1
    
    stop_server()
    
    print(f"\n=== RESULTS ===")
    print(f"Passed: {passed}/{len(PAGES)}")
    print(f"Failed: {failed}/{len(PAGES)}")
    
    return failed == 0


def get_all_links(url):
    """Extract all links from a page."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/') or href.startswith('http'):
                links.append(href)
        return links
    except Exception:
        return []


def is_internal(url):
    """Check if URL is internal to the site."""
    parsed = urlparse(url)
    return parsed.netloc == '' or parsed.netloc == urlparse(BASE_URL).netloc


def test_link_validation():
    """Test that all internal links are valid."""
    print("\n=== LINK VALIDATION TESTS ===\n")
    
    if not start_server():
        return False
    
    # Crawl all pages
    pages_to_check = [BASE_URL]
    checked_pages = set()
    all_links = {}
    
    while pages_to_check:
        url = pages_to_check.pop(0)
        if url in checked_pages:
            continue
        checked_pages.add(url)
        links = get_all_links(url)
        all_links[url] = links
        for link in links:
            if is_internal(link):
                full_link = urljoin(BASE_URL, link)
                if full_link not in checked_pages:
                    pages_to_check.append(full_link)
    
    # Test all internal links
    passed = 0
    failed = 0
    broken_links = []
    
    for page, links in all_links.items():
        for link in links:
            if is_internal(link):
                full_link = urljoin(BASE_URL, link)
                try:
                    response = requests.head(full_link, timeout=5, allow_redirects=True)
                    if response.status_code in [200, 404]:
                        if response.status_code == 404:
                            print(f"❌ Broken link: {link} (from {page})")
                            broken_links.append((link, page))
                            failed += 1
                        else:
                            passed += 1
                    else:
                        print(f"⚠️  Unexpected status: {link} - {response.status_code}")
                        failed += 1
                except Exception as e:
                    print(f"❌ Error accessing: {link} - {str(e)}")
                    broken_links.append((link, page))
                    failed += 1
    
    stop_server()
    
    print(f"\n=== RESULTS ===")
    print(f"Total links checked: {passed + failed}")
    print(f"Working: {passed}")
    print(f"Broken: {failed}")
    
    if broken_links:
        print("\n=== BROKEN LINKS ===")
        for link, page in broken_links:
            print(f"  {link} (from {page})")
    
    return failed == 0


def test_seo_validation():
    """Test SEO elements on key pages."""
    print("\n=== SEO VALIDATION TESTS ===\n")
    
    if not start_server():
        return False
    
    # Pages to check
    pages = [
        BASE_URL,
        f"{BASE_URL}/post/dash/",
        f"{BASE_URL}/about/",
    ]
    
    passed = 0
    failed = 0
    
    for url in pages:
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for canonical tag
            canonical = soup.find('link', {'rel': 'canonical'})
            if canonical:
                print(f"✅ {url} - Has canonical tag: {canonical.get('href')}")
                passed += 1
            else:
                print(f"❌ {url} - Missing canonical tag")
                failed += 1
            
            # Check for meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                print(f"   ✅ Has meta description")
                passed += 1
            else:
                print(f"   ⚠️  Missing meta description")
                failed += 1
            
            # Check for title
            if soup.title:
                print(f"   ✅ Has title tag")
                passed += 1
            else:
                print(f"   ❌ Missing title tag")
                failed += 1
            
            # Check for h1
            h1 = soup.find('h1')
            if h1:
                print(f"   ✅ Has h1 heading")
                passed += 1
            else:
                print(f"   ❌ Missing h1 heading")
                failed += 1
        except Exception as e:
            print(f"❌ {url} - Error: {str(e)}")
            failed += 4  # 4 checks per page
    
    # Check sitemap.xml
    try:
        sitemap_url = f"{BASE_URL}/sitemap.xml"
        response = requests.get(sitemap_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {sitemap_url} - Sitemap exists")
            passed += 1
        else:
            print(f"❌ {sitemap_url} - Sitemap not found")
            failed += 1
    except Exception as e:
        print(f"❌ Sitemap check failed: {str(e)}")
        failed += 1
    
    # Check robots.txt
    try:
        robots_url = f"{BASE_URL}/robots.txt"
        response = requests.get(robots_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {robots_url} - robots.txt exists")
            passed += 1
        else:
            print(f"❌ {robots_url} - robots.txt not found")
            failed += 1
    except Exception as e:
        print(f"❌ robots.txt check failed: {str(e)}")
        failed += 1
    
    stop_server()

    print(f"\n=== RESULTS ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return failed == 0


def test_rss_feed():
    """Test that the RSS feed is valid XML with expected elements.

    Catches regressions where config changes break the RSS template
    (e.g. params.author removed, empty site title).
    """
    print("\n=== RSS FEED TESTS ===\n")

    if not start_server():
        return False

    passed = 0
    failed = 0

    # Hugo outputs RSS at /index.xml by default
    rss_urls = [f"{BASE_URL}/index.xml", f"{BASE_URL}/rss.xml", f"{BASE_URL}/feed.xml"]
    rss_content = None
    rss_url = None

    for url in rss_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200 and 'xml' in response.headers.get('Content-Type', ''):
                rss_content = response.text
                rss_url = url
                break
        except Exception:
            continue

    if not rss_content:
        print("FAIL: No RSS feed found at /index.xml, /rss.xml, or /feed.xml")
        stop_server()
        return False

    print(f"PASS: RSS feed found at {rss_url}")
    passed += 1

    # Parse XML
    try:
        root = ET.fromstring(rss_content)
        print("PASS: RSS feed is valid XML")
        passed += 1
    except ET.ParseError as e:
        print(f"FAIL: RSS feed is not valid XML: {e}")
        failed += 1
        stop_server()
        return False

    # Check root element
    if root.tag == 'rss':
        print("PASS: Root element is <rss>")
        passed += 1
    else:
        print(f"FAIL: Root element is <{root.tag}>, expected <rss>")
        failed += 1

    # Check channel
    channel = root.find('channel')
    if channel is None:
        print("FAIL: Missing <channel> element")
        failed += 1
        stop_server()
        return False
    print("PASS: <channel> element exists")
    passed += 1

    # Check channel title is not empty (catches empty site title regression)
    title = channel.find('title')
    if title is not None and title.text and title.text.strip():
        print(f"PASS: Channel title: '{title.text.strip()}'")
        passed += 1
    else:
        print("FAIL: Channel title is empty or missing (check site title in config.toml)")
        failed += 1

    # Check managingEditor (catches params.author / [Author] regression)
    managing = channel.find('managingEditor')
    if managing is not None and managing.text and managing.text.strip():
        print(f"PASS: managingEditor: '{managing.text.strip()}'")
        passed += 1
    else:
        print("FAIL: managingEditor is empty or missing (check [Author] config section)")
        failed += 1

    # Check webMaster
    webmaster = channel.find('webMaster')
    if webmaster is not None and webmaster.text and webmaster.text.strip():
        print(f"PASS: webMaster: '{webmaster.text.strip()}'")
        passed += 1
    else:
        print("FAIL: webMaster is empty or missing (check [Author] config section)")
        failed += 1

    # Check atom:link self-reference
    atom_link = channel.find('{http://www.w3.org/2005/Atom}link')
    if atom_link is not None and atom_link.get('rel') == 'self':
        print(f"PASS: atom:link self-reference present")
        passed += 1
    else:
        print("FAIL: Missing atom:link self-reference")
        failed += 1

    # Check items
    items = channel.findall('item')
    if len(items) > 0:
        print(f"PASS: RSS feed has {len(items)} items")
        passed += 1
    else:
        print("FAIL: RSS feed has no items")
        failed += 1

    # Check each item has required fields
    for i, item in enumerate(items):
        item_title = item.find('title')
        item_link = item.find('link')
        item_pubdate = item.find('pubDate')
        item_ok = True
        if item_title is None or not item_title.text or not item_title.text.strip():
            print(f"FAIL: Item {i+1}: missing or empty <title>")
            item_ok = False
        if item_link is None or not item_link.text or not item_link.text.strip():
            print(f"FAIL: Item {i+1}: missing or empty <link>")
            item_ok = False
        if item_pubdate is None or not item_pubdate.text or not item_pubdate.text.strip():
            print(f"FAIL: Item {i+1}: missing or empty <pubDate>")
            item_ok = False
        if item_ok:
            print(f"PASS: Item {i+1}: '{item_title.text.strip()[:60]}'")
            passed += 1
        else:
            failed += 1

    stop_server()

    print(f"\n=== RESULTS ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return failed == 0


def test_page_titles():
    """Test that all pages have a non-empty, well-formed <title> tag.

    The theme renders titles as '{params.author} | {page.title}'.
    Catches regressions where params.author or site title config is
    removed, which would produce titles like ' | Posts' or empty titles.
    """
    print("\n=== PAGE TITLE TESTS ===\n")

    if not start_server():
        return False

    passed = 0
    failed = 0

    for page in PAGES:
        url = f"{BASE_URL}/{page}" if page else BASE_URL
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                title_text = title_tag.string.strip()
                # Title should not be empty, should not start with '|'
                # (which indicates missing author/site name)
                if not title_text:
                    print(f"FAIL: {url} - Title is empty")
                    failed += 1
                elif title_text.startswith('|'):
                    print(f"FAIL: {url} - Title '{title_text}' starts with '|' (missing author/site name in config)")
                    failed += 1
                else:
                    print(f"PASS: {url} - Title: '{title_text}'")
                    passed += 1
            else:
                print(f"FAIL: {url} - Missing <title> tag")
                failed += 1
        except Exception as e:
            print(f"FAIL: {url} - Error: {str(e)}")
            failed += 1

    stop_server()

    print(f"\n=== RESULTS ===")
    print(f"Passed: {passed}/{len(PAGES)}")
    print(f"Failed: {failed}/{len(PAGES)}")

    return failed == 0


def test_author_meta():
    """Test that all pages have a non-empty <meta name="author"> tag.

    Catches regressions where params.author is removed from config.toml,
    breaking the theme's head.html partial.
    """
    print("\n=== AUTHOR META TESTS ===\n")

    if not start_server():
        return False

    passed = 0
    failed = 0

    for page in PAGES:
        url = f"{BASE_URL}/{page}" if page else BASE_URL
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta and author_meta.get('content', '').strip():
                print(f"PASS: {url} - Author: '{author_meta['content'].strip()}'")
                passed += 1
            else:
                content = author_meta.get('content', '') if author_meta else '(tag missing)'
                print(f"FAIL: {url} - Missing or empty author meta: {content}")
                failed += 1
        except Exception as e:
            print(f"FAIL: {url} - Error: {str(e)}")
            failed += 1

    stop_server()

    print(f"\n=== RESULTS ===")
    print(f"Passed: {passed}/{len(PAGES)}")
    print(f"Failed: {failed}/{len(PAGES)}")

    return failed == 0


def test_robots_txt():
    """Test that robots.txt does not disallow pages listed in sitemap.xml.

    Catches contradictions where robots.txt blocks pages that the
    sitemap advertises (e.g. Disallow: /author/ while sitemap lists
    /author/ pages).
    """
    print("\n=== ROBOTS.TXT CONSISTENCY TESTS ===\n")

    if not start_server():
        return False

    passed = 0
    failed = 0

    # Fetch robots.txt
    try:
        robots_response = requests.get(f"{BASE_URL}/robots.txt", timeout=5)
        if robots_response.status_code != 200:
            print("FAIL: robots.txt not accessible")
            stop_server()
            return False
        robots_text = robots_response.text
        print("PASS: robots.txt is accessible")
        passed += 1
    except Exception as e:
        print(f"FAIL: Failed to fetch robots.txt: {e}")
        stop_server()
        return False

    # Parse Disallow rules
    disallow_rules = []
    for line in robots_text.splitlines():
        line = line.strip()
        if line.lower().startswith('disallow:'):
            path = line.split(':', 1)[1].strip()
            if path:
                disallow_rules.append(path)

    if disallow_rules:
        print(f"   Disallow rules: {disallow_rules}")
    else:
        print("   No Disallow rules found")

    # Fetch sitemap.xml
    try:
        sitemap_response = requests.get(f"{BASE_URL}/sitemap.xml", timeout=5)
        if sitemap_response.status_code != 200:
            print("FAIL: sitemap.xml not accessible")
            failed += 1
            stop_server()
            return failed == 0
        print("PASS: sitemap.xml is accessible")
        passed += 1
    except Exception as e:
        print(f"FAIL: Failed to fetch sitemap.xml: {e}")
        failed += 1
        stop_server()
        return failed == 0

    # Parse sitemap URLs (handle namespace)
    try:
        root = ET.fromstring(sitemap_response.text)
        urls = []
        for elem in root.iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag == 'loc' and elem.text:
                urls.append(elem.text.strip())
        print(f"   Sitemap contains {len(urls)} URLs")
        passed += 1
    except ET.ParseError as e:
        print(f"FAIL: sitemap.xml is not valid XML: {e}")
        failed += 1
        stop_server()
        return failed == 0

    # Check for conflicts: sitemap URLs disallowed by robots.txt
    conflicts = []
    for sitemap_url in urls:
        path = urlparse(sitemap_url).path
        for rule in disallow_rules:
            if path.startswith(rule):
                conflicts.append((sitemap_url, rule))

    if conflicts:
        for url, rule in conflicts:
            print(f"FAIL: {url} is disallowed by robots.txt rule '{rule}'")
            failed += 1
    else:
        print("PASS: No conflicts between robots.txt and sitemap.xml")
        passed += 1

    # Check robots.txt references the sitemap
    if re.search(r'^sitemap:', robots_text, re.MULTILINE | re.IGNORECASE):
        print("PASS: robots.txt references sitemap")
        passed += 1
    else:
        print("FAIL: robots.txt does not reference sitemap")
        failed += 1

    stop_server()

    print(f"\n=== RESULTS ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return failed == 0


def test_front_matter():
    """Test that all blog posts have required front matter fields.

    Checks content/post/*.md (excluding _index.md) for:
    title, date, author, description. Does not need a running server.
    """
    print("\n=== FRONT MATTER TESTS ===\n")

    passed = 0
    failed = 0

    post_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content', 'post')
    required_fields = ['title', 'date', 'author', 'description']

    if not os.path.isdir(post_dir):
        print(f"FAIL: Post directory not found: {post_dir}")
        return False

    post_files = []
    for f in sorted(os.listdir(post_dir)):
        if f.endswith('.md') and f != '_index.md':
            post_files.append(os.path.join(post_dir, f))

    if not post_files:
        print("FAIL: No blog post files found")
        return False

    print(f"Found {len(post_files)} blog posts\n")

    for filepath in post_files:
        filename = os.path.basename(filepath)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"FAIL: {filename} - Error reading file: {e}")
            failed += 1
            continue

        # Extract front matter keys
        fm_keys = set()
        if content.startswith('+++'):
            end = content.find('+++', 3)
            if end == -1:
                print(f"FAIL: {filename} - Malformed TOML front matter (no closing +++)")
                failed += 1
                continue
            for line in content[3:end].splitlines():
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    fm_keys.add(line.split('=', 1)[0].strip())
        elif content.startswith('---'):
            end = content.find('---', 3)
            if end == -1:
                print(f"FAIL: {filename} - Malformed YAML front matter (no closing ---)")
                failed += 1
                continue
            for line in content[3:end].splitlines():
                line = line.strip()
                if ':' in line and not line.startswith('#') and not line.startswith('-'):
                    fm_keys.add(line.split(':', 1)[0].strip())
        else:
            print(f"FAIL: {filename} - No front matter found")
            failed += 1
            continue

        # Check required fields
        missing = [f for f in required_fields if f not in fm_keys]
        if missing:
            print(f"FAIL: {filename} - Missing fields: {missing}")
            failed += 1
        else:
            print(f"PASS: {filename} - All required fields present")
            passed += 1

        # Warn if draft = true
        if 'draft' in fm_keys:
            fm_text = content[3:content.find('+++', 3)] if content.startswith('+++') else content[3:content.find('---', 3)]
            if re.search(r'draft\s*[=:]\s*true', fm_text, re.IGNORECASE):
                print(f"   WARN: {filename} is marked as draft (will not be published)")

    print(f"\n=== RESULTS ===")
    print(f"Passed: {passed}/{len(post_files)}")
    print(f"Failed: {failed}/{len(post_files)}")

    return failed == 0


def test_build_warnings():
    """Test that the Hugo build succeeds without errors.

    Logs deprecation warnings but does not fail on them (themes may use
    deprecated Hugo APIs that are not yet removed). Only fails on actual
    build errors or ERROR/FATAL messages. Does not need a running server.
    """
    print("\n=== BUILD WARNING TESTS ===\n")

    passed = 0
    failed = 0

    result = subprocess.run(
        ['hugo', '--minify', '--cleanDestinationDir'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"FAIL: Hugo build failed:\n{result.stderr}")
        return False

    print("PASS: Hugo build succeeded")
    passed += 1

    # Collect all output for warning/error scanning
    all_output = (result.stderr + '\n' + result.stdout).strip()

    # Log deprecation warnings (informational only, does not fail the test)
    warn_lines = [l for l in all_output.splitlines()
                  if 'WARN' in l.upper() and 'deprecated' in l.lower()]
    if warn_lines:
        for line in warn_lines:
            print(f"  WARN (informational): {line.strip()}")
        print(f"  ({len(warn_lines)} deprecation warning(s) logged, not failing)")
        passed += 1

    # Only fail on actual errors (not deprecation warnings)
    error_lines = [l for l in all_output.splitlines()
                   if ('ERROR' in l.upper() or 'FATAL' in l.upper())
                   and 'deprecated' not in l.lower()]
    if error_lines:
        for line in error_lines:
            print(f"FAIL: Build error: {line}")
            failed += 1
    else:
        print("PASS: No build errors found")
        passed += 1

    print(f"\n=== RESULTS ===")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return failed == 0


def _check_playwright():
    """Check if Playwright is available. Returns True if available."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except ImportError:
        return False


_CONTENT_TYPES = {
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.mjs': 'application/javascript',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.eot': 'application/vnd.ms-fontobject',
    '.otf': 'font/otf',
    '.html': 'text/html; charset=utf-8',
    '.htm': 'text/html; charset=utf-8',
    '.xml': 'application/xml',
    '.json': 'application/json',
    '.pdf': 'application/pdf',
    '.txt': 'text/plain; charset=utf-8',
    '.map': 'application/json',
}


def _make_route_handler(build_dir):
    """Create a Playwright route handler that serves local files for requests
    to the production domain.

    Because canonifyURLs=true, the local HTML references all assets via
    absolute URLs (https://www.datarush.nl/...). Without interception those
    requests hit the live server, which may serve different hashed filenames
    (404) or SRI mismatches, resulting in unstyled screenshots.

    This handler intercepts those requests and serves the files from the
    local build directory instead, so local screenshots have full styling.
    """
    build_abs = os.path.abspath(build_dir)

    def handler(route):
        url = route.request.url
        parsed = urlparse(url)
        path = parsed.path
        if path == '/' or path == '':
            path = '/index.html'
        elif path.endswith('/'):
            path = path + 'index.html'

        local_path = os.path.normpath(
            os.path.join(build_abs, path.lstrip('/'))
        )
        # Prevent directory traversal
        if not local_path.startswith(build_abs + os.sep) and local_path != build_abs:
            route.fulfill(status=403, body='Forbidden',
                          headers={'Access-Control-Allow-Origin': '*'})
            return

        if os.path.isfile(local_path):
            ext = os.path.splitext(local_path)[1].lower()
            content_type = _CONTENT_TYPES.get(ext, 'application/octet-stream')
            with open(local_path, 'rb') as f:
                body = f.read()
            route.fulfill(
                status=200,
                content_type=content_type,
                body=body,
                headers={'Access-Control-Allow-Origin': '*'},
            )
        else:
            route.fulfill(status=404, body='Not found',
                          headers={'Access-Control-Allow-Origin': '*'})

    return handler


def capture_visual_screenshots(output_dir, base_url=None,
                               intercept_production=False,
                               goto_timeout=30000):
    """Capture screenshots of key pages using Playwright.

    Args:
        output_dir: Directory to save screenshots.
        base_url: Base URL to visit (default: local BASE_URL).
        intercept_production: If True, intercept requests to the production
            domain (LIVE_URL) and serve files from the local build directory.
            This ensures styled screenshots even though canonifyURLs=true
            makes all asset URLs point to the production domain.
        goto_timeout: Timeout for page.goto() in milliseconds.

    Returns:
        Dict mapping page name to screenshot file path.
    """
    from playwright.sync_api import sync_playwright

    if base_url is None:
        base_url = BASE_URL

    os.makedirs(output_dir, exist_ok=True)
    screenshots = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={
                'width': VISUAL_CONFIG['viewport_width'],
                'height': VISUAL_CONFIG['viewport_height'],
            },
            ignore_https_errors=True,
        )
        page = context.new_page()

        if intercept_production:
            production_host = urlparse(LIVE_URL).netloc
            handler = _make_route_handler(BUILD_DIR)
            page.route(f'https://{production_host}/**', handler)
            page.route(f'http://{production_host}/**', handler)

        for name, path in VISUAL_PAGES:
            url = f"{base_url}/{path}" if path else base_url
            page.goto(url, wait_until='networkidle', timeout=goto_timeout)
            page.wait_for_timeout(1000)  # Allow animations/fonts to settle
            screenshot_path = os.path.join(output_dir, f"{name}.png")
            page.screenshot(path=screenshot_path, full_page=True)
            screenshots[name] = screenshot_path
            print(f"  Captured: {name}")

        browser.close()

    return screenshots


def compare_visual_screenshots(before_dir, after_dir, diff_dir=None, threshold=None):
    """Compare before/after screenshots pixel-by-pixel using PIL.

    Args:
        before_dir: Directory containing 'before' screenshots.
        after_dir: Directory containing 'after' screenshots.
        diff_dir: Directory to save diff images (default: VISUAL_CONFIG['diff_dir']).
        threshold: Max diff ratio to consider a match (default: VISUAL_CONFIG['threshold']).

    Returns:
        Dict mapping page name to comparison result.
    """
    from PIL import Image, ImageChops

    if diff_dir is None:
        diff_dir = VISUAL_CONFIG['diff_dir']
    if threshold is None:
        threshold = VISUAL_CONFIG['threshold']
    pixel_delta = VISUAL_CONFIG['pixel_delta']

    os.makedirs(diff_dir, exist_ok=True)
    results = {}

    for name, _ in VISUAL_PAGES:
        before_path = os.path.join(before_dir, f"{name}.png")
        after_path = os.path.join(after_dir, f"{name}.png")
        diff_path = os.path.join(diff_dir, f"{name}-diff.png")

        if not os.path.exists(before_path):
            results[name] = {
                'status': 'no_before',
                'message': 'No before screenshot found',
                'diff_percent': None,
                'diff_pixels': 0,
                'total_pixels': 0,
            }
            continue

        if not os.path.exists(after_path):
            results[name] = {
                'status': 'no_after',
                'message': 'No after screenshot found',
                'diff_percent': None,
                'diff_pixels': 0,
                'total_pixels': 0,
            }
            continue

        before_img = Image.open(before_path).convert('RGB')
        after_img = Image.open(after_path).convert('RGB')

        # Handle dimension mismatch by resizing after to match before
        if before_img.size != after_img.size:
            after_img = after_img.resize(before_img.size, Image.Resampling.LANCZOS)

        diff = ImageChops.difference(before_img, after_img)
        diff_bbox = diff.getbbox()

        if diff_bbox is None:
            results[name] = {
                'status': 'match',
                'diff_percent': 0.0,
                'diff_pixels': 0,
                'total_pixels': before_img.size[0] * before_img.size[1],
                'before_image': before_path,
                'after_image': after_path,
            }
            continue

        # Count changed pixels using histogram (avoids deprecated getdata())
        gray_diff = diff.convert('L')
        thresholded = gray_diff.point(lambda x: 255 if x > pixel_delta else 0)
        histogram = thresholded.histogram()
        diff_pixels = sum(histogram[1:])  # Count all non-zero bins
        total_pixels = before_img.size[0] * before_img.size[1]
        diff_percent = diff_pixels / total_pixels if total_pixels > 0 else 1.0

        # Generate diff visualization: after image with red overlay on changed pixels
        diff_img = after_img.copy()
        mask = thresholded.point(lambda x: 255 if x > 0 else 0)
        red_overlay = Image.new('RGB', before_img.size, (255, 0, 0))
        diff_img.paste(red_overlay, mask=mask)
        diff_img.save(diff_path)

        results[name] = {
            'status': 'match' if diff_percent <= threshold else 'diff',
            'diff_percent': diff_percent,
            'diff_pixels': diff_pixels,
            'total_pixels': total_pixels,
            'before_image': before_path,
            'after_image': after_path,
            'diff_image': diff_path,
        }

    return results


def generate_visual_report(results, html_path=None, json_path=None,
                           before_dir=None, after_dir=None, context="baseline"):
    """Generate HTML and JSON visual regression reports.

    Args:
        results: Dict from compare_visual_screenshots().
        html_path: Path for HTML report (default: VISUAL_CONFIG['report_html']).
        json_path: Path for JSON report (default: VISUAL_CONFIG['report_json']).
        before_dir: Directory of before screenshots (for HTML image links).
        after_dir: Directory of after screenshots (for HTML image links).
        context: Label describing what is being compared (e.g. "baseline",
            "Live (production) vs Local (latest commit)").
    """
    import json as json_module

    if html_path is None:
        html_path = VISUAL_CONFIG['report_html']
    if json_path is None:
        json_path = VISUAL_CONFIG['report_json']

    matched = sum(1 for r in results.values() if r['status'] == 'match')
    diffs = sum(1 for r in results.values() if r['status'] == 'diff')
    errors = sum(1 for r in results.values() if r['status'] in ('no_before', 'no_after'))
    total = len(results)

    # JSON report
    report_data = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'context': context,
        'summary': {
            'total_pages': total,
            'matched': matched,
            'differences': diffs,
            'errors': errors,
            'threshold': VISUAL_CONFIG['threshold'],
        },
        'conclusion': (
            f"{matched}/{total} pages match ({context}). "
            f"{diffs} page(s) have visual differences."
            if diffs > 0 else
            f"All {total} pages match ({context}). No visual regressions detected."
        ),
        'results': {name: {k: v for k, v in r.items()} for name, r in results.items()},
    }

    os.makedirs(os.path.dirname(json_path) or '.', exist_ok=True)
    with open(json_path, 'w') as f:
        json_module.dump(report_data, f, indent=2)

    # HTML report
    def img_tag(path, label, width='400'):
        if path and os.path.exists(path):
            # Use relative path for portability
            rel = os.path.relpath(path)
            return f'<div class="img-box"><p class="img-label">{label}</p>' \
                   f'<a href="{rel}" target="_blank">' \
                   f'<img src="{rel}" width="{width}" alt="{label}"></a></div>'
        return f'<div class="img-box"><p class="img-label">{label}</p><p>(not available)</p></div>'

    rows = []
    for name, r in results.items():
        status = r['status']
        if status == 'match':
            status_html = '<span class="pass">MATCH</span>'
            diff_pct = '0.00%'
        elif status == 'diff':
            status_html = '<span class="fail">DIFF</span>'
            diff_pct = f"{r['diff_percent'] * 100:.2f}%"
        else:
            status_html = f'<span class="warn">{status.upper()}</span>'
            diff_pct = 'N/A'

        before_path = r.get('before_image', '')
        after_path = r.get('after_image', '')
        diff_path = r.get('diff_image', '')

        detail = ''
        if status == 'diff':
            detail = (
                f'<div class="images">'
                f'{img_tag(before_path, "Before")}'
                f'{img_tag(after_path, "After")}'
                f'{img_tag(diff_path, "Diff (red = changed)")}'
                f'</div>'
            )

        rows.append(
            f'<tr><td>{name}</td><td>{status_html}</td>'
            f'<td>{diff_pct}</td>'
            f'<td>{r.get("diff_pixels", 0):,} / {r.get("total_pixels", 0):,}</td></tr>'
            f'<tr><td colspan="4">{detail}</td></tr>'
        )

    conclusion_class = 'fail' if diffs > 0 else 'pass'
    conclusion_text = report_data['conclusion']

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Visual Comparison Report - {context} - datarush.nl</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         max-width: 1200px; margin: 0 auto; padding: 20px; color: #333; }}
  h1 {{ border-bottom: 2px solid #ddd; padding-bottom: 10px; }}
  .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
  .stat {{ background: #f5f5f5; padding: 15px 25px; border-radius: 8px; text-align: center; }}
  .stat .num {{ font-size: 2em; font-weight: bold; }}
  .stat .label {{ color: #666; font-size: 0.9em; }}
  .conclusion {{ padding: 15px 20px; border-radius: 8px; margin: 20px 0; font-size: 1.1em; }}
  .conclusion.pass {{ background: #d4edda; color: #155724; }}
  .conclusion.fail {{ background: #f8d7da; color: #721c24; }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
  th {{ background: #f5f5f5; }}
  .pass {{ color: #155724; font-weight: bold; }}
  .fail {{ color: #721c24; font-weight: bold; }}
  .warn {{ color: #856404; font-weight: bold; }}
  .images {{ display: flex; gap: 15px; flex-wrap: wrap; padding: 10px 0; }}
  .img-box {{ text-align: center; }}
  .img-label {{ font-weight: bold; margin-bottom: 5px; }}
  .img-box img {{ border: 1px solid #ddd; border-radius: 4px; }}
  .timestamp {{ color: #999; font-size: 0.85em; }}
</style>
</head>
<body>
<h1>Visual Comparison Report: {context}</h1>
<p class="timestamp">Generated: {report_data['timestamp']}</p>

<div class="summary">
  <div class="stat"><div class="num">{total}</div><div class="label">Total Pages</div></div>
  <div class="stat"><div class="num" style="color:#155724">{matched}</div><div class="label">Matched</div></div>
  <div class="stat"><div class="num" style="color:#721c24">{diffs}</div><div class="label">Differences</div></div>
  <div class="stat"><div class="num" style="color:#856404">{errors}</div><div class="label">Errors</div></div>
</div>

<div class="conclusion {conclusion_class}">{conclusion_text}</div>

<table>
<tr><th>Page</th><th>Status</th><th>Diff %</th><th>Pixels Changed</th></tr>
{''.join(rows)}
</table>

<p class="timestamp">Threshold: {VISUAL_CONFIG['threshold'] * 100:.1f}% pixel difference tolerance</p>
</body>
</html>"""

    with open(html_path, 'w') as f:
        f.write(html)

    return report_data


def print_visual_conclusion(results, context="baseline"):
    """Print a human-readable conclusion of visual regression results."""
    matched = sum(1 for r in results.values() if r['status'] == 'match')
    diffs = sum(1 for r in results.values() if r['status'] == 'diff')
    errors = sum(1 for r in results.values() if r['status'] in ('no_before', 'no_after'))
    total = len(results)

    line = '=' * 60
    print(f"\n{line}")
    print(f"VISUAL COMPARISON CONCLUSION: {context}")
    print(f"{line}")
    print(f"  Total pages checked:  {total}")
    print(f"  Matching:             {matched}")
    print(f"  Visual differences:   {diffs}")
    print(f"  Errors (no image):    {errors}")
    print(f"{line}")

    if diffs > 0:
        print("\n  Pages with visual differences:")
        for name, r in results.items():
            if r['status'] == 'diff':
                print(f"    - {name}: {r['diff_percent'] * 100:.2f}% pixels differ "
                      f"({r['diff_pixels']:,} / {r['total_pixels']:,})")
        print(f"\n  Diff images:  {VISUAL_CONFIG['diff_dir']}/")
        print(f"  HTML report:  {VISUAL_CONFIG['report_html']}")
        print(f"  JSON report:  {VISUAL_CONFIG['report_json']}")
        print(f"\n  CONCLUSION: {diffs} page(s) have visual differences ({context}).")
    elif errors > 0:
        print("\n  Some pages could not be compared (missing screenshots).")
        print("  Run 'python test.py --visual-baseline' to create baseline screenshots.")
        print(f"\n  CONCLUSION: {matched}/{total} pages match. {errors} page(s) have no baseline.")
    else:
        print(f"\n  CONCLUSION: All {total} pages match ({context}). No visual regressions detected.")
    print(f"{line}")


def test_visual_regression():
    """Run visual regression tests: capture current screenshots and compare
    against saved baseline. Generates diff images and a report with conclusion.

    Requires: playwright (pip install playwright && playwright install chromium)
    Baseline:  screenshots/baseline/ (create with --visual-baseline)
    """
    print("\n=== VISUAL REGRESSION TESTS ===\n")

    if not _check_playwright():
        print("SKIP: Playwright not installed.")
        print("   Install with: pip install playwright && playwright install chromium")
        return True

    baseline_dir = VISUAL_CONFIG['baseline_dir']
    if not os.path.isdir(baseline_dir) or not any(
        f.endswith('.png') for f in os.listdir(baseline_dir)
    ):
        print(f"SKIP: No baseline screenshots found in {baseline_dir}/")
        print("   Run 'python test.py --visual-baseline' first to create baseline.")
        return True

    if not start_server():
        return False

    # Capture current screenshots (with production URL interception for styling)
    print("Capturing current screenshots...")
    current_dir = VISUAL_CONFIG['current_dir']
    try:
        capture_visual_screenshots(current_dir, intercept_production=True)
    except Exception as e:
        stop_server()
        print(f"FAIL: Screenshot capture failed: {e}")
        return False

    stop_server()

    # Compare against baseline
    print("\nComparing against baseline...")
    results = compare_visual_screenshots(baseline_dir, current_dir)

    # Generate reports
    print("\nGenerating reports...")
    generate_visual_report(results, context="Baseline vs Current build")

    # Print conclusion
    print_visual_conclusion(results, context="Baseline vs Current build")

    failed = sum(1 for r in results.values() if r['status'] == 'diff')
    return failed == 0


def save_visual_baseline():
    """Save current build screenshots as the baseline for future comparisons.

    Requires: playwright (pip install playwright && playwright install chromium)
    """
    print("\n=== SAVE VISUAL BASELINE ===\n")

    if not _check_playwright():
        print("FAIL: Playwright not installed.")
        print("   Install with: pip install playwright && playwright install chromium")
        return False

    if not start_server():
        return False

    baseline_dir = VISUAL_CONFIG['baseline_dir']
    print(f"Capturing baseline screenshots to {baseline_dir}/...")
    try:
        capture_visual_screenshots(baseline_dir, intercept_production=True)
    except Exception as e:
        stop_server()
        print(f"FAIL: Screenshot capture failed: {e}")
        return False

    stop_server()

    print(f"\nPASS: Baseline saved to {baseline_dir}/")
    print(f"   {len(VISUAL_PAGES)} pages captured: {', '.join(n for n, _ in VISUAL_PAGES)}")
    return True


def capture_visual_only(output_dir):
    """Capture screenshots only (no comparison). For CI use.

    Args:
        output_dir: Directory to save screenshots.
    """
    print(f"\n=== CAPTURE SCREENSHOTS TO {output_dir} ===\n")

    if not _check_playwright():
        print("FAIL: Playwright not installed.")
        print("   Install with: pip install playwright && playwright install chromium")
        return False

    if not start_server():
        return False

    try:
        capture_visual_screenshots(output_dir, intercept_production=True)
    except Exception as e:
        stop_server()
        print(f"FAIL: Screenshot capture failed: {e}")
        return False

    stop_server()
    print(f"\nPASS: Screenshots saved to {output_dir}/")
    return True


def compare_visual_only(before_dir, after_dir, context="Before vs After"):
    """Compare two screenshot directories only (no capture). For CI use.

    Args:
        before_dir: Directory containing 'before' screenshots.
        after_dir: Directory containing 'after' screenshots.
        context: Label describing what is being compared.
    """
    print(f"\n=== COMPARE SCREENSHOTS: {before_dir} vs {after_dir} ===\n")

    results = compare_visual_screenshots(before_dir, after_dir)
    generate_visual_report(results, before_dir=before_dir, after_dir=after_dir,
                           context=context)
    print_visual_conclusion(results, context=context)

    failed = sum(1 for r in results.values() if r['status'] == 'diff')
    return failed == 0


def capture_live_screenshots(output_dir, live_url=None):
    """Capture screenshots from the live production site.

    Args:
        output_dir: Directory to save screenshots.
        live_url: Live site base URL (default: LIVE_URL).

    Returns:
        Dict mapping page name to screenshot file path.
    """
    if live_url is None:
        live_url = LIVE_URL
    return capture_visual_screenshots(output_dir, base_url=live_url,
                                      intercept_production=False,
                                      goto_timeout=45000)


def capture_live_only(output_dir, live_url=None):
    """Capture live site screenshots only (no comparison). For CI use.

    Args:
        output_dir: Directory to save screenshots.
        live_url: Live site base URL (default: LIVE_URL).
    """
    if live_url is None:
        live_url = LIVE_URL

    print(f"\n=== CAPTURE LIVE SCREENSHOTS TO {output_dir} ===\n")
    print(f"  Source: {live_url}")

    if not _check_playwright():
        print("FAIL: Playwright not installed.")
        print("   Install with: pip install playwright && playwright install chromium")
        return False

    # Verify live site is reachable
    try:
        resp = requests.get(live_url, timeout=15)
        if resp.status_code != 200:
            print(f"FAIL: Live site returned status {resp.status_code}")
            return False
        print(f"✅ Live site is reachable ({live_url})")
    except Exception as e:
        print(f"FAIL: Cannot reach live site {live_url}: {e}")
        return False

    try:
        capture_live_screenshots(output_dir, live_url)
    except Exception as e:
        print(f"FAIL: Live screenshot capture failed: {e}")
        return False

    print(f"\nPASS: Live screenshots saved to {output_dir}/")
    return True


def test_visual_live_comparison(live_url=None):
    """Compare live production site screenshots against local build screenshots.

    BEFORE = live site (https://www.datarush.nl) — currently deployed production
    AFTER  = local build (latest commit) — with production URL interception
             so local screenshots have full styling

    Generates diff images, HTML report, JSON report, and prints a conclusion.

    Requires: playwright (pip install playwright && playwright install chromium)
    """
    print("\n=== LIVE vs LOCAL VISUAL COMPARISON ===\n")

    if not _check_playwright():
        print("SKIP: Playwright not installed.")
        print("   Install with: pip install playwright && playwright install chromium")
        return True

    if live_url is None:
        live_url = LIVE_URL

    before_dir = VISUAL_CONFIG['before_dir']
    after_dir = VISUAL_CONFIG['after_dir']
    context = f"Live ({live_url}) vs Local (latest commit)"

    # Step 1: Capture live site screenshots (BEFORE = production)
    print(f"Step 1: Capturing live site screenshots from {live_url}...")
    print(f"  -> {before_dir}/")
    try:
        resp = requests.get(live_url, timeout=15)
        if resp.status_code != 200:
            print(f"SKIP: Live site returned status {resp.status_code}")
            return True
    except Exception as e:
        print(f"SKIP: Cannot reach live site {live_url}: {e}")
        return True

    try:
        capture_live_screenshots(before_dir, live_url)
    except Exception as e:
        print(f"FAIL: Live screenshot capture failed: {e}")
        return False

    # Step 2: Capture local build screenshots (AFTER = latest commit)
    print(f"\nStep 2: Capturing local build screenshots (styled via interception)...")
    print(f"  -> {after_dir}/")
    if not start_server():
        return False

    try:
        capture_visual_screenshots(after_dir, intercept_production=True)
    except Exception as e:
        stop_server()
        print(f"FAIL: Local screenshot capture failed: {e}")
        return False

    stop_server()

    # Step 3: Compare
    print(f"\nStep 3: Comparing live ({before_dir}) vs local ({after_dir})...")
    results = compare_visual_screenshots(before_dir, after_dir)

    # Step 4: Generate reports
    print("\nStep 4: Generating reports...")
    generate_visual_report(results, before_dir=before_dir, after_dir=after_dir,
                           context=context)

    # Step 5: Print conclusion
    print_visual_conclusion(results, context=context)

    failed = sum(1 for r in results.values() if r['status'] == 'diff')
    return failed == 0


def test_interaction():
    """Run browser interaction tests."""
    print("\n=== INTERACTION TESTS ===\n")
    print("⚠️  Interaction tests require Chrome and chromedriver")
    print("   Install with: sudo apt-get install -y chromium chromedriver")
    print("   Skipping interaction tests")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n=== DEPENDENCY CHECK ===\n")
    
    missing = []
    
    # Check Hugo
    try:
        result = subprocess.run(['hugo', 'version'], capture_output=True, text=True)
        if result.returncode != 0:
            missing.append('Hugo (extended version)')
        else:
            print(f"✅ Hugo: {result.stdout.strip().split()[-1]}")
    except FileNotFoundError:
        missing.append('Hugo (extended version)')
    
    # Check Dart Sass (optional — Hugo extended has built-in Dart Sass)
    try:
        result = subprocess.run(['sass', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("ℹ️  Dart Sass CLI: not found (optional, Hugo extended has built-in support)")
        else:
            print(f"✅ Dart Sass: installed")
    except FileNotFoundError:
        print("ℹ️  Dart Sass CLI: not found (optional, Hugo extended has built-in support)")
    
    # Check Python packages (import name may differ from pip name)
    python_packages = [('requests', 'requests'), ('beautifulsoup4', 'bs4'), ('pillow', 'PIL')]
    for pip_name, import_name in python_packages:
        try:
            subprocess.run([sys.executable, '-c', f'import {import_name}'],
                          capture_output=True, check=True)
            print(f"✅ Python package: {pip_name}")
        except:
            missing.append(f'Python package: {pip_name}')

    # Check Playwright (optional — for visual regression tests)
    try:
        subprocess.run([sys.executable, '-c', 'from playwright.sync_api import sync_playwright'],
                      capture_output=True, check=True)
        print("✅ Python package: playwright")
    except:
        print("ℹ️  Python package: playwright (optional, for visual regression tests)")
        print("   Install with: pip install playwright && playwright install chromium")
    
    if missing:
        print("\n⚠️  Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print("\n📦 Install Python dependencies with: pip install requests beautifulsoup4 pillow")
        print("📦 Install Dart Sass: brew install sass/sass/sass")
        print("📦 Install Hugo: brew install hugo")
        return False
    
    print("\n✅ All dependencies are installed")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Run local integration tests for datarush.nl'
    )
    parser.add_argument('--build', action='store_true',
                        help='Build the site')
    parser.add_argument('--render', action='store_true',
                        help='Run page rendering tests')
    parser.add_argument('--links', action='store_true',
                        help='Run link validation tests')
    parser.add_argument('--seo', action='store_true',
                        help='Run SEO validation tests')
    parser.add_argument('--rss', action='store_true',
                        help='Run RSS feed validation tests')
    parser.add_argument('--titles', action='store_true',
                        help='Run page title validation tests')
    parser.add_argument('--author-meta', action='store_true',
                        help='Run author meta tag validation tests')
    parser.add_argument('--robots', action='store_true',
                        help='Run robots.txt consistency tests')
    parser.add_argument('--frontmatter', action='store_true',
                        help='Run front matter validation tests')
    parser.add_argument('--build-warnings', action='store_true',
                        help='Run build warning tests')
    parser.add_argument('--visual', action='store_true',
                        help='Run visual regression tests (compare against baseline)')
    parser.add_argument('--visual-baseline', action='store_true',
                        help='Save current build screenshots as visual baseline')
    parser.add_argument('--visual-capture', type=str, metavar='DIR',
                        help='Capture screenshots only to specified directory (CI use)')
    parser.add_argument('--visual-compare', nargs=2, metavar=('BEFORE_DIR', 'AFTER_DIR'),
                        help='Compare two screenshot directories only (CI use)')
    parser.add_argument('--visual-live', action='store_true',
                        help='Compare live site (datarush.nl) vs local build screenshots')
    parser.add_argument('--visual-live-capture', type=str, metavar='DIR',
                        help='Capture live site screenshots only to specified directory (CI use)')
    parser.add_argument('--live-url', type=str, default=LIVE_URL,
                        help=f'Live site URL for --visual-live (default: {LIVE_URL})')
    parser.add_argument('--interaction', action='store_true',
                        help='Run interaction tests')
    parser.add_argument('--all', action='store_true',
                        help='Run all tests (default)')
    parser.add_argument('--check-deps', action='store_true',
                        help='Check dependencies only')
    parser.add_argument('--no-build', action='store_true',
                        help='Skip the initial Hugo build (use existing public/ directory)')

    args = parser.parse_args()

    # Handle standalone visual commands (no build/test pipeline needed)
    if args.visual_capture:
        success = capture_visual_only(args.visual_capture)
        sys.exit(0 if success else 1)

    if args.visual_live_capture:
        success = capture_live_only(args.visual_live_capture, args.live_url)
        sys.exit(0 if success else 1)

    if args.visual_compare:
        success = compare_visual_only(args.visual_compare[0], args.visual_compare[1])
        sys.exit(0 if success else 1)

    # If no specific tests selected, run all
    server_tests = [args.build, args.render, args.links, args.seo,
                    args.rss, args.titles, args.author_meta, args.robots]
    file_tests = [args.frontmatter, args.build_warnings]
    if not any(server_tests + file_tests + [
            args.visual, args.visual_baseline, args.visual_live,
            args.interaction, args.check_deps, args.all]):
        args.all = True

    # Check dependencies first
    if args.check_deps or args.all:
        if not check_dependencies():
            print("\n❌ Dependency check failed. Install missing dependencies and try again.")
            sys.exit(1)

    # Build site if requested or if any server-based test is requested
    needs_build = (args.build or args.all or args.render or args.links
                   or args.seo or args.rss or args.titles or args.author_meta
                   or args.robots or args.build_warnings
                   or args.visual or args.visual_baseline or args.visual_live)
    if needs_build and not args.no_build:
        if not build_site():
            print("\n❌ Build failed. Cannot run tests without a successful build.")
            sys.exit(1)

    # Handle visual baseline save (standalone, after build)
    if args.visual_baseline:
        if not save_visual_baseline():
            sys.exit(1)
        # If only baseline was requested, exit
        if not any(server_tests + file_tests + [
                args.visual, args.visual_live, args.interaction, args.all]):
            print("\n🎉 Baseline saved successfully!")
            sys.exit(0)

    # Run tests
    all_passed = True

    if args.render or args.all:
        if not test_page_rendering():
            all_passed = False

    if args.links or args.all:
        if not test_link_validation():
            all_passed = False

    if args.seo or args.all:
        if not test_seo_validation():
            all_passed = False

    if args.rss or args.all:
        if not test_rss_feed():
            all_passed = False

    if args.titles or args.all:
        if not test_page_titles():
            all_passed = False

    if args.author_meta or args.all:
        if not test_author_meta():
            all_passed = False

    if args.robots or args.all:
        if not test_robots_txt():
            all_passed = False

    if args.frontmatter or args.all:
        if not test_front_matter():
            all_passed = False

    if args.build_warnings or args.all:
        if not test_build_warnings():
            all_passed = False

    if args.visual or args.all:
        if not test_visual_regression():
            all_passed = False

    if args.visual_live or args.all:
        if not test_visual_live_comparison(live_url=args.live_url):
            all_passed = False

    if args.interaction or args.all:
        if not test_interaction():
            all_passed = False
    
    # Clean up
    stop_server()
    
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == '__main__':
    main()

# Makefile for datarush.nl - Local Development and Testing
# Dwight (dwight-mta2nxwe) - Local integration test setup

.PHONY: help build serve test test-all test-render test-links test-seo test-rss test-titles test-author-meta test-robots test-frontmatter test-build-warnings test-visual test-visual-live visual-baseline visual-live-capture check-deps clean

# Default target
help:
	@echo "datarush.nl - Local Development Makefile"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Available targets:"
	@echo "  build             - Build the Hugo site"
	@echo "  serve             - Start Hugo development server"
	@echo "  test              - Run all integration tests"
	@echo "  test-all          - Alias for test"
	@echo "  test-render       - Run page rendering tests"
	@echo "  test-links        - Run link validation tests"
	@echo "  test-seo          - Run SEO validation tests"
	@echo "  test-rss          - Run RSS feed validation tests"
	@echo "  test-titles       - Run page title validation tests"
	@echo "  test-author-meta  - Run author meta tag validation tests"
	@echo "  test-robots       - Run robots.txt consistency tests"
	@echo "  test-frontmatter  - Run front matter validation tests"
	@echo "  test-build-warnings - Run build warning tests"
	@echo "  test-visual       - Run visual regression tests (compare vs baseline)"
	@echo "  test-visual-live  - Compare live site (datarush.nl) vs local build"
	@echo "  visual-baseline   - Save current build as visual baseline"
	@echo "  visual-live-capture - Capture live site screenshots only (CI use)"
	@echo "  check-deps        - Check if all dependencies are installed"
	@echo "  clean             - Remove public directory"
	@echo ""
	@echo " See TESTING.md for more details"

# Build the site
build:
	hugo --minify --cleanDestinationDir

# Start development server
serve:
	hugo server -D -p 1313

# Run all tests
test: test-all

test-all:
	python test.py --all

# Run page rendering tests
test-render:
	python test.py --render

# Run link validation tests
test-links:
	python test.py --links

# Run SEO validation tests
test-seo:
	python test.py --seo

# Run RSS feed validation tests
test-rss:
	python test.py --rss

# Run page title validation tests
test-titles:
	python test.py --titles

# Run author meta tag validation tests
test-author-meta:
	python test.py --author-meta

# Run robots.txt consistency tests
test-robots:
	python test.py --robots

# Run front matter validation tests
test-frontmatter:
	python test.py --frontmatter

# Run build warning tests
test-build-warnings:
	python test.py --build-warnings

# Run visual regression tests (compare against baseline)
test-visual:
	python test.py --visual

# Compare live site (production) vs local build screenshots
test-visual-live:
	python test.py --visual-live

# Save current build screenshots as visual baseline
visual-baseline:
	python test.py --visual-baseline

# Capture live site screenshots only (CI use)
visual-live-capture:
	python test.py --visual-live-capture screenshots/before

# Check dependencies
check-deps:
	python test.py --check-deps

# Clean build artifacts
clean:
	rm -rf public/

# Install dependencies
install:
	pip install -r requirements.txt

# Build and test in one command
build-and-test: build test

# Run with specific Python version
PYTHON?=python3

# Phony targets
.PHONY: build serve test test-all test-render test-links test-seo test-rss test-titles test-author-meta test-robots test-frontmatter test-build-warnings test-visual test-visual-live visual-baseline visual-live-capture check-deps clean install build-and-test

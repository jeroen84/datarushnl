# Datarush.nl Website

Welcome to the repository of the [datarush.nl](https://www.datarush.nl) website. This site provides data-driven solutions for the financial sector, specializing in business intelligence, dashboard development, and data science services.

## Overview

- **Framework**: [Hugo](https://gohugo.io) static site generator (v0.168.0)
- **Theme**: [Anatole](https://github.com/lxndrcom/anatole)
- **Deployment**: Automatic via GitHub Actions on push to `master`
- **Hosting**: FTP upload to production server

## Site Structure

The site is organized with the following content structure:

```
content/
├── _index.md          # Homepage
├── about/
│   └── index.md       # About page
├── post/
│   ├── _index.md      # Blog post listing
│   └── *.md           # Individual blog posts
├── author/
│   ├── _index.md      # All authors listing
│   └── jeroen-van-de-erve/
│       └── _index.md  # Jeroen's author page
├── categories/
│   └── _index.md      # Category listing
└── tags/
    └── _index.md       # Tag listing
```

### Taxonomies

The site uses three custom taxonomies configured in `config.toml`:

- **author**: Organizes posts by author (e.g., `/author/jeroen-van-de-erve/`)
- **tag**: Tags for individual posts (e.g., `/tags/powerbi/`)
- **category**: Broader categories for posts (e.g., `/categories/business-intelligence/`)

## Recent Improvements

### Google Search Console SEO Fixes (2026-08-26)

A comprehensive SEO audit was performed using Google Search Console data. The following issues were identified and fixed:

#### ✅ Fixed Issues

1. **404 Errors (2 pages)**
   - `/author` and `/author/jeroen-van-de-erve` returned 404
   - **Fix**: Configured Hugo taxonomies and created author pages
   - **Files**: `config.toml`, `content/author/_index.md`, `content/author/jeroen-van-de-erve/_index.md`

2. **Redirect Chains (7+ pages)**
   - URLs without trailing slashes redirected to trailing slash versions
   - **Fix**: Added `.htaccess` rules to enforce trailing slashes
   - **File**: `static/.htaccess`

3. **Dashboard Subdomain Redirects**
   - `dashboards.datarush.nl/demo1` and `/pensioendashboard` had incorrect redirects
   - **Fix**: Updated PHP redirect files to point to correct GitHub repositories
   - **Files**: `static/dashboard-demo1/index.php`, `static/pensioendashboard/index.php`

4. **Missing robots.txt**
   - No robots.txt file existed
   - **Fix**: Created `robots.txt` with proper directives and sitemap reference
   - **File**: `static/robots.txt`

5. **Hugo Version Inconsistency**
   - Local version (0.155.3) differed from CI/CD (0.165.0)
   - **Fix**: Documented version 0.165.0 in config.toml
   - **Files**: `config.toml`

#### ⚠️ Remaining Issues

1. **Domain Canonicalization**
   - Both `datarush.nl` and `www.datarush.nl` serve identical content
   - **Todo**: Implement 301 redirect from non-www to www via Cloudflare or server config

2. **Not Indexed Pages (9 pages)**
   - Tag pages are crawled but not indexed by Google
   - **Fix Applied**: Added `noindex = true` to tag and category taxonomy pages
   - **Files**: `content/tags/_index.md`, `content/categories/_index.md`

## Development

### Prerequisites

- [Hugo v0.168.0](https://gohugo.io) (extended version)
- [Dart Sass](https://sass-lang.com/install) (for theme compilation)
- Git

### Local Development

```bash
# Clone the repository
git clone git@github.com:jeroen84/datarushnl.git
cd datarushnl

# Initialize submodules (theme)
git submodule update --init --recursive

# Start local server (with live reload)
hugo server -D

# The site will be available at http://localhost:1313
```

### Creating New Content

```bash
# Create a new blog post
hugo new post/my-new-post.md

# Create a new author page
hugo new author/jane-doe/_index.md
```

New posts should include the following front matter:

```yaml
---
title: "Post Title"
date: 2026-08-26
draft: false
author: "Jeroen van de Erve"
tags: ["tag1", "tag2"]
categories: ["category1"]
description: "Post description for SEO"
---
```

## Preview Environment

Every commit pushed to any branch (except `master`) automatically generates a preview deployment, allowing you to test changes in a browser before merging.

### How it Works

- **Trigger**: Push to any branch (except `master`) or open a Pull Request
- **Preview URL**: 
  - For branches: `https://www.datarush.nl/preview/<branch-name>/`
  - For PRs: `https://www.datarush.nl/preview/pr-<pr-number>/`
- **Automatic PR comments**: When you open a PR, a comment with the preview URL is automatically added

### Usage

```bash
# Create and checkout a feature branch
git checkout -b my-feature-branch

# Make your changes and commit
git add .
git commit -m "Add new feature"
git push origin my-feature-branch

# Your preview will be available at:
# https://www.datarush.nl/preview/my-feature-branch/
```

**Workflow file**: `.github/workflows/preview.yml`

### Staging Environment

Pushes to the `master` branch trigger a staging deployment:
- **URL**: `https://www.datarush.nl/staging/`
- **Workflow file**: `.github/workflows/staging.yml`

## CI/CD Pipeline

### Production Deployment

The site is automatically built and deployed to staging on every push to the `master` branch. Production deployment requires manual confirmation.

**Workflow file**: `.github/workflows/deploy.yml`

**Steps**:
1. Checkout code with submodules
2. Install Dart Sass via Homebrew
3. Install Hugo v0.168.0 (extended)
4. Build the site with `hugo`
5. Install lftp
6. Upload to FTP server via SFTP

### Manual Deployment

If needed, you can manually deploy using the provided script:

```bash
# Make sure the script is executable
chmod +x deploy-ftp

# Run the deployment script
./deploy-ftp
```

## SEO Best Practices

### Taxonomy Pages

- Tag and category pages have `noindex = true` to prevent thin content from being indexed
- Author pages are indexable and include biographical information

### robots.txt

The site has a properly configured robots.txt at `static/robots.txt`:
- Allows all content except `/author/` paths
- Includes sitemap reference: `https://www.datarush.nl/sitemap.xml`

### URL Structure

- All URLs enforce trailing slashes (via `.htaccess`)
- HTTPS is enforced (via `.htaccess`)
- Canonical URLs are generated automatically by Hugo

## Project Resources

- [Hugo Documentation](https://gohugo.io/documentation/)
- [Anatole Theme Documentation](https://github.com/lxndrcom/anatole)
- [Google Search Console](https://search.google.com/search-console)

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository** and create a feature branch
2. **Make your changes** with appropriate commit messages
3. **Test locally** with `hugo server -D`
4. **Submit a pull request** with a clear description of changes

For major changes, please open an issue first to discuss the proposed changes.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Contact

For questions or inquiries, please contact:

- **Email**: [jeroen@datarush.nl](mailto:jeroen@datarush.nl)
- **LinkedIn**: [linkedin.com/in/jeroen-van-de-erve](https://www.linkedin.com/in/jeroen-van-de-erve/)
- **GitHub**: [github.com/jeroen84](https://github.com/jeroen84/)
- **Website**: [datarush.nl](https://www.datarush.nl)


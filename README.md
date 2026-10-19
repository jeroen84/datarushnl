# Datarush.nl Website

Welcome to the repository of the [datarush.nl](https://www.datarush.nl) website. This site provides data-driven solutions for the financial sector, specializing in business intelligence, dashboard development, and data science services.

## Overview

- **Framework**: [Hugo](https://gohugo.io) static site generator (v0.168.0)
- **Theme**: [Anatole](https://github.com/lxndrcom/anatole)
- **Deployment**: Automatic via GitHub Actions on push to `master`
- **Hosting**: FTP upload to production server

## Site Structure

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

## Development

### Prerequisites

- [Hugo v0.168.0](https://gohugo.io) (extended version)
- [Dart Sass](https://sass-lang.com/install) (for theme compilation)
- Git

### Local Development

```bash
git clone git@github.com:jeroen84/datarushnl.git
cd datarushnl
git submodule update --init --recursive
hugo server -D  # Site at http://localhost:1313
```

### Creating New Content

```bash
hugo new post/my-new-post.md
hugo new author/jane-doe/_index.md
```

New posts should include front matter:

```yaml
---
title: "Post Title"
date: 2026-08-26
draft: false
author: "Jeroen van de Erve"
tags: ["tag1", "tag2"]
categories: ["category1"]
description: "Post description"
---
```

## Deployment

The site builds and deploys automatically via GitHub Actions on push to `master`.
Preview deployments are available for feature branches at `https://www.datarush.nl/preview/<branch-name>/`.

- **Production**: `.github/workflows/deploy.yml`
- **Staging**: `.github/workflows/staging.yml`
- **Preview**: `.github/workflows/preview.yml`

## Project Resources

- [Hugo Documentation](https://gohugo.io/documentation/)
- [Anatole Theme Documentation](https://github.com/lxndrcom/anatole)

## Contributing

1. **Fork** the repository and create a feature branch
2. **Make** your changes with appropriate commit messages
3. **Test** locally with `hugo server -D`
4. **Submit** a pull request with a clear description

For major changes, please open an issue first.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contact

- **Email**: [jeroen@datarush.nl](mailto:jeroen@datarush.nl)
- **LinkedIn**: [linkedin.com/in/jeroen-van-de-erve](https://www.linkedin.com/in/jeroen-van-de-erve/)
- **GitHub**: [github.com/jeroen84](https://github.com/jeroen84/)
- **Website**: [datarush.nl](https://www.datarush.nl)

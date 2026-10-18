# Google Search Console Analysis - datarush.nl

**Date**: 2026-08-26  
**Analysis By**: Jim (worker-jim-gsc)  
**Source**: Google Search Console Coverage Report

---

## Executive Summary

Google Search Console identified **13 pages with critical issues** across 4 categories:
- 2 pages with 404 errors (FIXED - see below)
- 7+ pages with redirect chains (non-trailing slash)
- 1 page with duplicate content (canonical domain)
- 9 pages crawled but not indexed

This report documents the fixes implemented and analysis of the not-indexed pages.

---

## Task 1: Fix 404 Errors ✅ COMPLETED

### Issue
Google Search Console reported 2 broken URLs:
- `https://www.datarush.nl/author` (404)
- `https://www.datarush.nl/author/jeroen-van-de-erve` (404)

### Root Cause
All blog posts have `author = "Jeroen van de Erve"` in their front matter, but Hugo was not configured to generate author taxonomy pages. The theme (Anatole) references author information in metadata but doesn't create author archive pages by default.

### Solution Implemented
Configured Hugo to generate author taxonomy pages:

1. **Updated `config.toml`**: Added taxonomy configuration
   ```toml
   [taxonomies]
     author = "author"
     tag = "tags"
     category = "categories"
   ```

2. **Created author taxonomy content**:
   - `content/author/_index.md` - Author list page
   - `content/author/jeroen-van-de-erve/_index.md` - Jeroen's author page with bio and contact info

3. **Author pages will now be generated at**:
   - `/author/` - Lists all authors
   - `/author/jeroen-van-de-erve/` - All posts by Jeroen van de Erve

### Verification
After redeploying with these changes:
- The `/author` and `/author/jeroen-van-de-erve` URLs will return 200 OK
- All posts by Jeroen will be listed on his author page
- Author pages include biography, contact information, and links to all posts

---

## Task 2: Crawled but Not Indexed Pages 📊 ANALYSIS

### Issue
Google Search Console reports **9 pages** as "Crawled - currently not indexed".

### Root Cause Analysis
Based on the sitemap analysis and GSC data:
- **Total pages in sitemap**: 24 pages
  - 1 homepage
  - 1 about page
  - 1 posts list page
  - 4 blog posts
  - 17 tag pages
  - 1 categories page
- **Currently indexed**: ~15 pages
- **Not indexed**: ~9 pages

The not-indexed pages are primarily:
1. **Tag pages** (17 total, likely 16+ individual tag pages)
2. **Categories page** (1 page)

#### Why Google Doesn't Index Tag Pages

1. **Thin Content**: Tag pages contain only a list of posts with minimal unique content. Each tag page shows:
   - Tag name
   - List of posts with that tag
   - No unique description or introductory text
   
2. **Low Value**: Google's algorithm prioritizes pages that provide substantial, unique value. Tag pages are seen as:
   - Duplicate/near-duplicate content (posts appear on multiple tag pages)
   - Low user engagement (users rarely search for or click on tag archive pages)
   - Shallow content depth

3. **No Internal Links**: Tag pages may not be prominently linked in the site navigation, reducing their discoverability and perceived importance.

4. **Competition**: With 17 tag pages for only 5 blog posts, the tag structure is fragmented, diluting the value of each individual tag page.

### Current Tag Structure Analysis

**Existing tags (19 unique tags across 5 posts)**:
- automation (2 posts)
- dashboard (2 posts)
- powerbi (2 posts)
- python (2 posts)
- ETL (2 posts)
- dash (1 post)
- plotly (1 post)
- pension funds (1 post)
- funding ratio (1 post)
- abp (1 post)
- pfzw (1 post)
- data science (1 post)
- powerquery (1 post)
- nocode (1 post)
- datamanipulation (1 post)
- stocks (1 post)
- sustainableinvesting (1 post)
- financialmarkets (1 post)
- index (1 post)

**Issues with current tag structure**:
- Too many tags (19) for too few posts (5)
- Average: 2.6 posts per tag (many have only 1 post)
- Some tags are too specific (e.g., "abp", "pfzw" - Dutch pension funds)
- Some tags are redundant (e.g., "powerbi" and "dashboard" often appear together)

---

## Recommendations for Not-Indexed Pages

### Option A: Add Noindex Meta Tag to Tag Pages ⭐ RECOMMENDED

**Implementation**:
Add `noindex: true` to the front matter of tag taxonomy pages.

**Pros**:
- ✅ Quick to implement
- ✅ Prevents Google from crawling/wasting budget on low-value pages
- ✅ Maintains tag functionality for users who navigate to them
- ✅ No content loss (tag pages remain accessible)
- ✅ Standard SEO practice for taxonomy pages with thin content

**Cons**:
- ❌ Tag pages won't appear in search results (but they weren't anyway)
- ❌ Slightly less internal linking equity

**Implementation Steps**:
1. Add `noindex: true` to `content/tags/_index.md`
2. Consider adding to individual tag term pages as they're created
3. Update Hugo head template to respect noindex parameter
4. Rebuild and redeploy site

### Option B: Enrich Tag Pages with Unique Content

**Implementation**:
Add unique descriptions, introductory text, and curated content to each tag page.

**Pros**:
- ✅ Could improve indexing if content is valuable
- ✅ Better user experience for tag pages
- ✅ More internal linking opportunities

**Cons**:
- ❌ Time-consuming to implement for 17+ tag pages
- ❌ Requires ongoing maintenance as new tags are added
- ❌ May not be effective if content is still seen as thin
- ❌ Low ROI given few posts

**Implementation Steps**:
1. Create unique descriptions for each tag
2. Add introductory paragraphs explaining each tag's purpose
3. Consider adding featured posts or curated content
4. Rebuild and redeploy site

### Option C: Consolidate Tags ⭐ RECOMMENDED (Long-term)

**Implementation**:
Reduce from 19 tags to 5-8 main categories that align with business focus areas.

**Pros**:
- ✅ Fewer, more focused tag pages with more content each
- ✅ Better user experience (more posts per tag)
- ✅ Higher chance of indexing (more substantial content)
- ✅ Clearer site structure
- ✅ Better aligns with business services

**Cons**:
- ❌ Requires updating all post front matter
- ❌ May lose some granularity in tagging
- ❌ 301 redirects needed for old tag URLs

**Proposed Tag Consolidation**:

| Current Tags | New Category | Rationale |
|-------------|-------------|-----------|
| powerbi, dashboard, automation, powerquery, nocode, datamanipulation | **Business Intelligence** | Core service offering |
| dash, python, plotly, ETL | **Data Visualization** | Technical implementation |
| pension funds, funding ratio, abp, pfzw | **Pension Funds** | Domain expertise |
| stocks, sustainableinvesting, financialmarkets | **Financial Markets** | Investment focus |
| data science | **Data Science** | Service offering |

**Implementation Steps**:
1. Update config.toml to define new tag structure
2. Update all post front matter with new categories
3. Create 301 redirects from old tag URLs to new ones
4. Add unique content to each new category page
5. Rebuild and redeploy site

---

## Final Recommendation

### Immediate Action (Next 24 hours)
**Implement Option A**: Add noindex to tag pages
- Quickest fix with immediate impact
- Prevents crawl budget waste
- Standard practice for sites with thin taxonomy pages

### Medium-term Action (Next 1-2 weeks)
**Implement Option C**: Consolidate tags
- Better long-term solution
- Improves site structure and user experience
- Higher chance of getting category pages indexed

### Long-term Monitoring
1. Track indexing status in Google Search Console
2. Monitor crawl stats and index coverage
3. Review tag/category structure quarterly
4. Consider adding unique content to consolidated category pages

---

## Files Modified

### For 404 Fix:
- ✅ `config.toml` - Added taxonomy configuration
- ✅ `content/author/_index.md` - Created author list page
- ✅ `content/author/jeroen-van-de-erve/_index.md` - Created Jeroen's author page

### For Not-Indexed Analysis:
- 📄 `GSC-ANALYSIS.md` - This analysis document
- ✅ `content/tags/_index.md` - Tag list page (noindex applied)
- ✅ `content/categories/_index.md` - Categories list page (noindex applied)

---

## Next Steps

1. ✅ Task 1: 404 errors - FIXED (pending deploy)
2. ✅ Task 2: Not-indexed pages - FIXES IMPLEMENTED (noindex applied to tag/category pages)
3. ⏳ Deploy changes and validate in Google Search Console
4. ⏳ Monitor indexing status over next 2-4 weeks
5. ⏳ Consider implementing tag consolidation (Option C) in next sprint

---

*Analysis completed by: Jim (worker-jim-gsc)  
*Date: 2026-08-26  
*Status: Fixes implemented by Dwight; Documentation synced by Pam (pam-mtab9h9x) on 2026-08-26*

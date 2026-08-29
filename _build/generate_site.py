#!/usr/bin/env python3
"""Rebuild BudhiWorks static site: 25 practical articles + utility pages."""

from __future__ import annotations

import html
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTICLES_DIR = ROOT / "articles"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from articles_batch_a import ARTICLES as A  # noqa: E402
from articles_batch_b import ARTICLES as B  # noqa: E402
from articles_batch_c import ARTICLES as C  # noqa: E402

ARTICLES = sorted(A + B + C, key=lambda x: x["date"], reverse=True)

AUTHOR = {
    "name": "Ram",
    "role": "Founder & Editor, BudhiWorks",
    "bio": (
        "I build and ship production web apps — Node, React/Next.js, Postgres, and "
        "the boring infrastructure that keeps them online. BudhiWorks is where I "
        "publish the guides I wish I had when something broke at 2 a.m."
    ),
    "email": "contact@budhiworks.com",
    "initials": "RM",
}

SITE = "https://budhiworks.com"
ADSENSE = (
    '  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
    '?client=ca-pub-5099209873544602"\n     crossorigin="anonymous"></script>\n'
)


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def fmt_date(iso: str) -> str:
    return datetime.strptime(iso, "%Y-%m-%d").strftime("%B %-d, %Y")


def nav(active: str, prefix: str = "") -> str:
    items = [
        ("index.html", "Home", "home"),
        ("start-here.html", "Start here", "start"),
        ("resources.html", "Resources", "resources"),
        ("about.html", "About", "about"),
        ("contact.html", "Contact", "contact"),
    ]
    links = []
    for href, label, key in items:
        cls = ' class="nav-link active"' if key == active else ' class="nav-link"'
        links.append(f'<li><a href="{prefix}{href}"{cls}>{label}</a></li>')
    return "\n          ".join(links)


def header(active: str, prefix: str = "") -> str:
    home = f"{prefix}index.html"
    return f"""  <header class="site-header">
    <div class="container navbar">
      <a href="{home}" class="brand-logo">
        <span class="logo-icon">B</span>
        <span>Budhi<span class="gradient-text">Works</span></span>
      </a>
      <nav>
        <ul class="nav-links" id="navLinks">
          {nav(active, prefix)}
        </ul>
      </nav>
      <div class="header-actions">
        <button class="theme-toggle-btn" id="themeToggleBtn" aria-label="Toggle Dark/Light Mode">☀️</button>
        <button class="mobile-nav-toggle" id="mobileNavToggle" aria-label="Toggle Navigation Menu">☰</button>
      </div>
    </div>
  </header>"""


def footer(prefix: str = "") -> str:
    return f"""  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <a href="{prefix}index.html" class="brand-logo">
            <span class="logo-icon">B</span>
            <span>Budhi<span class="gradient-text">Works</span></span>
          </a>
          <p>Practical guides for building, shipping, and debugging modern web systems — written from production experience, not theory dumps.</p>
        </div>
        <div>
          <h4>Explore</h4>
          <ul>
            <li><a href="{prefix}index.html#articles">All articles</a></li>
            <li><a href="{prefix}start-here.html">Start here</a></li>
            <li><a href="{prefix}resources.html">Resources</a></li>
            <li><a href="{prefix}author.html">Author</a></li>
          </ul>
        </div>
        <div>
          <h4>Site</h4>
          <ul>
            <li><a href="{prefix}about.html">About</a></li>
            <li><a href="{prefix}editorial-policy.html">Editorial policy</a></li>
            <li><a href="{prefix}contact.html">Contact</a></li>
            <li><a href="{prefix}privacy.html">Privacy</a></li>
            <li><a href="{prefix}terms.html">Terms</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p>&copy; 2026 BudhiWorks. Written by {esc(AUTHOR["name"])}.</p>
      </div>
    </div>
  </footer>"""


def shell(title: str, description: str, canonical: str, active: str, body: str, prefix: str = "", extra_head: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{esc(canonical)}">
  <meta name="color-scheme" content="dark light">
  <meta name="author" content="{esc(AUTHOR["name"])}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(canonical)}">
  <meta property="og:site_name" content="BudhiWorks">
{extra_head}  <link rel="stylesheet" href="{prefix}style.css">
  <script src="{prefix}script.js" defer></script>
{ADSENSE}</head>
<body>
  <div class="bg-glow-container">
    <div class="bg-glow-1"></div>
    <div class="bg-glow-2"></div>
  </div>
{header(active, prefix)}
{body}
{footer(prefix)}
</body>
</html>
"""


def render_section(sec: dict) -> str:
    parts = [f"          <h2>{esc(sec['h2'])}</h2>"]
    for p in sec.get("paragraphs", []):
        parts.append(f"          <p>{esc(p)}</p>")
    if sec.get("bullets"):
        parts.append("          <ul>")
        for b in sec["bullets"]:
            parts.append(f"            <li>{esc(b)}</li>")
        parts.append("          </ul>")
    if sec.get("code"):
        code = esc(sec["code"])
        parts.append(f"          <pre><code>{code}</code></pre>")
    return "\n".join(parts)


def word_count(article: dict) -> int:
    n = 0
    for s in article["sections"]:
        n += sum(len(p.split()) for p in s.get("paragraphs", []))
        n += sum(len(b.split()) for b in s.get("bullets", []) or [])
        if s.get("code"):
            n += max(1, len(s["code"].split()) // 3)
    n += sum(len(t.split()) for t in article["takeaways"])
    n += len(article["excerpt"].split())
    return n


def write_article(article: dict, index: int) -> None:
    words = word_count(article)
    read_min = article.get("read_min") or max(6, words // 180)
    date_iso = article["date"]
    date_human = fmt_date(date_iso)
    prev_a = ARTICLES[index + 1] if index + 1 < len(ARTICLES) else None
    next_a = ARTICLES[index - 1] if index > 0 else None

    sections_html = "\n\n".join(render_section(s) for s in article["sections"])
    takeaways = "\n".join(f"            <li>{esc(t)}</li>" for t in article["takeaways"])

    nav_prev = (
        f'<a href="{esc(prev_a["slug"])}.html" class="btn btn-secondary">&larr; {esc(prev_a["title"][:42])}…</a>'
        if prev_a
        else f'<a href="../index.html#articles" class="btn btn-secondary">&larr; All articles</a>'
    )
    nav_next = (
        f'<a href="{esc(next_a["slug"])}.html" class="btn btn-primary">Next: {esc(next_a["title"][:42])}… &rarr;</a>'
        if next_a
        else f'<a href="../start-here.html" class="btn btn-primary">Start here &rarr;</a>'
    )

    body = f"""  <main class="main-content">
    <div class="container article-container">
      <article class="content-page">
        <header class="article-header">
          <span class="badge badge-cyan">{esc(article["category"])}</span>
          <h1 class="article-title">{esc(article["title"])}</h1>
          <p class="article-lead">{esc(article["excerpt"])}</p>
          <div class="article-meta">
            <div class="author-avatar">{esc(AUTHOR["initials"])}</div>
            <div>
              <strong>By <a href="../author.html">{esc(AUTHOR["name"])}</a></strong><br>
              <time datetime="{esc(date_iso)}">{esc(date_human)}</time> &bull; {read_min} min read &bull; ~{words} words
            </div>
          </div>
        </header>

        <div class="quick-take-box">
          <h3>What you will learn</h3>
          <ul>
{takeaways}
          </ul>
        </div>

        <div class="article-body article-prose">
{sections_html}

          <h2>Key takeaways</h2>
          <ul>
{takeaways}
          </ul>

          <div class="info-card" style="margin-top:2rem;">
            <h3 style="margin-top:0;">About the author</h3>
            <p><strong>{esc(AUTHOR["name"])}</strong> — {esc(AUTHOR["role"])}. {esc(AUTHOR["bio"])}</p>
            <p><a href="../author.html">More about Ram</a> · <a href="../contact.html">Contact</a></p>
          </div>
        </div>
      </article>

      <div style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid var(--border-color); display: flex; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
        {nav_prev}
        {nav_next}
      </div>
    </div>
  </main>"""

    extra = (
        f'  <meta name="keywords" content="{esc(article["keywords"])}">\n'
        f'  <meta property="og:type" content="article">\n'
        f'  <meta property="article:published_time" content="{esc(date_iso)}">\n'
        f'  <meta property="article:author" content="{esc(AUTHOR["name"])}">\n'
    )
    page = shell(
        f'{article["title"]} — BudhiWorks',
        article["description"],
        f'{SITE}/articles/{article["slug"]}.html',
        "home",
        body,
        prefix="../",
        extra_head=extra,
    )
    (ARTICLES_DIR / f'{article["slug"]}.html').write_text(page, encoding="utf-8")


def write_index() -> None:
    cats = sorted({a["category"] for a in ARTICLES})
    filters = ['<button class="filter-btn active" type="button" data-filter="all">All (25)</button>']
    for c in cats:
        count = sum(1 for a in ARTICLES if a["category"] == c)
        filters.append(
            f'<button class="filter-btn" type="button" data-filter="{esc(c)}">{esc(c)} ({count})</button>'
        )

    cards = []
    for a in ARTICLES:
        cards.append(
            f"""      <article class="article-card" data-category="{esc(a["category"])}">
        <div class="card-top">
          <span class="badge">{esc(a["category"])}</span>
        </div>
        <h2 class="card-title"><a href="articles/{esc(a["slug"])}.html">{esc(a["title"])}</a></h2>
        <p class="card-excerpt">{esc(a["excerpt"])}</p>
        <div class="card-footer">
          <div class="card-meta">By {esc(AUTHOR["name"])} • {esc(fmt_date(a["date"]))} • {a["read_min"]} min read</div>
        </div>
      </article>"""
        )

    body = f"""  <main class="main-content">
    <div class="container">
      <section class="hero-section">
        <div class="hero-content">
          <span class="badge badge-cyan" style="margin-bottom: 1rem;">Practical engineering guides</span>
          <h1>Build, ship, and debug with clarity</h1>
          <p class="hero-subtitle">25 original how-to guides on web performance, APIs, databases, DevOps, and frontend — written for developers who search when something is broken.</p>
          <p style="margin: 1rem 0 0;"><a class="btn btn-primary" href="start-here.html">New here? Start here</a>
          <a class="btn btn-secondary" href="resources.html" style="margin-left:0.5rem;">Useful resources</a></p>

          <div class="search-box-container">
            <span class="search-icon" aria-hidden="true">⌕</span>
            <input type="text" id="articleSearchInput" class="search-input" placeholder="Search guides (CORS, JWT, Docker, Core Web Vitals…)" aria-label="Search articles">
          </div>

          <div class="category-filters" role="toolbar" aria-label="Filter by category">
            {chr(10).join(filters)}
          </div>
        </div>
      </section>

      <section id="articles" class="article-grid" aria-label="Articles">
{chr(10).join(cards)}
      </section>
    </div>
  </main>"""

    page = shell(
        "BudhiWorks — Practical Web Engineering Guides",
        "Original how-to guides on Core Web Vitals, JWT auth, Docker, React, Postgres, Redis, and more — written from production experience.",
        f"{SITE}/",
        "home",
        body,
    )
    (ROOT / "index.html").write_text(page, encoding="utf-8")


def write_about() -> None:
    body = f"""  <main class="main-content">
    <div class="container article-container">
      <div class="article-header" style="text-align:center;">
        <span class="badge badge-cyan" style="margin-bottom:1rem;">About</span>
        <h1>A small publication for <span class="gradient-text">working engineers</span></h1>
        <p class="article-lead" style="max-width:720px;margin:0 auto 2rem;">
          BudhiWorks exists because most “ultimate guides” online are either too shallow to ship from or too academic to use under deadline. This site publishes fewer posts — each one meant to answer a real search like “how to fix CORS” or “when to use Postgres indexes.”
        </p>
      </div>

      <section class="info-card">
        <h2 style="font-size:1.4rem;margin-top:0;">Who runs this</h2>
        <p><strong>{esc(AUTHOR["name"])}</strong> — {esc(AUTHOR["role"])}.</p>
        <p>{esc(AUTHOR["bio"])}</p>
        <p>I am not a faceless “editorial team.” If something is wrong in an article, email me and I will fix it.</p>
        <p><a href="author.html">Full author page</a> · <a href="mailto:{esc(AUTHOR["email"])}">{esc(AUTHOR["email"])}</a></p>
      </section>

      <section class="info-card">
        <h2 style="font-size:1.4rem;margin-top:0;">Why BudhiWorks exists</h2>
        <p>“Budhi” points to practical intelligence — judgment you use while building. The site focuses on:</p>
        <ul>
          <li>Problems people actually type into Google (CORS, JWT cookies, Core Web Vitals, Docker Compose).</li>
          <li>Guides with copy-pasteable commands and the failure modes I have hit in production.</li>
          <li>A small catalog (25 strong posts) instead of a flood of lookalike essays.</li>
        </ul>
      </section>

      <section class="info-card">
        <h2 style="font-size:1.4rem;margin-top:0;">Editorial standards</h2>
        <p>Every guide should be usable without ads. We document sources of truth (official docs) on the <a href="resources.html">resources</a> page and follow a public <a href="editorial-policy.html">editorial policy</a>.</p>
        <p>We do not publish AI-padded philosophy metaphors dressed up as engineering.</p>
      </section>
    </div>
  </main>"""
    page = shell(
        "About BudhiWorks — Who we are and why this site exists",
        "BudhiWorks is a practical engineering publication by Ram: original how-tos for web, APIs, databases, and DevOps.",
        f"{SITE}/about.html",
        "about",
        body,
    )
    (ROOT / "about.html").write_text(page, encoding="utf-8")


def write_contact() -> None:
    body = f"""  <main class="main-content">
    <div class="container">
      <div style="text-align:center;max-width:700px;margin:0 auto 3rem;">
        <span class="badge badge-cyan" style="margin-bottom:1rem;">Contact</span>
        <h1>Talk to a <span class="gradient-text">real person</span></h1>
        <p class="hero-subtitle">Corrections, topic requests, and partnership notes go to {esc(AUTHOR["name"])}. Expect a reply within 1–2 business days.</p>
      </div>

      <div class="info-card" style="max-width:720px;margin:0 auto 2rem;">
        <h2 style="font-size:1.3rem;margin-top:0;">Direct email</h2>
        <p><a href="mailto:{esc(AUTHOR["email"])}">{esc(AUTHOR["email"])}</a></p>
        <p>Best for: factual corrections, “this command failed on my stack,” or suggesting a guide people keep searching for.</p>
      </div>

      <div class="form-container">
        <div id="formAlert" class="form-alert" role="alert"></div>
        <form id="contactForm" novalidate>
          <div class="form-group">
            <label for="name" class="form-label">Full name <span style="color:var(--accent-primary);">*</span></label>
            <input type="text" id="name" name="name" class="form-input" placeholder="Your name" required>
          </div>
          <div class="form-group">
            <label for="email" class="form-label">Email <span style="color:var(--accent-primary);">*</span></label>
            <input type="email" id="email" name="email" class="form-input" placeholder="you@example.com" required>
          </div>
          <div class="form-group">
            <label for="subject" class="form-label">Subject <span style="color:var(--accent-primary);">*</span></label>
            <input type="text" id="subject" name="subject" class="form-input" placeholder="e.g. Correction on JWT cookie guide" required>
          </div>
          <div class="form-group">
            <label for="message" class="form-label">Message <span style="color:var(--accent-primary);">*</span></label>
            <textarea id="message" name="message" class="form-input" rows="6" placeholder="Include URLs, error text, and what you already tried." required></textarea>
          </div>
          <button type="submit" class="btn btn-primary">Send message</button>
        </form>
        <p style="margin-top:1rem;color:var(--text-muted);font-size:0.9rem;">The form opens your mail client to {esc(AUTHOR["email"])}. If that fails, email directly.</p>
      </div>
    </div>
  </main>"""
    page = shell(
        "Contact BudhiWorks",
        "Contact Ram at BudhiWorks for corrections, topic requests, or partnership inquiries.",
        f"{SITE}/contact.html",
        "contact",
        body,
    )
    (ROOT / "contact.html").write_text(page, encoding="utf-8")


def write_author() -> None:
    recent = "\n".join(
        f'            <li><a href="articles/{esc(a["slug"])}.html">{esc(a["title"])}</a> — {esc(fmt_date(a["date"]))}</li>'
        for a in ARTICLES[:8]
    )
    body = f"""  <main class="main-content">
    <div class="container article-container">
      <div class="article-header">
        <span class="badge badge-emerald">Author</span>
        <h1>{esc(AUTHOR["name"])}</h1>
        <p class="article-lead">{esc(AUTHOR["role"])}</p>
        <div class="article-meta">
          <div class="author-avatar">{esc(AUTHOR["initials"])}</div>
          <div>
            <strong>{esc(AUTHOR["name"])}</strong><br>
            <a href="mailto:{esc(AUTHOR["email"])}">{esc(AUTHOR["email"])}</a>
          </div>
        </div>
      </div>
      <div class="article-prose">
        <p>{esc(AUTHOR["bio"])}</p>
        <p>Topics I write about most: API auth, database performance, containerized local setups, frontend performance, and the CI/CD glue that turns a repo into a deploy.</p>
        <h2>Recent guides</h2>
        <ul>
{recent}
        </ul>
        <p><a href="index.html#articles">Browse all 25 guides</a> · <a href="editorial-policy.html">How we edit</a></p>
      </div>
    </div>
  </main>"""
    page = shell(
        "Ram — Author at BudhiWorks",
        "Meet Ram, founder and editor of BudhiWorks: practical web engineering guides from production experience.",
        f"{SITE}/author.html",
        "about",
        body,
    )
    (ROOT / "author.html").write_text(page, encoding="utf-8")


def write_editorial() -> None:
    body = """  <main class="main-content">
    <div class="container article-container">
      <div class="article-header">
        <span class="badge badge-cyan">Policy</span>
        <h1>Editorial policy</h1>
        <p class="article-lead">How BudhiWorks decides what to publish, how we update posts, and what we will not do.</p>
      </div>
      <div class="article-prose">
        <h2>What we publish</h2>
        <p>Guides that answer a concrete developer question with steps you can run. Preference goes to topics with clear search intent (troubleshooting, comparisons, setup checklists).</p>
        <h2>Accuracy</h2>
        <p>Commands and configs are checked against current docs when published. If a reader reports a break, we patch the page and note material updates when the change is significant.</p>
        <h2>Independence</h2>
        <p>Affiliate or sponsored mentions — if any — will be labeled. Ads never decide article topics.</p>
        <h2>What we reject</h2>
        <ul>
          <li>Thin rewrites of documentation with no added decision guidance.</li>
          <li>Mass-produced lookalike posts published on the same day.</li>
          <li>Philosophy metaphors that do not help you ship or debug.</li>
        </ul>
        <h2>Corrections</h2>
        <p>Email <a href="mailto:contact@budhiworks.com">contact@budhiworks.com</a> with the URL and what failed. Serious errors get priority fixes.</p>
      </div>
    </div>
  </main>"""
    page = shell(
        "Editorial policy — BudhiWorks",
        "BudhiWorks editorial standards: practical how-tos, accuracy updates, and no thin lookalike content.",
        f"{SITE}/editorial-policy.html",
        "about",
        body,
    )
    (ROOT / "editorial-policy.html").write_text(page, encoding="utf-8")


def write_start_here() -> None:
    paths = [
        ("Stuck on an API error", ["how-to-fix-cors-errors", "jwt-authentication-nodejs", "api-rate-limiting", "rest-api-design-best-practices"]),
        ("Making pages faster", ["core-web-vitals-guide", "optimize-images-webp-avif", "debounce-throttle-javascript"]),
        ("Local & production ops", ["docker-compose-for-developers", "nginx-reverse-proxy-setup", "github-actions-ci-cd", "deploy-static-site-guide"]),
        ("Data layer", ["postgresql-indexes-explained", "redis-caching-patterns", "sql-vs-nosql-when-to-choose", "mongodb-aggregation-pipeline"]),
        ("Frontend craft", ["react-useeffect-common-mistakes", "nextjs-app-router-data-fetching", "css-flexbox-vs-grid", "accessibility-wcag-checklist", "typescript-generics-practical-guide"]),
    ]
    by_slug = {a["slug"]: a for a in ARTICLES}
    blocks = []
    for title, slugs in paths:
        items = []
        for s in slugs:
            a = by_slug[s]
            items.append(f'<li><a href="articles/{esc(s)}.html">{esc(a["title"])}</a></li>')
        blocks.append(f"""      <section class="info-card">
        <h2 style="font-size:1.25rem;margin-top:0;">{esc(title)}</h2>
        <ul>
          {chr(10).join(items)}
        </ul>
      </section>""")

    body = f"""  <main class="main-content">
    <div class="container article-container">
      <div class="article-header">
        <span class="badge badge-emerald">Orientation</span>
        <h1>Start here</h1>
        <p class="article-lead">Pick the path that matches what you are trying to do. These are the highest-utility guides on the site — the ones people typically search without caring about ads.</p>
      </div>
{chr(10).join(blocks)}
      <p style="margin-top:2rem;"><a href="resources.html">Official docs &amp; tools we recommend →</a></p>
    </div>
  </main>"""
    page = shell(
        "Start here — BudhiWorks learning paths",
        "Curated learning paths for CORS, JWT, Core Web Vitals, Docker, Postgres, React, and more.",
        f"{SITE}/start-here.html",
        "start",
        body,
    )
    (ROOT / "start-here.html").write_text(page, encoding="utf-8")


def write_resources() -> None:
    body = """  <main class="main-content">
    <div class="container article-container">
      <div class="article-header">
        <span class="badge badge-cyan">Resources</span>
        <h1>Useful pages without the fluff</h1>
        <p class="article-lead">Bookmarks we actually use while writing BudhiWorks guides. Prefer primary documentation over random Medium clones.</p>
      </div>
      <div class="article-prose">
        <h2>Performance &amp; frontend</h2>
        <ul>
          <li><a href="https://web.dev/articles/vitals" rel="noopener noreferrer" target="_blank">web.dev — Core Web Vitals</a></li>
          <li><a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS" rel="noopener noreferrer" target="_blank">MDN — CORS</a></li>
          <li><a href="https://react.dev/reference/react/useEffect" rel="noopener noreferrer" target="_blank">React docs — useEffect</a></li>
          <li><a href="https://nextjs.org/docs/app/building-your-application/data-fetching" rel="noopener noreferrer" target="_blank">Next.js — Data fetching</a></li>
        </ul>
        <h2>Backend &amp; data</h2>
        <ul>
          <li><a href="https://jwt.io/introduction" rel="noopener noreferrer" target="_blank">JWT introduction</a></li>
          <li><a href="https://www.postgresql.org/docs/current/indexes.html" rel="noopener noreferrer" target="_blank">PostgreSQL indexes</a></li>
          <li><a href="https://redis.io/docs/latest/develop/use/patterns/" rel="noopener noreferrer" target="_blank">Redis patterns</a></li>
          <li><a href="https://www.mongodb.com/docs/manual/aggregation/" rel="noopener noreferrer" target="_blank">MongoDB aggregation</a></li>
        </ul>
        <h2>Ops</h2>
        <ul>
          <li><a href="https://docs.docker.com/compose/" rel="noopener noreferrer" target="_blank">Docker Compose</a></li>
          <li><a href="https://nginx.org/en/docs/http/ngx_http_proxy_module.html" rel="noopener noreferrer" target="_blank">Nginx proxy module</a></li>
          <li><a href="https://docs.github.com/en/actions" rel="noopener noreferrer" target="_blank">GitHub Actions</a></li>
          <li><a href="https://kubernetes.io/docs/concepts/configuration/secret/" rel="noopener noreferrer" target="_blank">Kubernetes Secrets</a></li>
        </ul>
        <h2>On this site</h2>
        <ul>
          <li><a href="start-here.html">Start-here learning paths</a></li>
          <li><a href="editorial-policy.html">Editorial policy</a></li>
          <li><a href="author.html">Author bio</a></li>
          <li><a href="sitemap.xml">XML sitemap</a></li>
        </ul>
      </div>
    </div>
  </main>"""
    page = shell(
        "Resources — BudhiWorks",
        "Curated official docs and tools for web performance, APIs, databases, and DevOps.",
        f"{SITE}/resources.html",
        "resources",
        body,
    )
    (ROOT / "resources.html").write_text(page, encoding="utf-8")


def write_sitemap() -> None:
    urls = [
        ("/", "1.0"),
        ("/about.html", "0.7"),
        ("/contact.html", "0.6"),
        ("/author.html", "0.7"),
        ("/start-here.html", "0.8"),
        ("/resources.html", "0.8"),
        ("/editorial-policy.html", "0.5"),
        ("/privacy.html", "0.3"),
        ("/terms.html", "0.3"),
    ]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path, prio in urls:
        last = ARTICLES[0]["date"] if ARTICLES else "2026-08-29"
        lines.append("  <url>")
        lines.append(f"    <loc>{SITE}{path if path != '/' else '/'}</loc>")
        lines.append(f"    <lastmod>{last}</lastmod>")
        lines.append(f"    <priority>{prio}</priority>")
        lines.append("  </url>")
    for a in ARTICLES:
        lines.append("  <url>")
        lines.append(f"    <loc>{SITE}/articles/{a['slug']}.html</loc>")
        lines.append(f"    <lastmod>{a['date']}</lastmod>")
        lines.append("    <priority>0.8</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def patch_legal_nav() -> None:
    for name in ("privacy.html", "terms.html"):
        path = ROOT / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        # Best-effort: leave content; generator already linked them from footer.
        path.write_text(text, encoding="utf-8")


def main() -> None:
    if ARTICLES_DIR.exists():
        shutil.rmtree(ARTICLES_DIR)
    ARTICLES_DIR.mkdir(parents=True)

    for i, article in enumerate(ARTICLES):
        write_article(article, i)

    write_index()
    write_about()
    write_contact()
    write_author()
    write_editorial()
    write_start_here()
    write_resources()
    write_sitemap()
    patch_legal_nav()

    print(f"Generated {len(ARTICLES)} articles + core pages in {ROOT}")
    print("Categories:", sorted({a["category"] for a in ARTICLES}))


if __name__ == "__main__":
    main()

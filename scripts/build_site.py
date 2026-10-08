"""Regenerate GitHub Pages HTML from editable fragments and publication records.

Python 3.10+; standard library only. Run from any working directory.
The committed HTML is ready to serve without a build or JavaScript.
"""
from collections import defaultdict
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://yaningliucudenver.github.io/"
PROFILE = json.loads((ROOT / "content/profile.json").read_text(encoding="utf-8"))
PUBLICATIONS = json.loads((ROOT / "content/publications.json").read_text(encoding="utf-8"))
PAGES = {
    "index.html": ("Yaning Liu | Associate Professor · CU Denver", "Yaning Liu, Associate Professor and Director of Statistical Programs at CU Denver. Research in uncertainty quantification, machine learning, and scientific modeling."),
    "publications.html": ("Publications | Yaning Liu", "Journal articles, preprints, books, and proceedings by Yaning Liu. Search work in uncertainty quantification, surrogate modeling, and subsurface energy storage."),
    "courses.html": ("Teaching | Yaning Liu", "Yaning Liu's teaching in numerical analysis, machine learning, probabilistic modeling, data science, Monte Carlo methods, and uncertainty quantification."),
    "students.html": ("Students & Mentoring | Yaning Liu", "Doctoral and master's advising and committee service by Yaning Liu at the University of Colorado Denver."),
    "education.html": ("Education & Experience | Yaning Liu", "Yaning Liu's education at Florida State University and Zhejiang University, and academic appointments at CU Denver and Lawrence Berkeley National Laboratory."),
    "grants.html": ("Grants & Awards | Yaning Liu", "Research grants, open education projects, and teaching awards involving Yaning Liu at the University of Colorado Denver."),
    "conferences.html": ("Talks & Conferences | Yaning Liu", "Invited talks, seminars, and conference presentations in uncertainty quantification, surrogate modeling, and computational mathematics."),
    "OER.html": ("Open Educational Resources | Yaning Liu", "Open numerical analysis resources with Python, an online Jupyter Book, computational notebooks, and CU Denver mathematics and statistics materials."),
}
PRIMARY_NAV = [("Home", "index.html"), ("Research", "index.html#research"), ("Publications", "publications.html"), ("Teaching", "courses.html"), ("Students", "students.html")]
SECONDARY_NAV = [("Education & experience", "education.html"), ("Grants & awards", "grants.html"), ("Talks & conferences", "conferences.html"), ("Open resources", "OER.html")]
TYPES = {"journal": "Journal article", "preprint": "Preprint", "book": "Book", "resource": "Book companion", "chapter": "Book chapter", "conference": "Conference paper"}
TOPICS = {"uncertainty": "Uncertainty & sensitivity", "surrogates": "Surrogate modeling & ML", "energy": "Energy & environment", "applications": "Other applications"}


def text(value):
    return escape(str(value), quote=True)


def validate_publications():
    ids, identities = set(), set()
    for paper in PUBLICATIONS:
        for field in ("id", "title", "authors", "year", "type", "venue", "url", "topics"):
            if field not in paper:
                raise ValueError(f"Missing {field}: {paper.get('id')}")
        if paper["id"] in ids:
            raise ValueError(f"Duplicate ID: {paper['id']}")
        ids.add(paper["id"])
        identity = (re.sub(r"\W+", "", paper["title"]).lower(), paper["type"])
        if identity in identities:
            raise ValueError(f"Duplicate publication: {paper['title']}")
        identities.add(identity)
        if paper["type"] not in TYPES or not paper["authors"]:
            raise ValueError(f"Invalid type or authors: {paper['id']}")
        if paper["year"] is not None and (not isinstance(paper["year"], int) or not 1900 <= paper["year"] <= 2100):
            raise ValueError(f"Invalid year: {paper['id']}")
        for key in ("url", "scholarUrl"):
            if paper.get(key) and urlparse(paper[key]).scheme not in ("https", "http"):
                raise ValueError(f"Invalid {key}: {paper['id']}")
        if not paper["topics"] or any(topic not in TOPICS for topic in paper["topics"]):
            raise ValueError(f"Invalid topics: {paper['id']}")


def authors_html(paper):
    authors = []
    for index, author in enumerate(paper["authors"]):
        own = author == "Yaning Liu" or index == paper.get("selfAuthorIndex")
        authors.append(f"<strong>{text(author)}</strong>" if own else text(author))
    return ", ".join(authors)


def citation(paper):
    venue = [paper["venue"]]
    if paper.get("volume"):
        vol = str(paper["volume"])
        if paper.get("issue"):
            vol += f", {paper['issue']}" if str(paper["issue"]).startswith("Part ") else f"({paper['issue']})"
        venue.append(vol)
    if paper.get("pages"):
        venue.append(str(paper["pages"]))
    venue.append(str(paper["year"]) if paper["year"] else "Undated")
    return " · ".join(venue)


def render_paper(paper):
    search = " ".join([paper["title"], PROFILE["name"], *paper["authors"], citation(paper), TYPES[paper["type"]], *(TOPICS[t] for t in paper["topics"]), paper.get("doi", "")])
    label = "Read preprint" if paper["type"] == "preprint" else "View resource" if paper["type"] in ("book", "resource") else "View publication"
    links = f'<a href="{text(paper["url"])}">{label} <span aria-hidden="true">↗</span></a>'
    if paper.get("doi") and paper["url"] != f'https://doi.org/{paper["doi"]}':
        links += f'<a href="https://doi.org/{text(paper["doi"])}">DOI <span aria-hidden="true">↗</span></a>'
    if paper.get("scholarUrl"):
        links += f'<a href="{text(paper["scholarUrl"])}">Scholar <span aria-hidden="true">↗</span></a>'
    note = f'<p class="paper-note">{text(paper["note"])}</p>' if paper.get("note") else ""
    return f'''<li class="publication" id="{text(paper['id'])}" data-publication data-year="{paper['year'] or 'undated'}" data-type="{paper['type']}" data-topics="{' '.join(paper['topics'])}" data-search="{text(search)}">
      <h4><a href="{text(paper['url'])}">{text(paper['title'])}</a></h4>
      <p class="paper-authors">{authors_html(paper)}</p>
      <p class="paper-venue">{text(citation(paper))} · {TYPES[paper['type']]}</p>
      {note}<div class="paper-links">{links}</div>
    </li>'''


def publication_page():
    years = sorted({p["year"] for p in PUBLICATIONS if p["year"]}, reverse=True)
    options = '<option value="all">All years</option>' + "".join(f'<option value="{year}">{year}</option>' for year in years)
    if any(p["year"] is None for p in PUBLICATIONS):
        options += '<option value="undated">Undated</option>'
    topic_options = '<option value="all">All research areas</option>' + "".join(f'<option value="{key}">{text(label)}</option>' for key, label in TOPICS.items())
    chips = "".join(f'<button class="filter-chip" type="button" data-type-filter="{kind}" aria-pressed="{str(kind == "all").lower()}">{label}</button>' for kind, label in [("all", "All work"), ("journal", "Journal articles"), ("preprint", "Preprints"), ("book,resource", "Books & resources"), ("chapter,conference", "Chapters & proceedings")])
    sections = []
    for types, label, note in [
        (("journal",), "Journal articles", ""),
        (("preprint",), "Preprints", "Preprints are listed separately from peer-reviewed journal articles."),
        (("book", "resource"), "Books & educational resources", ""),
        (("chapter",), "Book chapters", ""),
        (("conference",), "Refereed conference papers", ""),
    ]:
        groups = defaultdict(list)
        for paper in PUBLICATIONS:
            if paper["type"] in types:
                groups[paper["year"] or 0].append(paper)
        if not groups:
            continue
        html_groups = []
        for year in sorted(groups, reverse=True):
            entries = "\n".join(render_paper(p) for p in sorted(groups[year], key=lambda p: p["title"].lower()))
            html_groups.append(f'<div class="publication-group" data-publication-group><h3>{year or "Undated"}</h3><ol class="publication-list">{entries}</ol></div>')
        note_html = f'<p class="source-note">{text(note)}</p>' if note else ""
        sections.append(f'<section class="publication-section" data-publication-section><h2>{label}</h2>{note_html}{"".join(html_groups)}</section>')
    return f'''<div class="container">
      <header class="page-heading"><p class="eyebrow">Research & scholarship</p><h1>Publications</h1><p class="intro">Work in uncertainty quantification, sensitivity analysis, surrogate modeling, and their applications to complex scientific systems.</p><div class="heading-links"><a class="text-link" href="{text(PROFILE['scholar'])}">Google Scholar <span aria-hidden="true">↗</span></a><a class="text-link" href="content/publications.bib" download>Download BibTeX <span aria-hidden="true">↓</span></a></div><p class="source-note">Publication records checked against Google Scholar and publisher records · October 2026</p></header>
      <div class="publication-filters" data-publication-filters hidden>
        <div class="filter-fields"><div class="filter-field"><label for="publication-search">Search publications</label><input id="publication-search" type="search" placeholder="Search title, author, journal, or keyword…" autocomplete="off"></div><div class="filter-field"><label for="publication-year">Year</label><select id="publication-year">{options}</select></div><div class="filter-field"><label for="publication-topic">Research area</label><select id="publication-topic">{topic_options}</select></div></div>
        <div class="filter-chips" role="group" aria-label="Publication type">{chips}</div>
        <div class="filter-status"><p id="publication-results" role="status" aria-live="polite">{len(PUBLICATIONS)} publications</p><button type="button" id="publication-reset">Clear filters</button></div>
      </div>
      <div class="page-content">{''.join(sections)}<div class="empty-state" id="publication-empty" hidden><h2>No publications found.</h2><p>Try another keyword, or use “Clear filters” above.</p></div></div>
    </div>'''


def recent_publications():
    selected = []
    for phrase in ("Hierarchical Dirichlet", "Application of multifidelity", "Operational performance of compressed CO2"):
        paper = next((p for p in PUBLICATIONS if phrase in p["title"] and p["type"] == "journal"), None)
        if paper:
            selected.append(f'<a class="recent-paper" href="publications.html#{text(paper["id"])}"><span class="recent-year">{paper["year"]}</span><div><h3>{text(paper["title"])}</h3><p>{text(citation(paper))}</p></div><span class="recent-arrow" aria-hidden="true">↗</span></a>')
    return "\n".join(selected)


def render_nav(entries, current):
    links = []
    for label, href in entries:
        active = ' aria-current="page"' if href == current else ""
        links.append(f'<a href="{href}"{active}>{text(label)}</a>')
    return "\n".join(links)


def bibtex_escape(value):
    # Protect title case and encode punctuation that has meaning in BibTeX/LaTeX.
    replacements = {"\\": "\\textbackslash{}", "&": "\\&", "%": "\\%", "_": "\\_", "#": "\\#", "$": "\\$", "{": "\\{", "}": "\\}"}
    return "".join(replacements.get(c, c) for c in str(value))


def write_bibtex():
    entries = []
    for paper in PUBLICATIONS:
        kind = {"journal": "article", "book": "book", "chapter": "incollection", "conference": "inproceedings"}.get(paper["type"], "misc")
        fields = {"title": "{" + bibtex_escape(paper["title"]) + "}", "author": " and ".join(bibtex_escape(a) for a in paper["authors"])}
        if paper["year"]:
            fields["year"] = str(paper["year"])
        fields["journal" if kind == "article" else "booktitle" if kind in ("incollection", "inproceedings") else "howpublished" if kind == "misc" else "publisher"] = bibtex_escape(paper["venue"])
        for key in ("volume", "issue", "pages", "doi", "url"):
            if paper.get(key):
                fields["number" if key == "issue" else key] = bibtex_escape(paper[key])
        if paper["type"] == "preprint":
            fields["note"] = "Preprint"
        entries.append(f'@{kind}{{{paper["id"]},\n' + ",\n".join(f"  {key} = {{{value}}}" for key, value in fields.items()) + "\n}")
    (ROOT / "content/publications.bib").write_text("\n\n".join(entries) + "\n", encoding="utf-8")


def main():
    validate_publications()
    template = (ROOT / "templates/base.html").read_text(encoding="utf-8")
    stylesheet_version = sha256((ROOT / "assets/site.css").read_bytes()).hexdigest()[:12]
    profile_data = {
        "@context": "https://schema.org", "@type": "Person", "name": PROFILE["name"],
        "url": ORIGIN, "image": ORIGIN + "img/SelfPic.jpg", "jobTitle": [PROFILE["title"], PROFILE["leadership"]],
        "email": PROFILE["email"], "affiliation": {"@type": "CollegeOrUniversity", "name": PROFILE["institution"]},
        "sameAs": [PROFILE[k] for k in ("scholar", "faculty", "linkedin")],
    }
    for filename, (title, description) in PAGES.items():
        content = publication_page() if filename == "publications.html" else (ROOT / "content/pages" / filename).read_text(encoding="utf-8")
        values = {
            **{k: text(v) for k, v in PROFILE.items()}, "title_role": text(PROFILE["title"]), "title_lower": text(PROFILE["title"].lower()),
            "title": text(title), "description": text(description), "canonical": ORIGIN + filename,
            "year": PROFILE["verified"][:4], "selected_publications": recent_publications(),
            "stylesheet_version": stylesheet_version,
            "structured_data": '<script type="application/ld+json">' + json.dumps(profile_data, ensure_ascii=False).replace("<", "\\u003c") + "</script>" if filename == "index.html" else "",
            "navigation": render_nav(PRIMARY_NAV, filename), "secondary_navigation": render_nav(SECONDARY_NAV, filename),
            "more_current": ' class="is-current"' if filename in {href for _, href in SECONDARY_NAV} else "",
        }
        for key, value in values.items():
            content = content.replace("{{" + key + "}}", value)
        values["content"] = content
        output = template
        for key, value in values.items():
            output = output.replace("{{" + key + "}}", value)
        if re.search(r"\{\{\w+\}\}", output):
            raise ValueError(f"Unfilled placeholder in {filename}")
        output = "\n".join(line.rstrip() for line in output.splitlines()) + "\n"
        (ROOT / filename).write_text(output, encoding="utf-8")
    write_bibtex()
    # Preserve the earlier homepage URL while directing visitors to current content.
    (ROOT / "index_old.html").write_text('<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=index.html"><title>Yaning Liu — current website</title></head><body><p><a href="index.html">Visit Yaning Liu’s current website.</a></p></body></html>\n', encoding="utf-8")
    urls = "\n".join(f"  <url><loc>{ORIGIN}{filename}</loc></url>" for filename in PAGES)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}\n</urlset>\n', encoding="utf-8")
    print(f"Generated {len(PAGES)} pages and {len(PUBLICATIONS)} publication records.")


if __name__ == "__main__":
    main()

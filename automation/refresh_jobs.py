#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

JOBS_CSV = OUTPUT_DIR / "bioinformatics-jobs-board.csv"
JOBS_MD = OUTPUT_DIR / "bioinformatics-jobs-board.md"
TRENDS_MD = OUTPUT_DIR / "bioinformatics-skill-trends.md"
HISTORY_CSV = OUTPUT_DIR / "bioinformatics-trend-history.csv"

USER_AGENT = "bioinformatics-hiring-index/1.0 (+https://github.com/SpicyChicken6/bioinformatics_jobskill_index)"
TIMEZONE = ZoneInfo("America/Chicago")
SNAPSHOT_DATE = datetime.now(TIMEZONE).date().isoformat()

RESPONSIBILITY_HINTS = (
    "responsibil",
    "what you'll do",
    "what you will do",
    "what youll do",
    "you will",
    "in this role",
    "day-to-day",
    "day to day",
    "key duties",
    "essential duties",
    "primary duties",
    "position summary",
    "about the role",
)

REQUIREMENT_HINTS = (
    "requirement",
    "qualification",
    "what we're looking for",
    "what we are looking for",
    "you have",
    "who you are",
    "skills",
    "experience",
    "preferred",
    "minimum",
    "basic qualification",
)

ROLE_RULES = [
    ("Computational Biologist", re.compile(r"\bcomputational biologist\b", re.I)),
    ("Bioinformatics Scientist", re.compile(r"\bbioinformatics scientist\b", re.I)),
    ("Bioinformatics Engineer", re.compile(r"\bbioinformatics engineer\b", re.I)),
    ("Bioinformatics Analyst", re.compile(r"\bbioinformatics analyst\b", re.I)),
]

SKILL_RULES = [
    ("Python", [r"\bpython\b"]),
    ("R", [r"\\br\\b(?!\\s*&\\s*d)", r"bioconductor", r"seurat", r"tidyverse"]),
    ("NGS / genomics", [r"\bngs\b", r"genomics?", r"rna-?seq", r"sequencing", r"transcriptomics?", r"ctdna", r"cfdna"]),
    ("Pipelines / workflow orchestration", [r"pipelines?", r"workflows?", r"workflow orchestration", r"automation"]),
    ("Statistics / modeling", [r"statistics?", r"statistical", r"modeling", r"modelling", r"regression", r"bayesian"]),
    ("Single-cell / multi-omics", [r"single-?cell", r"multi-omics?", r"multiomics", r"spatial omics", r"perturb"]),
    ("Linux / Unix", [r"linux", r"unix", r"\bbash\b", r"shell scripting"]),
    ("Software engineering / reproducibility", [r"software engineering", r"reproducible", r"version control", r"\bgit\b", r"testing"]),
    ("Cross-functional collaboration", [r"cross-functional", r"stakeholders?", r"partner with", r"collaborat", r"wet-?lab"]),
    ("Scientific writing / communication", [r"manuscript", r"presentation", r"scientific writing", r"grant", r"communicat", r"write up"]),
    ("Cancer / liquid biopsy / biomarkers", [r"oncology", r"cancer", r"liquid biopsy", r"biomarker", r"ctdna", r"cfdna"]),
    ("Experimental design / assay partnership", [r"assay design", r"assay development", r"experimental design", r"wet-?lab", r"assay"]),
    ("Cloud / scalable compute", [r"\baws\b", r"\bgcp\b", r"\bazure\b", r"cloud", r"distributed systems", r"scalab"]),
    ("Machine learning / AI", [r"machine learning", r"\bml\b", r"artificial intelligence", r"\bai\b", r"deep learning"]),
    ("Workflow engines \(Nextflow / WDL / Snakemake\)", [r"nextflow", r"\bwdl\b", r"snakemake", r"cromwell"]),
    ("Data visualization / reporting", [r"visualization", r"dashboard", r"reporting", r"plot", r"notebook"]),
    ("Clinical / translational applications", [r"clinical", r"translational", r"patient stratification"]),
    ("Multi-omics integration", [r"multimodal", r"integrat(?:e|ing) .*omics", r"multi-omics integration", r"proteomics", r"cytokines"]),
    ("Containers / CI-CD / production", [r"docker", r"containers?", r"ci/cd", r"ci cd", r"production"]),
    ("Drug discovery", [r"drug discovery", r"target discovery", r"therapeutic hypotheses"]),
    ("Natural products / comparative genomics", [r"natural product", r"comparative genomics"]),
    ("Customer-facing / platform migration", [r"customer", r"platform migration", r"user-facing"]),
]

FOCUS_RULES = [
    ("New cfDNA product opportunities", [r"novel cell free dna", r"novel cfdna", r"new cfdna"]),
    ("cfDNA assay R&D and product translation", [r"cfdna", r"cell free dna"]),
    ("Single-cell perturbation biology", [r"single-?cell", r"perturb"]),
    ("Aging, single-cell, and target discovery", [r"aging", r"target discovery"]),
    ("Translational and clinical biomarker strategy", [r"translational", r"patient stratification", r"clinical biomarker"]),
    ("Natural product discovery and comparative genomics", [r"natural product", r"comparative genomics"]),
    ("NGS platform engineering for gene editing", [r"gene editing", r"ngs platform"]),
    ("Oncology assay and algorithm development", [r"oncology", r"product development", r"assay"]),
    ("Production pipeline engineering for molecular diagnostics", [r"molecular diagnostics", r"production pipeline", r"bioinformatics engineer"]),
    ("Platform migration and workflow productization", [r"platform migration", r"productization"]),
    ("AI-enabled multi-omics drug discovery", [r"drug discovery", r"multi-omics", r"ai-enabled"]),
    ("Cancer genomics research", [r"cancer genomics"]),
    ("Research informatics and collaborative omics analysis", [r"research informatics", r"omics analysis"]),
]

WORK_MODE_RULES = [
    ("Remote", [r"\bremote\b", r"work from home"]),
    ("Hybrid", [r"\bhybrid\b"]),
    ("On-site", [r"on-?site", r"in person", r"in-person"]),
]

HISTORY_FIELDS = [
    "snapshot_date",
    "total_roles",
    "unique_companies",
    "computational_biologist_roles",
    "bioinformatics_scientist_roles",
    "bioinformatics_engineer_roles",
    "bioinformatics_analyst_roles",
    "python_roles",
    "pipelines_roles",
    "ngs_genomics_roles",
    "r_roles",
    "statistics_roles",
    "cancer_biomarker_roles",
    "cloud_roles",
    "ml_ai_roles",
    "single_cell_multiomics_roles",
    "workflow_engine_roles",
    "cross_functional_collaboration_roles",
]

GREENHOUSE_SOURCES = [
    {"board_token": "neptunebio", "company": "Neptune Bio", "default_work_mode": "On-site"},
    {"board_token": "newlimit", "company": "NewLimit", "default_work_mode": "On-site"},
    {"board_token": "recursionpharmaceuticals", "company": "Recursion", "default_work_mode": "Hybrid"},
    {"board_token": "hexagonbio", "company": "Hexagon Bio", "default_work_mode": "On-site"},
    {"board_token": "profluent", "company": "Profluent", "default_work_mode": "On-site"},
    {"board_token": "natera", "company": "Natera", "default_work_mode": "Hybrid"},
    {"board_token": "personalisinc", "company": "Personalis", "default_work_mode": "Hybrid"},
    {"board_token": "latchbio", "company": "LatchBio", "default_work_mode": "On-site"},
]

LEVER_SOURCES = [
    {"site": "gatchealth", "company": "GATC Health", "default_work_mode": "Remote"},
]

DIRECT_HTML_SOURCES = [
    {
        "company": "Dana-Farber Cancer Institute",
        "url": "https://careers.dana-farber.org/job/538/computational-biologist-it-informatics-us-ma-boston-450-brookline-ave/",
        "default_location": "Boston, MA",
        "default_work_mode": "On-site",
    },
    {
        "company": "Dana-Farber Cancer Institute",
        "url": "https://careers.dana-farber.org/job/446/computational-biologist-collins-genomics-lab-it-informatics-us-ma-boston-450-brookline-ave/",
        "default_location": "Boston, MA",
        "default_work_mode": "On-site",
    },
]


@dataclass
class JobRecord:
    company: str
    title: str
    role_family: str
    focus_area: str
    location: str
    work_mode: str
    responsibilities: list[str]
    requirements: list[str]
    skill_tags: list[str]
    source_url: str


class StructuredHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.capture: str | None = None
        self.buffer: list[str] = []
        self.tokens: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self._flush()
            self.capture = "heading"
            self.buffer = []
        elif tag == "li":
            self._flush()
            self.capture = "li"
            self.buffer = []
        elif tag == "p":
            self._flush()
            self.capture = "p"
            self.buffer = []
        elif tag == "br" and self.capture:
            self.buffer.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self.capture == "heading":
            self._flush()
        elif tag == "li" and self.capture == "li":
            self._flush()
        elif tag == "p" and self.capture == "p":
            self._flush()

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.buffer.append(data)

    def _flush(self) -> None:
        if self.capture:
            text = clean_text("".join(self.buffer))
            if text:
                self.tokens.append((self.capture, text))
        self.capture = None
        self.buffer = []


def main() -> int:
    warnings: list[str] = []
    jobs: list[JobRecord] = []

    for source in GREENHOUSE_SOURCES:
        try:
            jobs.extend(fetch_greenhouse_jobs(source))
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Greenhouse source '{source['board_token']}' failed: {exc}")

    for source in LEVER_SOURCES:
        try:
            jobs.extend(fetch_lever_jobs(source))
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Lever source '{source['site']}' failed: {exc}")

    for source in DIRECT_HTML_SOURCES:
        try:
            job = fetch_direct_html_job(source)
            if job:
                jobs.append(job)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"Direct source '{source['url']}' failed: {exc}")

    jobs = dedupe_jobs(sort_jobs(jobs))
    if not jobs:
        raise SystemExit("No jobs were collected; refusing to overwrite outputs with an empty dataset.")

    write_jobs_csv(jobs)
    write_jobs_markdown(jobs)
    write_trends_markdown(jobs, warnings)
    write_history_csv(jobs)

    print(f"Wrote {len(jobs)} jobs for snapshot {SNAPSHOT_DATE}.")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")
    return 0


def fetch_greenhouse_jobs(source: dict[str, str]) -> list[JobRecord]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{source['board_token']}/jobs?content=true"
    payload = fetch_json(url)
    jobs: list[JobRecord] = []
    for item in payload.get("jobs", []):
        title = clean_text(item.get("title", ""))
        role_family = classify_role_family(title)
        if not role_family:
            continue

        content_html = item.get("content") or ""
        responsibilities, requirements, plain_text = extract_content_sections(content_html)
        combined_text = " ".join([title, plain_text])
        location = clean_text((item.get("location") or {}).get("name", "")) or "Unspecified"
        work_mode = infer_work_mode(combined_text, location, source.get("default_work_mode", "On-site"))
        focus_area = infer_focus_area(combined_text)
        skill_tags = infer_skill_tags(combined_text)
        jobs.append(
            JobRecord(
                company=source["company"],
                title=title,
                role_family=role_family,
                focus_area=focus_area,
                location=location,
                work_mode=work_mode,
                responsibilities=responsibilities,
                requirements=requirements,
                skill_tags=skill_tags,
                source_url=item.get("absolute_url", url),
            )
        )
    return jobs


def fetch_lever_jobs(source: dict[str, str]) -> list[JobRecord]:
    url = f"https://api.lever.co/v0/postings/{source['site']}?mode=json"
    payload = fetch_json(url)
    jobs: list[JobRecord] = []
    for item in payload:
        title = clean_text(item.get("text", ""))
        role_family = classify_role_family(title)
        if not role_family:
            continue

        sections, plain_text = extract_lever_sections(item)
        responsibilities = choose_section_items(sections, RESPONSIBILITY_HINTS)
        requirements = choose_section_items(sections, REQUIREMENT_HINTS)
        fallback_items = flatten_section_items(sections)
        if not responsibilities:
            responsibilities = fallback_items[:3] or sentence_fallback(plain_text)[:3]
        if not requirements:
            requirements = [item for item in fallback_items if item not in responsibilities][:3] or sentence_fallback(plain_text)[3:6]

        categories = item.get("categories") or {}
        location = clean_text(categories.get("location") or categories.get("allLocations") or "Unspecified")
        combined_text = " ".join([title, plain_text, location])
        work_mode = infer_work_mode(combined_text, location, source.get("default_work_mode", "Remote"))
        focus_area = infer_focus_area(combined_text)
        skill_tags = infer_skill_tags(combined_text)

        jobs.append(
            JobRecord(
                company=source["company"],
                title=title,
                role_family=role_family,
                focus_area=focus_area,
                location=location,
                work_mode=work_mode,
                responsibilities=responsibilities,
                requirements=requirements,
                skill_tags=skill_tags,
                source_url=item.get("hostedUrl", url),
            )
        )
    return jobs


def fetch_direct_html_job(source: dict[str, str]) -> JobRecord | None:
    html_text = fetch_text(source["url"])
    title = parse_page_title(html_text)
    role_family = classify_role_family(title)
    if not role_family:
        return None

    responsibilities, requirements, plain_text = extract_content_sections(html_text)
    combined_text = " ".join([title, plain_text])
    return JobRecord(
        company=source["company"],
        title=title,
        role_family=role_family,
        focus_area=infer_focus_area(combined_text),
        location=source.get("default_location", "Unspecified"),
        work_mode=infer_work_mode(combined_text, source.get("default_location", ""), source.get("default_work_mode", "On-site")),
        responsibilities=responsibilities,
        requirements=requirements,
        skill_tags=infer_skill_tags(combined_text),
        source_url=source["url"],
    )


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_json(url: str) -> dict | list:
    return json.loads(fetch_text(url))


def extract_lever_sections(item: dict) -> tuple[dict[str, list[str]], str]:
    sections: dict[str, list[str]] = {}
    plain_parts = [clean_text(item.get("descriptionPlain", "")), clean_text(item.get("additionalPlain", ""))]
    for section in item.get("lists") or []:
        heading = normalize_heading(section.get("text", "")) or "section"
        content = section.get("content")
        extracted: list[str] = []
        if isinstance(content, list):
            for entry in content:
                if isinstance(entry, str):
                    extracted.extend(extract_items_from_html(entry))
                elif isinstance(entry, dict):
                    extracted.extend(extract_items_from_html(str(entry.get("text") or entry.get("content") or "")))
        elif isinstance(content, str):
            extracted.extend(extract_items_from_html(content))
        extracted = limit_bullets(extracted, limit=None)
        if extracted:
            sections.setdefault(heading, []).extend(extracted)
            plain_parts.extend(extracted)
    return sections, clean_text(" ".join(plain_parts))


def extract_content_sections(raw_html: str) -> tuple[list[str], list[str], str]:
    parser = StructuredHTMLParser()
    parser.feed(raw_html)
    parser.close()

    sections: dict[str, list[str]] = {}
    current_heading = ""
    orphan_bullets: list[str] = []
    paragraph_text: list[str] = []
    for kind, text in parser.tokens:
        if kind == "heading":
            current_heading = normalize_heading(text)
            sections.setdefault(current_heading, [])
        elif kind == "li":
            if current_heading:
                sections.setdefault(current_heading, []).append(text)
            else:
                orphan_bullets.append(text)
        elif kind == "p":
            paragraph_text.append(text)

    responsibilities = choose_section_items(sections, RESPONSIBILITY_HINTS)
    requirements = choose_section_items(sections, REQUIREMENT_HINTS)
    all_bullets = flatten_section_items(sections) + orphan_bullets
    all_bullets = dedupe_keep_order(all_bullets)

    if not responsibilities:
        responsibilities = all_bullets[:3]
    if not requirements:
        requirements = [item for item in all_bullets if item not in responsibilities][:3]

    if not responsibilities:
        responsibilities = sentence_fallback(" ".join(paragraph_text))[:3]
    if not requirements:
        requirements = sentence_fallback(" ".join(paragraph_text))[3:6]

    plain_text = clean_text(" ".join(paragraph_text + all_bullets))
    return limit_bullets(responsibilities), limit_bullets(requirements), plain_text


def extract_items_from_html(raw_html: str) -> list[str]:
    raw_html = raw_html or ""
    parser = StructuredHTMLParser()
    parser.feed(raw_html)
    parser.close()
    items = [text for kind, text in parser.tokens if kind in {"li", "p"}]
    if items:
        return dedupe_keep_order(items)
    stripped = strip_html(raw_html)
    return sentence_fallback(stripped)


def choose_section_items(sections: dict[str, list[str]], hints: Iterable[str]) -> list[str]:
    selected: list[str] = []
    for heading, items in sections.items():
        if any(hint in heading for hint in hints):
            selected.extend(items)
    return limit_bullets(dedupe_keep_order(selected))


def flatten_section_items(sections: dict[str, list[str]]) -> list[str]:
    flattened: list[str] = []
    for items in sections.values():
        flattened.extend(items)
    return dedupe_keep_order(flattened)


def limit_bullets(items: list[str], limit: int | None = 3) -> list[str]:
    cleaned = []
    for item in items:
        normalized = clean_text(item)
        if normalized:
            cleaned.append(normalized)
    cleaned = dedupe_keep_order(cleaned)
    return cleaned if limit is None else cleaned[:limit]


def sentence_fallback(text: str) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [clean_text(sentence) for sentence in sentences if clean_text(sentence)]


def infer_skill_tags(text: str) -> list[str]:
    skill_tags: list[str] = []
    for label, patterns in SKILL_RULES:
        if any(re.search(pattern, text, re.I) for pattern in patterns):
            skill_tags.append(label)
    return skill_tags


def infer_focus_area(text: str) -> str:
    lowered = text.lower()
    for label, patterns in FOCUS_RULES:
        if any(re.search(pattern, lowered, re.I) for pattern in patterns):
            return label
    return "General bioinformatics and computational biology"


def infer_work_mode(text: str, location: str, default_mode: str) -> str:
    combined = f"{text} {location}".lower()
    for label, patterns in WORK_MODE_RULES:
        if any(re.search(pattern, combined, re.I) for pattern in patterns):
            return label
    if location.lower() == "united states":
        return "Remote"
    return default_mode


def classify_role_family(title: str) -> str | None:
    for label, pattern in ROLE_RULES:
        if pattern.search(title):
            return label
    return None


def parse_page_title(raw_html: str) -> str:
    for pattern in [r"<h1[^>]*>(.*?)</h1>", r"<title[^>]*>(.*?)</title>"]:
        match = re.search(pattern, raw_html, re.I | re.S)
        if match:
            text = clean_text(strip_html(match.group(1)))
            if text:
                return text.replace("| Dana-Farber Cancer Institute Careers", "").strip()
    return "Unknown title"


def strip_html(raw_html: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", raw_html)
    return clean_text(html.unescape(without_tags))


def normalize_heading(value: str) -> str:
    return re.sub(r"\s+", " ", clean_text(value).lower()).strip(": ")


def clean_text(value: str) -> str:
    value = html.unescape(str(value or ""))
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -\t\r\n")


def dedupe_keep_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def sort_jobs(jobs: list[JobRecord]) -> list[JobRecord]:
    return sorted(jobs, key=lambda item: (item.company.lower(), item.title.lower()))


def dedupe_jobs(jobs: list[JobRecord]) -> list[JobRecord]:
    seen: set[str] = set()
    deduped: list[JobRecord] = []
    for job in jobs:
        key = job.source_url.lower()
        if key not in seen:
            deduped.append(job)
            seen.add(key)
    return deduped


def write_jobs_csv(jobs: list[JobRecord]) -> None:
    with JOBS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Company", "Title", "RoleFamily", "FocusArea", "Location", "WorkMode", "Responsibilities", "Requirements", "KeySkills", "SourceUrl"])
        for job in jobs:
            writer.writerow([
                job.company,
                job.title,
                job.role_family,
                job.focus_area,
                job.location,
                job.work_mode,
                "; ".join(job.responsibilities),
                "; ".join(job.requirements),
                "; ".join(job.skill_tags),
                job.source_url,
            ])


def write_jobs_markdown(jobs: list[JobRecord]) -> None:
    lines = [
        "# Bioinformatics Jobs Board",
        "",
        f"Snapshot date: {SNAPSHOT_DATE}  ",
        f"Verified live roles: {len(jobs)}  ",
        f"Unique companies: {len({job.company for job in jobs})}",
        "",
        "This board is regenerated from public company job-board endpoints and direct official job pages. The snapshot date is the date of retrieval in America/Chicago.",
        "",
        "| Company | Title | Role family | Focus area | Location | Mode | Responsibilities | Requirements | Key skills | Source |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for job in jobs:
        lines.append(
            "| {company} | {title} | {role} | {focus} | {location} | {mode} | {resp} | {req} | {skills} | [Source]({url}) |".format(
                company=escape_md(job.company),
                title=escape_md(job.title),
                role=escape_md(job.role_family),
                focus=escape_md(job.focus_area),
                location=escape_md(job.location),
                mode=escape_md(job.work_mode),
                resp=escape_md("; ".join(job.responsibilities)),
                req=escape_md("; ".join(job.requirements)),
                skills=escape_md(", ".join(job.skill_tags)),
                url=job.source_url,
            )
        )
    JOBS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_trends_markdown(jobs: list[JobRecord], warnings: list[str]) -> None:
    skill_counts = Counter(skill for job in jobs for skill in job.skill_tags)
    role_counts = Counter(job.role_family for job in jobs)
    mode_counts = Counter(job.work_mode for job in jobs)
    total_roles = len(jobs)

    sorted_skills = sorted(skill_counts.items(), key=lambda item: (-item[1], item[0]))
    lines = [
        "# Bioinformatics Skill Trends",
        "",
        f"Snapshot date: {SNAPSHOT_DATE}  ",
        f"Verified live roles: {total_roles}  ",
        f"Unique companies: {len({job.company for job in jobs})}",
        "",
        "## Method",
        "- The refresh job pulls from public company job-board APIs where available and a small set of direct official job pages for sources without a stable public API.",
        "- The dashboard tracks the retrieval date rather than job post dates, because job boards expose posting dates inconsistently.",
        "- Trend tags are normalized from responsibilities and requirements so they can be compared across companies.",
        "",
        "## Role mix",
    ]
    lines.extend(f"- {label}: {count}" for label, count in sorted(role_counts.items(), key=lambda item: (-item[1], item[0])))
    lines.extend([
        "",
        "## Work-mode mix",
    ])
    lines.extend(f"- {label}: {count}" for label, count in sorted(mode_counts.items(), key=lambda item: (-item[1], item[0])))
    lines.extend([
        "",
        "## Top skill index",
    ])
    for label, count in sorted_skills:
        share = round((count / total_roles) * 100, 1)
        lines.append(f"- {label}: {count}/{total_roles} roles ({share}%)")

    lines.extend([
        "",
        "## What is trending",
        f"- Python appears in {skill_counts.get('Python', 0)}/{total_roles} live roles and remains the baseline programming skill.",
        f"- Pipeline or workflow work appears in {skill_counts.get('Pipelines / workflow orchestration', 0)}/{total_roles} roles, which keeps production-oriented bioinformatics central to the market.",
        f"- Oncology or biomarker-oriented work appears in {skill_counts.get('Cancer / liquid biopsy / biomarkers', 0)}/{total_roles} roles in this snapshot.",
        f"- Cloud appears in {skill_counts.get('Cloud / scalable compute', 0)}/{total_roles} roles and ML or AI appears in {skill_counts.get('Machine learning / AI', 0)}/{total_roles} roles.",
        f"- Explicit workflow engines such as Nextflow, WDL, or Snakemake appear in {skill_counts.get('Workflow engines (Nextflow / WDL / Snakemake)', 0)}/{total_roles} roles.",
    ])

    if warnings:
        lines.extend([
            "",
            "## Source notes",
        ])
        lines.extend(f"- {warning}" for warning in warnings)

    lines.extend([
        "",
        "## Source files",
        "- `bioinformatics-jobs-board.csv`",
        "- `bioinformatics-jobs-board.md`",
        "- `bioinformatics-trend-history.csv`",
    ])
    TRENDS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_history_csv(jobs: list[JobRecord]) -> None:
    role_counts = Counter(job.role_family for job in jobs)
    skill_counts = Counter(skill for job in jobs for skill in job.skill_tags)
    history_rows: list[dict[str, str]] = []
    if HISTORY_CSV.exists():
        with HISTORY_CSV.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                history_rows.append(dict(row))

    current_row = {
        "snapshot_date": SNAPSHOT_DATE,
        "total_roles": str(len(jobs)),
        "unique_companies": str(len({job.company for job in jobs})),
        "computational_biologist_roles": str(role_counts.get("Computational Biologist", 0)),
        "bioinformatics_scientist_roles": str(role_counts.get("Bioinformatics Scientist", 0)),
        "bioinformatics_engineer_roles": str(role_counts.get("Bioinformatics Engineer", 0)),
        "bioinformatics_analyst_roles": str(role_counts.get("Bioinformatics Analyst", 0)),
        "python_roles": str(skill_counts.get("Python", 0)),
        "pipelines_roles": str(skill_counts.get("Pipelines / workflow orchestration", 0)),
        "ngs_genomics_roles": str(skill_counts.get("NGS / genomics", 0)),
        "r_roles": str(skill_counts.get("R", 0)),
        "statistics_roles": str(skill_counts.get("Statistics / modeling", 0)),
        "cancer_biomarker_roles": str(skill_counts.get("Cancer / liquid biopsy / biomarkers", 0)),
        "cloud_roles": str(skill_counts.get("Cloud / scalable compute", 0)),
        "ml_ai_roles": str(skill_counts.get("Machine learning / AI", 0)),
        "single_cell_multiomics_roles": str(skill_counts.get("Single-cell / multi-omics", 0)),
        "workflow_engine_roles": str(skill_counts.get("Workflow engines (Nextflow / WDL / Snakemake)", 0)),
        "cross_functional_collaboration_roles": str(skill_counts.get("Cross-functional collaboration", 0)),
    }

    filtered_rows = [row for row in history_rows if row.get("snapshot_date") != SNAPSHOT_DATE]
    filtered_rows.append(current_row)
    filtered_rows.sort(key=lambda row: row["snapshot_date"])

    with HISTORY_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HISTORY_FIELDS)
        writer.writeheader()
        writer.writerows(filtered_rows)


def escape_md(value: str) -> str:
    return str(value).replace("|", "\\|")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HTTPError as exc:
        print(f"HTTP error: {exc}", file=sys.stderr)
        raise
    except URLError as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        raise

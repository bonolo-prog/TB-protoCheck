"""
Step 1 - Load documents and split them into citable sections.

Each Markdown document is split at its '## ' headings. Every section gets a
stable ID such as 'SOP-001#5', so an answer can say exactly where a fact came
from, and the verifier can look that section up again.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Section:
    id: str          # e.g. "SOP-001#5"
    doc_id: str      # e.g. "SOP-001"
    doc_title: str   # e.g. "DNA Library Preparation for Short-Read Sequencing"
    title: str       # e.g. "5. Adapter ligation"
    text: str        # the section body

    def as_prompt_block(self) -> str:
        return f"[{self.id}] {self.doc_id}, section '{self.title}'\n{self.text}"


def _doc_id_and_title(first_heading: str, fallback: str) -> tuple[str, str]:
    """'# SOP-001: DNA Library Preparation' -> ('SOP-001', 'DNA Library Preparation')"""
    m = re.match(r"#\s*([A-Za-z0-9_.-]+)\s*:\s*(.+)", first_heading)
    if m:
        return m.group(1), m.group(2).strip()
    return fallback, first_heading.lstrip("# ").strip()


def load_markdown(path: Path) -> list[Section]:
    lines = path.read_text(encoding="utf-8").splitlines()
    first = next((ln for ln in lines if ln.startswith("# ")), f"# {path.stem}")
    doc_id, doc_title = _doc_id_and_title(first, path.stem)

    sections: list[Section] = []
    title, body = None, []

    def flush():
        if title is not None and "\n".join(body).strip():
            num = re.match(r"(\d+(?:\.\d+)*)", title)
            key = num.group(1) if num else str(len(sections) + 1)
            sections.append(Section(f"{doc_id}#{key}", doc_id, doc_title,
                                    title, "\n".join(body).strip()))

    for line in lines:
        if line.startswith("## "):
            flush()
            title, body = line[3:].strip(), []
        elif title is not None:
            body.append(line)
    flush()
    return sections


def load_folder(folder: str | Path) -> list[Section]:
    folder = Path(folder)
    files = sorted(folder.glob("*.md"))
    if not files:
        raise FileNotFoundError(f"No .md documents found in {folder}")
    sections = [s for f in files for s in load_markdown(f)]
    ids = [s.id for s in sections]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"Duplicate section IDs (check document IDs): {sorted(dupes)}")
    return sections

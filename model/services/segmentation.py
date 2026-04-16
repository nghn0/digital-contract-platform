# app/services/segmentation.py
import re
from typing import List, Tuple

# Common legal section heading patterns
HEADING_PATTERN = re.compile(
    r'^\s*(\d+\.?\d*\.?\d*\s+[A-Z][^\n]{3,180}|'      # "1. CONFIDENTIALITY"
    r'[A-Z][A-Z\s]{4,50}(?=\n)|'                    # "CONFIDENTIALITY\n"
    r'(?:Section|Article|Clause)\s+\d+[^\n]{0,50})', # "Section 5. ..."
    re.MULTILINE
)

FALLBACK_NUMERIC_LINE_PATTERN = re.compile(
    r"^\s*(?:(?:section|article|clause)\s*)?\d{1,3}(?:\s*[\.:\-)]+\s*|\s+).{2,}$",
    re.IGNORECASE,
)

EMBEDDED_DOC_BOUNDARY_PATTERN = re.compile(
    r"(?im)^\s*(?:"
    r"(?:neutrinos\s+)?non[-\s]?disclosure\s+agreement|"
    r"nda\b|"
    r"this\s+agreement\s+is\s+made\s+on|"
    r"in\s+witness\s+whereof|"
    r"confidential\s+information\s*:?"
    r")\s*$"
)

SUBCLAUSE_ANCHOR_PATTERN = re.compile(
    r"(?im)^\s*(?:"
    r"\([a-z0-9]+\)|"
    r"[a-z]\)|"
    r"\d+[\.:\)]|"
    r"[A-Z][A-Z\s]{4,80}|"
    r"(?:Confidential(?:ity| Information)|Obligations? of Confidentiality|Exceptions?|"
    r"Retention(?:\s+Duration)?|Return(?:\s+or\s+Destruction)?\s+of\s+Information|"
    r"Permitted\s+Use|Term(?:\s+and\s+Termination)?)"
    r")\s*$"
)


def _split_by_embedded_boundaries(text: str) -> list[str]:
    """Split mixed PDFs into logical document blocks using embedded agreement markers."""
    matches = list(EMBEDDED_DOC_BOUNDARY_PATTERN.finditer(text))
    if not matches:
        return [text]

    boundaries = sorted({match.start() for match in matches if match.start() > 0})
    if not boundaries:
        return [text]

    blocks: list[str] = []
    last = 0
    for boundary in boundaries:
        block = text[last:boundary].strip()
        if len(block) > 50:
            blocks.append(block)
        last = boundary

    tail = text[last:].strip()
    if len(tail) > 50:
        blocks.append(tail)

    return blocks or [text]


def _split_large_clause(heading: str, body: str, max_chars: int = 1700) -> list[tuple[str, str]]:
    """Split oversized clauses into smaller sub-clauses for stable extraction quality."""
    cleaned_body = (body or "").strip()
    lines = [line.rstrip() for line in cleaned_body.splitlines() if line.strip()]
    if not lines:
        return [(heading, cleaned_body)]

    anchors = [index for index, line in enumerate(lines) if SUBCLAUSE_ANCHOR_PATTERN.match(line.strip())]
    if len(cleaned_body) <= max_chars and len(anchors) < 2:
        return [(heading, cleaned_body)]

    if 0 not in anchors:
        anchors.insert(0, 0)
    anchors = sorted(set(anchors))

    chunks: list[tuple[str, str]] = []
    if len(anchors) >= 2:
        for idx, start in enumerate(anchors):
            end = anchors[idx + 1] if idx + 1 < len(anchors) else len(lines)
            part_lines = lines[start:end]
            part_text = "\n".join(part_lines).strip()
            if len(part_text) < 40:
                continue

            first_line = part_lines[0].strip()
            section_title = first_line if len(first_line) <= 90 else first_line[:90].rstrip()
            section_heading = f"{heading} - {section_title}" if section_title else heading

            if len(part_text) > max_chars:
                chunks.extend(_split_large_clause(section_heading, part_text, max_chars=max_chars))
            else:
                chunks.append((section_heading, part_text))

    if chunks:
        return chunks

    paragraphs = [p.strip() for p in cleaned_body.split("\n\n") if len(p.strip()) > 60]
    if len(paragraphs) >= 3:
        for index, paragraph in enumerate(paragraphs, start=1):
            para_heading = f"{heading} - Part {index}"
            if len(paragraph) > max_chars:
                chunks.extend(_split_large_clause(para_heading, paragraph, max_chars=max_chars))
            else:
                chunks.append((para_heading, paragraph))
        return chunks

    compact = re.sub(r"\s+", " ", cleaned_body).strip()
    chunk_size = max_chars
    overlap = 180
    start = 0
    part_index = 1
    while start < len(compact):
        end = min(len(compact), start + chunk_size)
        cut = compact.rfind(" ", start, end)
        if cut <= start + 300:
            cut = end
        piece = compact[start:cut].strip()
        if len(piece) > 80:
            chunks.append((f"{heading} - Part {part_index}", piece))
            part_index += 1
        if cut >= len(compact):
            break
        start = max(cut - overlap, start + 1)

    return chunks or [(heading, cleaned_body)]


def _fallback_segment_text(text: str) -> List[str]:
    """Robust fallback segmentation for noisy/OCR text.

    Strategy:
    1) Paragraph split on blank lines.
    2) Split by numbered line anchors when blank lines are missing.
    3) Size-based chunking for fully unstructured long documents.
    """
    paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 80]
    if len(paragraphs) >= 3:
        return paragraphs

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    anchor_indices = [i for i, line in enumerate(lines) if FALLBACK_NUMERIC_LINE_PATTERN.match(line)]
    if len(anchor_indices) >= 3:
        chunks: List[str] = []
        for idx, start in enumerate(anchor_indices):
            end = anchor_indices[idx + 1] if idx + 1 < len(anchor_indices) else len(lines)
            chunk = "\n".join(lines[start:end]).strip()
            if len(chunk) > 120:
                chunks.append(chunk)
        if len(chunks) >= 3:
            return chunks

    textual_anchor_indices = [i for i, line in enumerate(lines) if SUBCLAUSE_ANCHOR_PATTERN.match(line)]
    if len(textual_anchor_indices) >= 2:
        chunks: List[str] = []
        for idx, start in enumerate(textual_anchor_indices):
            end = textual_anchor_indices[idx + 1] if idx + 1 < len(textual_anchor_indices) else len(lines)
            chunk = "\n".join(lines[start:end]).strip()
            if len(chunk) > 40:
                chunks.append(chunk)
        if len(chunks) >= 2:
            return chunks

    # Last resort for very long, unstructured text.
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) < 1600:
        # Very short strings are typically extraction noise and should not create fake clauses.
        return [compact] if len(compact) >= 80 else []

    chunk_size = 1800
    overlap = 220
    chunks = []
    start = 0
    while start < len(compact):
        end = min(len(compact), start + chunk_size)
        cut = compact.rfind(" ", start, end)
        if cut <= start + 400:
            cut = end
        chunk = compact[start:cut].strip()
        if len(chunk) > 120:
            chunks.append(chunk)
        if cut >= len(compact):
            break
        start = max(cut - overlap, start + 1)

    return chunks


def _clean_heading(heading: str) -> str:
    """Normalize a detected heading and remove likely body-text bleed-through."""
    normalized = (heading or "").strip()

    # Handle merged heading/body lines like: "10. Collateral. The term ..."
    numeric_prefix = re.match(r"^(\d+[\.\d]*\s+)", normalized)
    if numeric_prefix and ". " in normalized:
        split_index = normalized.find(". ")
        # Keep title sentence only when extra body sentence exists.
        if split_index > 0 and split_index + 2 < len(normalized):
            candidate = normalized[: split_index + 1].strip()
            if len(candidate) >= len(numeric_prefix.group(1)) + 3:
                return candidate

    if len(normalized) <= 80:
        return normalized

    title_match = re.match(r'^(\d+[\.\d]*\s+[A-Z][^.]{3,60}\.)', normalized)
    if title_match:
        return title_match.group(1).strip()

    truncated = normalized[:60].rsplit(' ', 1)[0].strip()
    return f"{truncated}..." if truncated else normalized[:60]

def segment_clauses(text: str) -> List[Tuple[str, str]]:
    """
    Split contract text into (heading, clause_text) tuples.
    Returns list of (section_heading, clause_body) pairs.
    
    Strategy:
    1. Try regex heading detection first (fast, deterministic)
    2. Fall back to paragraph-level split for unstructured docs
    """
    normalized_text = (text or "").strip()
    if not normalized_text:
        return []

    clauses: list[tuple[str, str]] = []
    blocks = _split_by_embedded_boundaries(normalized_text)

    for block_index, block in enumerate(blocks, start=1):
        matches = list(HEADING_PATTERN.finditer(block))

        if len(matches) >= 2:
            # Well-structured document — split by headings.
            for i, match in enumerate(matches):
                original_heading = match.group(0).strip()
                heading = _clean_heading(original_heading)
                start = match.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(block)
                body = block[start:end].strip()

                if original_heading != heading:
                    bleed = ""
                    if original_heading.startswith(heading):
                        bleed = original_heading[len(heading):].strip()
                    elif heading.endswith("..."):
                        prefix = heading[:-3].strip()
                        if prefix and original_heading.startswith(prefix):
                            bleed = original_heading[len(prefix):].strip()
                    if bleed:
                        body = f"{bleed} {body}".strip()

                if len(body) > 20:
                    clauses.append((heading, body))
        else:
            # Unstructured/noisy docs: robust fallback segmentation.
            paragraphs = _fallback_segment_text(block)
            for i, para in enumerate(paragraphs, start=1):
                clauses.append((f"Section {block_index}.{i}", para))

    granular: list[tuple[str, str]] = []
    for heading, body in clauses:
        granular.extend(_split_large_clause(heading, body, max_chars=1700))

    return [(heading, body) for heading, body in granular if len((body or "").strip()) > 20]

def chunk_for_context(text: str, max_chars: int = 6000) -> List[str]:
    """
    For long contracts, split into overlapping chunks for Pass 1/3/4/5
    that need the full document but must fit in context window.
    """
    chunks = []
    words = text.split()
    chunk_words = []
    char_count = 0
    
    for word in words:
        chunk_words.append(word)
        char_count += len(word) + 1
        if char_count >= max_chars:
            chunks.append(' '.join(chunk_words))
            # 200-word overlap for continuity
            chunk_words = chunk_words[-200:]
            char_count = sum(len(w) + 1 for w in chunk_words)
    
    if chunk_words:
        chunks.append(' '.join(chunk_words))
    
    return chunks
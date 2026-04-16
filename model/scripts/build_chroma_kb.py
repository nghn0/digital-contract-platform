from __future__ import annotations

"""Build ChromaDB collections from knowledge-base JSON files.

Reads all KB JSON files in knowledge-base/ (excluding chroma_db artifacts) and
loads entries into Chroma collections keyed by source filename.
"""

import json
from pathlib import Path
from typing import Any

import chromadb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KB_DIR = PROJECT_ROOT / "knowledge-base"
CHROMA_PATH = KB_DIR / "chroma_db"


def _collection_name_for_file(file_name: str) -> str:
    stem = Path(file_name).stem
    return f"kb_{stem}"


def _entry_document(entry: dict[str, Any]) -> str:
    metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
    key_indicators = metadata.get("key_indicators") if isinstance(metadata.get("key_indicators"), list) else []

    parts = [
        str(entry.get("text") or "").strip(),
        f"type: {metadata.get('clause_type') or metadata.get('risk_type') or metadata.get('document_type') or entry.get('type') or ''}",
        "key_indicators: " + ", ".join(str(item) for item in key_indicators if str(item).strip()),
        f"notes: {metadata.get('notes') or ''}",
    ]
    return "\n".join(part for part in parts if part.strip())


def _entry_metadata(entry: dict[str, Any], source_file: str) -> dict[str, Any]:
    metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
    return {
        "domain": str(metadata.get("domain") or "General"),
        "collection_source": source_file,
        "risk_level": str(metadata.get("risk_level") or metadata.get("typical_risk") or "UNKNOWN"),
    }


def build_chroma_kb() -> tuple[int, int]:
    """Load KB entries from JSON into Chroma collections.

    Returns:
        Tuple of (documents_loaded, collections_loaded).
    """
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    documents_loaded = 0
    collections_loaded = 0

    for json_file in sorted(KB_DIR.glob("*.json")):
        try:
            with json_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            # Keep build resilient when optional KB files are empty/corrupt.
            print(f"[WARN] Skipping invalid JSON file: {json_file.name}")
            continue
        entries = payload.get("entries", []) if isinstance(payload, dict) else []
        if not entries:
            continue

        collection_name = _collection_name_for_file(json_file.name)
        collection = client.get_or_create_collection(name=collection_name)
        collections_loaded += 1

        ids: list[str] = []
        docs: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for idx, entry in enumerate(entries):
            if not isinstance(entry, dict):
                continue
            entry_id = str(entry.get("id") or f"{json_file.stem}_{idx}")
            ids.append(entry_id)
            docs.append(_entry_document(entry))
            metadatas.append(_entry_metadata(entry, json_file.name))

        if ids:
            existing = collection.get(ids=ids)
            existing_ids = set(existing.get("ids") or [])
            new_ids: list[str] = []
            new_docs: list[str] = []
            new_meta: list[dict[str, Any]] = []
            for i, entry_id in enumerate(ids):
                if entry_id in existing_ids:
                    continue
                new_ids.append(entry_id)
                new_docs.append(docs[i])
                new_meta.append(metadatas[i])

            if new_ids:
                collection.add(ids=new_ids, documents=new_docs, metadatas=new_meta)
                documents_loaded += len(new_ids)

    return documents_loaded, collections_loaded


if __name__ == "__main__":
    loaded_docs, loaded_collections = build_chroma_kb()
    print(f"Loaded {loaded_docs} documents into {loaded_collections} collections")

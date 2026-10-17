#!/usr/bin/env python3
"""Bounded, offline BM25 passage search with hash-checked source citations.

Only Python's standard library is used. Nothing is executed from a document.
The current working directory is the workspace boundary for every input/output.
"""

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
import unicodedata

FORMAT = "evidence-search/v1"
SUFFIXES = {".md", ".txt", ".rst"}
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 8_000_000
MAX_INDEX_BYTES = 16_000_000
MAX_FILES = 1000
MAX_PASSAGES = 20000
MAX_LINE_CHARS = 16000
WINDOW = 10
STRIDE = 8


class SearchError(ValueError):
    pass


def workspace_path(value):
    """Reject traversal and symlinks before reading the selected workspace path."""
    path = Path(value)
    if ".." in path.parts:
        raise SearchError("parent traversal is not allowed")
    base = Path.cwd()
    if not path.is_absolute():
        path = base / path
    try:
        relative = path.relative_to(base)
    except ValueError:
        raise SearchError("path is outside the current workspace") from None
    current = base
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise SearchError("symlink paths are not allowed")
    return path


def read_bytes(path, limit):
    if not path.is_file():
        raise SearchError(f"not a regular file: {path.name}")
    # Read at most one byte beyond the cap, even if the file grows while read.
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise SearchError(f"file exceeds {limit} bytes: {path.name}")
    return data


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_lines(text):
    # LF and CRLF count as one source line; other Unicode separators stay in it.
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [line.removesuffix("\r") for line in lines]


def tokens(text):
    """Unicode case-insensitive words; retain complete hexadecimal addresses."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)


def valid_relative(name):
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        return False
    path = PurePosixPath(name)
    return (not path.is_absolute() and name == path.as_posix()
            and all(part not in (".", "..") and not part.startswith(".")
                    for part in path.parts)
            and path.suffix.lower() in SUFFIXES)


def validate_index(index):
    if not isinstance(index, dict) or set(index) != {"format", "documents"}:
        raise SearchError("invalid index envelope")
    if index["format"] != FORMAT:
        raise SearchError("unsupported index format")
    documents = index["documents"]
    if not isinstance(documents, list) or len(documents) > MAX_FILES:
        raise SearchError("invalid document count")
    seen, total = set(), 0
    for document in documents:
        if not isinstance(document, dict) or set(document) != {"path", "sha256", "text"}:
            raise SearchError("invalid indexed document")
        name, sha, text = (document[key] for key in ("path", "sha256", "text"))
        if not valid_relative(name) or name in seen:
            raise SearchError("invalid or duplicate source path")
        seen.add(name)
        if not isinstance(text, str) or "\x00" in text:
            raise SearchError("invalid indexed text")
        try:
            raw = text.encode("utf-8")
        except UnicodeError:
            raise SearchError("invalid Unicode in indexed text") from None
        total += len(raw)
        if len(raw) > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
            raise SearchError("source byte limit exceeded")
        if any(len(line) > MAX_LINE_CHARS for line in source_lines(text)):
            raise SearchError("source line length limit exceeded")
        if not isinstance(sha, str) or sha != digest(raw):
            raise SearchError("indexed text does not match its SHA-256")
    return index


def build_index(root):
    root = workspace_path(root)
    if not root.is_dir():
        raise SearchError("corpus root must be a directory")
    documents, total = [], 0
    # Hidden entries and symlinks are excluded; no links are followed.
    def walk_error(error):
        raise SearchError(f"cannot read corpus directory: {error.strerror}")
    for folder, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        dirs[:] = sorted(name for name in dirs if not name.startswith(".")
                         and not (Path(folder) / name).is_symlink())
        for name in sorted(files):
            path = Path(folder) / name
            if name.startswith(".") or path.suffix.lower() not in SUFFIXES:
                continue
            if path.is_symlink():
                continue
            path = workspace_path(path)
            if len(documents) >= MAX_FILES:
                raise SearchError("document count limit exceeded")
            raw = read_bytes(path, MAX_FILE_BYTES)
            total += len(raw)
            if total > MAX_TOTAL_BYTES:
                raise SearchError("total source byte limit exceeded")
            try:
                text = raw.decode("utf-8")
            except UnicodeError:
                raise SearchError(f"source is not UTF-8: {path.name}") from None
            documents.append({"path": path.relative_to(root).as_posix(),
                              "sha256": digest(raw), "text": text})
    documents.sort(key=lambda item: item["path"])
    index = validate_index({"format": FORMAT, "documents": documents})
    passages(index)  # Fail at build time if the passage budget would be exceeded.
    return index


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SearchError("duplicate JSON key in index")
        result[key] = value
    return result


def load_index(filename):
    raw = read_bytes(workspace_path(filename), MAX_INDEX_BYTES)
    try:
        index = json.loads(raw, object_pairs_hook=reject_duplicates)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise SearchError("index is not valid UTF-8 JSON") from None
    return validate_index(index)


def write_index(filename, index):
    path = workspace_path(filename)
    if path.exists():
        raise SearchError("index output already exists; choose a new filename")
    if not path.parent.is_dir():
        raise SearchError("index parent directory must already exist")
    data = (json.dumps(index, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(data) > MAX_INDEX_BYTES:
        raise SearchError("serialized index byte limit exceeded")
    # Exclusive creation avoids overwriting any corpus or existing user file.
    try:
        with path.open("xb") as stream:
            stream.write(data)
    except FileExistsError:
        raise SearchError("index output already exists") from None


def passages(index):
    result = []
    for document in index["documents"]:
        lines = source_lines(document["text"])
        previous = None
        for start in range(0, len(lines), STRIDE):
            end = min(start + WINDOW, len(lines))
            while start < end and not lines[start].strip():
                start += 1
            while end > start and not lines[end - 1].strip():
                end -= 1
            if start == end or (start, end) == previous:
                continue
            previous = (start, end)
            text = "\n".join(lines[start:end])
            counts = Counter(tokens(text))
            if counts:
                result.append({"document": document, "start": start + 1,
                               "end": end, "text": text, "counts": counts,
                               "length": sum(counts.values())})
                if len(result) > MAX_PASSAGES:
                    raise SearchError("passage count limit exceeded")
    return result


def search_snapshot(index, query, limit=5, require_all=False):
    """Rank embedded source bytes only; never claim a live source was verified."""
    validate_index(index)
    if not isinstance(query, str) or len(query) > 4096:
        raise SearchError("query exceeds 4096 characters")
    terms = sorted(set(tokens(query)))
    if not terms:
        raise SearchError("query must contain a word or address")
    if not 1 <= limit <= 50:
        raise SearchError("limit must be between 1 and 50")
    candidates = passages(index)
    count = len(candidates)
    average = sum(item["length"] for item in candidates) / count if count else 1
    frequencies = Counter(term for item in candidates for term in terms
                          if term in item["counts"])
    ranked = []
    for item in candidates:
        matched = [term for term in terms if term in item["counts"]]
        if not matched or (require_all and len(matched) != len(terms)):
            continue
        score = 0.0
        for term in matched:
            df, tf = frequencies[term], item["counts"][term]
            idf = math.log(1 + (count - df + 0.5) / (df + 0.5))
            score += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * item["length"] / average))
        ranked.append((score, item, matched))
    ranked.sort(key=lambda row: (-row[0], row[1]["document"]["path"], row[1]["start"]))
    hits, selected_spans = [], {}
    for score, item, matched in ranked:
        document = item["document"]
        name = document["path"]
        # Suppress overlapping windows of the same source in the result set.
        if any(item["start"] <= end and start <= item["end"]
               for start, end in selected_spans.get(name, [])):
            continue
        selected_spans.setdefault(name, []).append((item["start"], item["end"]))
        hits.append({"path": name, "line_start": item["start"], "line_end": item["end"],
                     "citation": f"{name}:{item['start']}-{item['end']}",
                     "sha256": document["sha256"], "source_verified": False,
                     "score": round(score, 8), "matched_terms": matched,
                     "text": item["text"]})
        if len(hits) >= limit:
            break
    return {"format": "evidence-search-results/v1", "query": query,
            "terms": terms, "require_all": require_all,
            "indexed_documents": len(index["documents"]),
            "indexed_passages": count, "hits": hits}


def search(index, query, root, limit=5, require_all=False):
    """Rank a snapshot, then verify every returned source against the live root."""
    root = workspace_path(root)
    if not root.is_dir():
        raise SearchError("corpus root must be a directory")
    result = search_snapshot(index, query, limit, require_all)
    verified = set()
    for hit in result["hits"]:
        name = hit["path"]
        if name not in verified:
            raw = read_bytes(workspace_path(root / name), MAX_FILE_BYTES)
            if digest(raw) != hit["sha256"]:
                raise SearchError(f"stale source: {name}; rebuild the index")
            verified.add(name)
        hit["source_verified"] = True
    return result


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="index UTF-8 .md/.txt/.rst files")
    build.add_argument("root")
    build.add_argument("--index", required=True)
    query = commands.add_parser("query", help="search and verify the cited sources")
    query.add_argument("root")
    query.add_argument("query")
    query.add_argument("--index", required=True)
    query.add_argument("--limit", type=int, default=5)
    query.add_argument("--all", action="store_true", help="require every query term in a passage")
    demo = commands.add_parser("demo", help="search bundled real ZTO/IMD observations; writes nothing")
    demo.add_argument("query", nargs="?", default="ZTO token decimals")
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            index = build_index(args.root)
            write_index(args.index, index)
            emit({"index": args.index, "documents": len(index["documents"]),
                  "passages": len(passages(index)), "format": FORMAT})
            return 0
        if args.command == "demo":
            root = workspace_path(Path(__file__).absolute().parent / "examples" / "docs")
            result = search(build_index(root), args.query, root)
        else:
            result = search(load_index(args.index), args.query, args.root,
                            args.limit, args.all)
        emit(result)
        return 0 if result["hits"] else 1
    except (SearchError, OSError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

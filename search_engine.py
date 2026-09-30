"""
search_engine.py
Core logic of the semantic search mini-project:
    load documents -> split into chunks -> create embeddings -> save/load index
    -> search (semantic / keyword / hybrid) -> optional reranking.

Used by app.py (web UI), search_cli.py (terminal) and evaluate.py (tests).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

# ----------------------------------------------------------------- settings
DOCS_DIR = Path("docs")
INDEX_DIR = Path("index")
EMBEDDING_MODEL = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
SUPPORTED_EXTENSIONS = {".md", ".txt", ".csv", ".pdf"}
MAX_WORDS = 120          # maximum words in one chunk
OVERLAP_WORDS = 30       # overlap when a long section is split into windows
DEFAULT_MIN_SCORE = 0.25 # semantic results below this cosine score are hidden
LOW_CONFIDENCE = 0.35    # warn the user if the best semantic score is below this
HYBRID_WEIGHT = 0.7      # hybrid score = 0.7 * semantic + 0.3 * keyword

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "is", "are",
    "was", "be", "it", "this", "that", "with", "as", "at", "by", "from", "how",
    "what", "which", "who", "why", "when", "do", "does", "can", "i", "my", "me",
    "you", "your", "we", "about", "into", "its", "if", "not", "no", "so", "than",
    "then", "there", "their", "they", "will", "would", "should", "could",
}


def tokenize(text: str) -> list[str]:
    """Lowercase words and numbers without stopwords (used for BM25 and highlighting)."""
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS]


# ----------------------------------------------------------------- chunks
@dataclass
class Chunk:
    chunk_id: int
    doc: str        # file name
    title: str      # document title
    section: str    # heading, page number or FAQ label
    chunk_no: int   # position of the chunk inside its document
    text: str
    file_type: str
    topic: str = ""

    @property
    def embed_text(self) -> str:
        """Text that is embedded: title and section give the chunk context."""
        return f"{self.title}. {self.section}. {self.text}"


def _clean(text: str) -> str:
    return " ".join(text.split())


def _windows(text: str) -> list[str]:
    """Split long text into overlapping windows of MAX_WORDS words."""
    words = text.split()
    if len(words) <= MAX_WORDS:
        return [text]
    step = MAX_WORDS - OVERLAP_WORDS
    pieces = []
    for start in range(0, len(words), step):
        pieces.append(" ".join(words[start:start + MAX_WORDS]))
        if start + MAX_WORDS >= len(words):
            break
    return pieces


def _read_markdown(path: Path):
    """Split Markdown at headings: each ## section becomes one unit."""
    title, current, buf, sections = path.stem.replace("_", " ").title(), "Introduction", [], []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.match(r"^#\s+", line):
            title = line.lstrip("#").strip()
            continue
        heading = re.match(r"^#{2,6}\s+(.*)", line)
        if heading:
            if "".join(buf).strip():
                sections.append((current, "\n".join(buf), ""))
            current, buf = heading.group(1).strip(), []
        else:
            buf.append(line)
    if "".join(buf).strip():
        sections.append((current, "\n".join(buf), ""))
    return title, sections


def _read_text(path: Path):
    """Split plain text at blank lines. A short first line without a full stop is a heading."""
    text = path.read_text(encoding="utf-8", errors="replace")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    title, sections = path.stem.replace("_", " ").title(), []
    for i, para in enumerate(paragraphs):
        lines = para.splitlines()
        if i == 0 and len(lines) == 1 and len(para) < 80 and not para.endswith("."):
            title = para.title() if para.isupper() else para
            continue
        first = lines[0].strip()
        if len(lines) > 1 and len(first) < 60 and not first.endswith((".", ":")):
            sections.append((first, " ".join(lines[1:]), ""))
        else:
            sections.append((f"Paragraph {len(sections) + 1}", para, ""))
    return title, sections


def _read_csv(path: Path):
    """One chunk per row. question/answer columns become a Q&A text; 'topic' becomes metadata."""
    text = path.read_text(encoding="utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    sections = []
    for n, row in enumerate(reader, start=1):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        topic = row.pop("topic", "")
        if row.get("question") and row.get("answer"):
            body = f"Q: {row['question']} A: {row['answer']}"
        else:
            body = ". ".join(f"{k}: {v}" for k, v in row.items() if v)
        if body:
            sections.append((f"Row {n}" + (f" ({topic})" if topic else ""), body, topic))
    return path.stem.replace("_", " ").upper() if len(path.stem) <= 4 else path.stem.title(), sections


def _read_pdf(path: Path):
    """One unit per PDF page (long pages are split into windows later)."""
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    sections = []
    for i, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        if page_text:
            sections.append((f"Page {i}", page_text, ""))
    return path.stem.replace("_", " ").title(), sections


READERS = {".md": _read_markdown, ".txt": _read_text, ".csv": _read_csv, ".pdf": _read_pdf}


def load_documents(docs_dir: Path = DOCS_DIR) -> tuple[list[Chunk], list[str]]:
    """Read every supported file in docs_dir and return (chunks, warnings)."""
    docs_dir = Path(docs_dir)
    if not docs_dir.is_dir():
        raise FileNotFoundError(
            f"Document folder '{docs_dir}' was not found. Create it and add .md, .txt, "
            f".csv or .pdf files (or run: python create_docs.py)."
        )
    chunks: list[Chunk] = []
    warnings: list[str] = []
    for path in sorted(p for p in docs_dir.iterdir() if p.is_file()):
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            warnings.append(f"Skipped {path.name}: unsupported file type.")
            continue
        try:
            title, sections = READERS[ext](path)
        except Exception as exc:  # broken or unreadable file
            warnings.append(f"Skipped {path.name}: could not read the file ({exc}).")
            continue
        if not sections:
            warnings.append(f"Skipped {path.name}: the file is empty.")
            continue
        n = 0
        for section, text, topic in sections:
            for piece in _windows(_clean(text)):
                chunks.append(Chunk(len(chunks), path.name, title, section, n, piece, ext[1:], topic))
                n += 1
    if not chunks:
        raise ValueError(
            f"No readable documents found in '{docs_dir}'. Supported types: "
            f"{', '.join(sorted(SUPPORTED_EXTENSIONS))}."
        )
    return chunks, warnings


def _fingerprint(docs_dir: Path, model_name: str) -> str:
    """Hash of the documents, model and chunk settings. Changes => index is rebuilt."""
    h = hashlib.sha256(f"{model_name}|{MAX_WORDS}|{OVERLAP_WORDS}|v1".encode())
    for p in sorted(Path(docs_dir).iterdir()):
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS:
            h.update(p.name.encode())
            h.update(p.read_bytes())
    return h.hexdigest()


# ----------------------------------------------------------------- engine
class SearchEngine:
    def __init__(self, docs_dir=DOCS_DIR, index_dir=INDEX_DIR, model_name=EMBEDDING_MODEL):
        self.docs_dir = Path(docs_dir)
        self.index_dir = Path(index_dir)
        self.model_name = model_name
        self._model = None
        self._reranker = None
        self.chunks: list[Chunk] = []
        self.embeddings: np.ndarray | None = None
        self.bm25: BM25Okapi | None = None
        self.warnings: list[str] = []
        self.index_status = ""

    @property
    def model(self):
        if self._model is None:  # loaded only when needed
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    @property
    def doc_names(self) -> list[str]:
        return sorted({c.doc for c in self.chunks})

    # ---- index
    def build_or_load(self, force_rebuild: bool = False) -> str:
        self.chunks, self.warnings = load_documents(self.docs_dir)
        fingerprint = _fingerprint(self.docs_dir, self.model_name)
        if not force_rebuild and self._load_index(fingerprint):
            self.index_status = "loaded from disk"
        else:
            texts = [c.embed_text for c in self.chunks]
            self.embeddings = self.model.encode(
                texts, batch_size=32, normalize_embeddings=True,
                convert_to_numpy=True, show_progress_bar=False,
            ).astype(np.float32)
            self._save_index(fingerprint)
            self.index_status = "built and saved"
        self.bm25 = BM25Okapi([tokenize(c.embed_text) for c in self.chunks])
        return self.index_status

    def _save_index(self, fingerprint: str) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        np.save(self.index_dir / "embeddings.npy", self.embeddings)
        (self.index_dir / "chunks.json").write_text(
            json.dumps([asdict(c) for c in self.chunks], indent=2, ensure_ascii=False), encoding="utf-8")
        (self.index_dir / "meta.json").write_text(json.dumps({
            "fingerprint": fingerprint, "model": self.model_name,
            "num_chunks": len(self.chunks), "dimensions": int(self.embeddings.shape[1]),
        }, indent=2), encoding="utf-8")

    def _load_index(self, fingerprint: str) -> bool:
        try:
            meta = json.loads((self.index_dir / "meta.json").read_text(encoding="utf-8"))
            if meta.get("fingerprint") != fingerprint:
                return False
            embeddings = np.load(self.index_dir / "embeddings.npy")
            if embeddings.shape[0] != len(self.chunks):
                return False
            self.embeddings = embeddings
            return True
        except (OSError, ValueError):
            return False

    # ---- scoring
    def _semantic_scores(self, query: str) -> np.ndarray:
        q = self.model.encode([query], normalize_embeddings=True,
                              convert_to_numpy=True, show_progress_bar=False)[0]
        # Vectors are normalized to length 1, so the dot product equals cosine similarity.
        return self.embeddings @ q

    def _keyword_scores(self, query: str) -> np.ndarray:
        tokens = tokenize(query)
        if not tokens:
            return np.zeros(len(self.chunks))
        return np.asarray(self.bm25.get_scores(tokens), dtype=float)

    def _rerank_scores(self, query: str, ids: list[int]) -> np.ndarray:
        if self._reranker is None:
            from sentence_transformers import CrossEncoder
            self._reranker = CrossEncoder(RERANK_MODEL)
        pairs = [(query, self.chunks[i].embed_text) for i in ids]
        return np.asarray(self._reranker.predict(pairs, show_progress_bar=False), dtype=float)

    # ---- search
    def search(self, query: str, mode: str = "semantic", top_k: int = 5,
               min_score: float = DEFAULT_MIN_SCORE, docs: list[str] | None = None,
               rerank: bool = False) -> list[dict]:
        """Return the top_k results as dicts (rank, score, chunk metadata...)."""
        if self.embeddings is None or self.bm25 is None:
            raise RuntimeError("The index is not ready. Call build_or_load() first.")
        query = (query or "").strip()
        if not query:
            raise ValueError("The query is empty. Type something to search for.")
        if mode not in ("semantic", "keyword", "hybrid"):
            raise ValueError(f"Unknown search mode '{mode}'. Use semantic, keyword or hybrid.")
        top_k = max(1, min(int(top_k), len(self.chunks)))

        sem = self._semantic_scores(query) if mode in ("semantic", "hybrid") else None
        kw = self._keyword_scores(query) if mode in ("keyword", "hybrid") else None
        if mode == "semantic":
            scores = sem
        elif mode == "keyword":
            scores = kw
        else:
            kw_norm = kw / kw.max() if kw.max() > 0 else np.zeros_like(kw)
            scores = HYBRID_WEIGHT * np.clip(sem, 0, 1) + (1 - HYBRID_WEIGHT) * kw_norm

        mask = np.ones(len(self.chunks), dtype=bool)
        if docs:
            allowed = set(docs)
            mask &= np.array([c.doc in allowed for c in self.chunks])
        mask &= (scores > 0) if mode == "keyword" else (scores >= min_score)
        candidates = [int(i) for i in np.argsort(-scores, kind="stable") if mask[i]]

        rerank_map: dict[int, float] = {}
        if rerank and candidates:
            pool = candidates[:max(top_k * 3, 10)]
            rr = self._rerank_scores(query, pool)
            rerank_map = {pool[j]: float(rr[j]) for j in range(len(pool))}
            candidates = [pool[j] for j in np.argsort(-rr, kind="stable")]

        results = []
        for rank, i in enumerate(candidates[:top_k], start=1):
            r = asdict(self.chunks[i])
            r.update(rank=rank, score=float(scores[i]), mode=mode)
            if sem is not None:
                r["semantic_score"] = float(sem[i])
            if kw is not None:
                r["keyword_score"] = float(kw[i])
            if i in rerank_map:
                r["rerank_score"] = rerank_map[i]
            results.append(r)
        return results

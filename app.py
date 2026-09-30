"""
app.py - web interface for the semantic search mini-project.
Run:  streamlit run app.py
"""
import html
import re

import streamlit as st

from search_engine import (DEFAULT_MIN_SCORE, EMBEDDING_MODEL, LOW_CONFIDENCE,
                           SearchEngine, tokenize)

st.set_page_config(page_title="Automation Notes Search", page_icon="🔎", layout="wide")

EXAMPLES = [
    "How can I tell when a machine part is about to fail?",
    "keep people safe around robot arms",
    "74LS08",
    "save electricity on fans and pumps",
    "security",
    "best pizza recipe",
]
MODES = {
    "Semantic (embeddings)": "semantic",
    "Keyword (BM25)": "keyword",
    "Hybrid (semantic + keyword)": "hybrid",
    "Compare semantic vs keyword": "compare",
}
SCORE_LABEL = {"semantic": "Cosine similarity", "keyword": "BM25 score", "hybrid": "Hybrid score"}


@st.cache_resource(show_spinner="Loading the model and index (the first run downloads the model)...")
def load_engine() -> SearchEngine:
    engine = SearchEngine()
    engine.build_or_load()
    return engine


def highlight(text: str, query: str) -> str:
    """Mark query words inside the passage."""
    safe = html.escape(text)
    terms = sorted({t for t in tokenize(query) if len(t) > 2}, key=len, reverse=True)
    if not terms:
        return safe
    pattern = re.compile(r"\b(" + "|".join(map(re.escape, terms)) + r")\w*", re.IGNORECASE)
    return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", safe)


def show_results(results: list[dict], query: str, mode: str) -> None:
    if not results:
        st.warning("No results found. Try other words, lower the minimum score, "
                   "or remove the document filter.")
        return
    if mode in ("semantic", "hybrid") and results[0]["score"] < LOW_CONFIDENCE:
        st.warning(f"Low confidence: the best score is {results[0]['score']:.2f}. "
                   "These passages may not answer the query.")
    for r in results:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{r['rank']}. {r['title']}**  \n{r['section']}")
            right.metric(SCORE_LABEL[mode], f"{r['score']:.3f}")
            if mode != "keyword":
                st.progress(min(max(r["score"], 0.0), 1.0))
            st.markdown(highlight(r["text"], query), unsafe_allow_html=True)
            info = [f"File: {r['doc']}", f"chunk {r['chunk_no']}"]
            if r.get("topic"):
                info.append(f"topic: {r['topic']}")
            if mode == "hybrid":
                info.append(f"semantic {r['semantic_score']:.3f}, BM25 {r['keyword_score']:.2f}")
            if "rerank_score" in r:
                info.append(f"rerank score {r['rerank_score']:.2f}")
            st.caption(" | ".join(info))


# ----------------------------------------------------------------- page
st.title("🔎 Search automation course notes")
st.write("Find passages by meaning, even when your words differ from the text.")

try:
    engine = load_engine()
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"The model or index could not be loaded: {exc}. "
             "Check your internet connection for the first model download.")
    st.stop()

with st.sidebar:
    st.header("Settings")
    mode = MODES[st.radio("Search mode", list(MODES))]
    top_k = st.slider("Number of results", 1, 10, 5)
    min_score = st.slider("Minimum similarity (semantic and hybrid)", 0.0, 0.8,
                          DEFAULT_MIN_SCORE, 0.05)
    docs = st.multiselect("Only search these documents", engine.doc_names,
                          placeholder="All documents")
    rerank = st.checkbox("Rerank with a cross-encoder",
                         help="Re-scores the best candidates with a second model. "
                              "Slower; downloads the model on first use.")
    st.divider()
    st.caption(f"Model: {EMBEDDING_MODEL}")
    st.caption(f"{len(engine.doc_names)} documents, {len(engine.chunks)} chunks, "
               f"index {engine.index_status}")
    if st.button("Rebuild index"):
        with st.spinner("Rebuilding the index..."):
            engine.build_or_load(force_rebuild=True)
        st.success("Index rebuilt.")
    for warning in engine.warnings:
        st.warning(warning)

if "query" not in st.session_state:
    st.session_state.query = ""


def use_example(q: str) -> None:
    st.session_state.query = q


st.write("Try an example:")
for col, example in zip(st.columns(3) * 2, EXAMPLES):
    col.button(example, on_click=use_example, args=(example,))

query = st.text_input("Search query", key="query",
                      placeholder="e.g. how do I notice a broken sensor cable?")

if not query.strip():
    st.info("Type a query and press Enter, or pick an example.")
    st.stop()

try:
    with st.spinner("Searching..."):
        if mode == "compare":
            sem = engine.search(query, "semantic", top_k, min_score, docs, rerank)
            kw = engine.search(query, "keyword", top_k, min_score, docs, rerank)
        else:
            results = engine.search(query, mode, top_k, min_score, docs, rerank)
except ValueError as exc:
    st.warning(str(exc))
    st.stop()

if mode == "compare":
    shared = {r["chunk_id"] for r in sem} & {r["chunk_id"] for r in kw}
    st.caption(f"{len(shared)} passage(s) appear in both result lists.")
    col_sem, col_kw = st.columns(2)
    with col_sem:
        st.subheader("Semantic search")
        show_results(sem, query, "semantic")
    with col_kw:
        st.subheader("Keyword search (BM25)")
        show_results(kw, query, "keyword")
else:
    show_results(results, query, mode)

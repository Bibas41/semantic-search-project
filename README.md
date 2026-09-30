# Semantic Search for Automation Course Notes

Mini-project for **Applied AI Programming (TX00FM14)**, Metropolia University of Applied Sciences
Author: **Bibas Dhital**

**Demo video:** ADD-YOUTUBE-LINK-HERE

A semantic search application that finds passages in a small collection of industrial-automation
notes **by meaning**, not only by exact words. A query such as *"how can I tell when a machine part
is about to fail"* finds the predictive maintenance notes even though they use different words.
The app also runs keyword search (BM25) side by side, so the two approaches can be compared.

## Features

- Loads **Markdown, TXT, CSV and PDF** files from the `docs/` folder
- Splits documents into passages (by heading, paragraph, CSV row or PDF page, with sliding windows for long text)
- Creates embeddings with a ready-made **Sentence Transformers** model that runs locally
- Ranks passages by **cosine similarity** and shows the score for every result
- **Keyword search (BM25)**, **hybrid search**, and a **side-by-side comparison** mode
- Optional **reranking** with a cross-encoder
- **Saves and reloads the index**; it is rebuilt automatically when documents change
- **Filter by document**, adjustable number of results and minimum score
- **Highlights** query words in the returned passages
- Handles empty queries, missing folders, empty/unsupported files, no results and low-confidence results
- Web interface (Streamlit), terminal interface, and an **evaluation script** with 25 test queries

## Project structure

```
semantic-search-project/
├── app.py                  # Streamlit web interface
├── search_engine.py        # loading, chunking, embeddings, index, search, ranking
├── search_cli.py           # terminal interface
├── evaluate.py             # test queries, semantic vs keyword comparison
├── create_docs.py          # generates the synthetic document collection
├── docs/                   # the 11 test documents
├── results/                # evaluation_results.md (example queries and returned results)
├── index/                  # saved index (created automatically, not in Git)
├── requirements.txt
└── README.md
```

## Setup and running

Requires Python 3.9–3.12. The first run downloads the embedding model (about 90 MB) from
Hugging Face; after that everything runs offline.

```bash
git clone https://github.com/Bibas41/semantic-search-project.git
cd semantic-search-project
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
# source .venv/bin/activate         # macOS / Linux
pip install -r requirements.txt
```

| What | Command |
|---|---|
| Web app (recommended) | `streamlit run app.py` (opens http://localhost:8501) |
| Terminal search | `python search_cli.py "how do I notice a broken sensor cable"` |
| Terminal, keyword mode | `python search_cli.py --mode keyword "74LS08"` |
| Interactive terminal | `python search_cli.py` |
| Run the evaluation | `python evaluate.py` |
| Recreate the documents | `python create_docs.py` |

To search your own files, put `.md`, `.txt`, `.csv` or `.pdf` files in `docs/`. The index is
rebuilt automatically when the files change (or press **Rebuild index** in the app).

## How it works

```
docs/ -> load files -> split into chunks -> embed chunks (384-d vectors) -> save index/
query -> embed query -> cosine similarity with every chunk -> filter + rank -> (rerank) -> show top k
```

### Embedding model, library and services

- **Library:** [Sentence Transformers](https://sbert.net/) (runs locally on the CPU, no cloud API).
- **Embedding model:** [`multi-qa-MiniLM-L6-cos-v1`](https://huggingface.co/sentence-transformers/multi-qa-MiniLM-L6-cos-v1).
  It maps text to 384-dimensional vectors and was trained on 215 million question–answer pairs,
  which makes it suited to **asymmetric search**: a short query searching longer passages. It is
  small and fast enough for a laptop. The model can be changed with `EMBEDDING_MODEL` in
  `search_engine.py` (for example `all-MiniLM-L6-v2`, a general-purpose model better suited to
  symmetric sentence similarity).
- **Reranker (optional):** [`cross-encoder/ms-marco-MiniLM-L-6-v2`](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2).
  A cross-encoder reads the query and passage *together*, which is more accurate but too slow to
  run on every chunk, so it only re-scores the best candidates.
- **Keyword search:** BM25 via [`rank-bm25`](https://github.com/dorianbrown/rank_bm25).
- **Interface:** [Streamlit](https://streamlit.io/).

### Documents indexed

Eleven **synthetic** course-style documents about smart automation, created for this project with
`create_docs.py`. They mix formats so that every loader is tested.

| File | Topic | Format |
|---|---|---|
| plc_basics.md | PLCs, scan cycle, IEC 61131-3 languages | Markdown |
| industrial_sensors.md | Proximity, optical, ultrasonic, PT100, 4–20 mA | Markdown |
| predictive_maintenance.md | Maintenance strategies, vibration, RUL | Markdown |
| mqtt_iot_communication.md | Publish/subscribe, QoS, MQTT security | Markdown |
| opc_ua.md | Information model, security, OPC UA vs MQTT | Markdown |
| robot_safety.md | Risk assessment, guarding, cobots, lockout/tagout | Markdown |
| machine_vision_quality.md | Cameras, lighting, CNN inspection | Markdown |
| digital_twin.md | Virtual commissioning, simulation | Markdown |
| energy_efficiency_motors.md | IE classes, VFDs, compressed air | Markdown |
| logic_gates_74ls.txt | 74LS chips, Karnaugh maps (contains part codes) | TXT |
| faq.csv | 10 short questions and answers with a `topic` column | CSV |

The collection deliberately includes part numbers and standard codes (74LS08, ISO 10218, port 8883),
overlapping topics (security in MQTT and OPC UA) and short FAQ rows, so that both easy and difficult
cases can be tested.

### How documents are split and prepared

| Format | Splitting rule |
|---|---|
| Markdown | One chunk per `##` section; the `#` heading is the document title |
| TXT | Paragraphs separated by blank lines; a short first line without a full stop is used as the heading |
| CSV | One chunk per row (`Q: ... A: ...`); the `topic` column is kept as metadata |
| PDF | One unit per page (text extracted with `pypdf`) |

- Whitespace is normalised.
- Any unit longer than **120 words** is split into **sliding windows of 120 words with 30 words overlap**,
  so no passage exceeds the length the model handles well and no sentence is lost at a boundary.
- Before embedding, each chunk is prefixed with its **document title and section heading**
  (for example *"OPC UA. Security. Security is built into..."*). This gives short chunks context
  (a paragraph that only says "it" still knows it is about OPC UA).
- Each chunk keeps metadata: file name, title, section, chunk number, file type and topic.

Chunking by section was chosen because the headings mark natural units of meaning. Whole documents
would give vague matches (one vector for five topics); single sentences would lose context.

### How similarity is calculated

The query and every chunk are turned into vectors that are **normalised to length 1**. Similarity is
**cosine similarity**:

cos(q, d) = (q · d) / (‖q‖ ‖d‖)

Because the vectors already have length 1, this equals the dot product, so all chunk scores are
computed at once with one matrix–vector multiplication in NumPy (`embeddings @ query`). Scores range
from -1 to 1; higher means more similar according to the model. This is exact search over all
vectors, which is fast for a small collection; a FAISS index or vector database would be the next
step for tens of thousands of chunks.

### How results are ranked

1. **Semantic mode:** chunks are sorted by cosine similarity (highest first).
2. Chunks below the **minimum score (default 0.25)** are removed, so unrelated queries return
   "No results" instead of random passages. The app warns when the best score is **below 0.35**
   (low confidence).
3. Optional **document filter** limits the search to selected files.
4. The top *k* results (default 5) are shown with rank, score bar, file, section and chunk number.
5. **Keyword mode:** BM25 score; only chunks sharing at least one query word are shown.
6. **Hybrid mode:** `0.7 × cosine + 0.3 × (BM25 / best BM25)`, combining meaning with exact terms.
7. **Reranking (optional):** the best 10–15 candidates are re-scored by the cross-encoder and
   re-ordered.

### Saving and reloading the index

The embeddings are saved to `index/embeddings.npy`, the chunks and metadata to `index/chunks.json`,
and `index/meta.json` stores a SHA-256 fingerprint of the documents, model name and chunk settings.
On start-up the index is reloaded if the fingerprint matches; otherwise it is rebuilt.

### Error handling

| Situation | Behaviour |
|---|---|
| Empty query | Message asking for a query; no search is run |
| `docs/` folder missing | Clear error explaining how to create it |
| No readable documents | Error listing the supported file types |
| Empty, unsupported or broken file | File is skipped and a warning is shown |
| No result above the threshold | "No results" with tips (other words, lower score, remove filter) |
| Weak best match | Low-confidence warning |
| Model cannot be downloaded | Error message pointing to the internet connection |

## Testing and results

`evaluate.py` runs **25 test queries** in seven categories against semantic, keyword and hybrid
search and records where the first correct document appears:

- **Paraphrase:** meaning is the same but the words are different ("keep workers from getting hurt by automated arms")
- **Synonym:** "motor speed controller" for variable frequency drive, "fault prediction"
- **Exact term / code:** "74LS08", "port 8883", "IEC 61131-3", "ISO 10218"
- **Question:** natural questions ("What happens during a PLC scan cycle?")
- **Ambiguous:** one-word queries with several valid answers ("security", "light", "model")
- **Poor / typo:** "compresed air leeks", "machine broke what do"
- **Out of domain:** "best pizza recipe", should return nothing

<!-- EVAL_START -->
_Run `python evaluate.py` to fill in this section automatically._
<!-- EVAL_END -->

The full list of queries with the top 3 returned passages and scores for each search mode is in
[results/evaluation_results.md](results/evaluation_results.md).

## Semantic search vs keyword search

| | Keyword search (BM25) | Semantic search (embeddings) |
|---|---|---|
| Matches | Shared words, weighted by how rare they are | Meaning, via vectors from a trained model |
| Strong at | Codes, part numbers, names, exact terms | Paraphrases, synonyms, natural questions |
| Weak at | Different wording, synonyms, typos | Exact codes and numbers, very short queries |
| Unrelated query | Usually returns nothing (no shared words) | Always finds a "nearest" passage, so a threshold is needed |
| Explainability | Easy: you can see the matching words | Harder: a score without a visible reason |

**Queries that work well with semantic search:** paraphrases and questions written in the user's
own words, such as *"try out the control program before the real line exists"* (finds virtual
commissioning in the digital twin notes) or *"notice that a cable from a sensor is cut"* (finds the
4–20 mA live-zero explanation). Keyword search misses these when no important word is shared.

**Queries that are difficult:**
- **Codes and numbers** (*"74LS08"*, *"port 8883"*): the embedding model splits them into sub-word
  pieces and has no real understanding of which chip is which, so a passage about a *different*
  chip can score almost as high. Keyword search is reliable here, which is why hybrid mode exists.
- **One-word ambiguous queries** (*"security"*, *"model"*): results are spread across several
  documents; the ranking is reasonable but it cannot know which meaning the user wants.
- **Vague queries** (*"machine broke what do"*): scores are low and the top result is related but
  may not answer the question.
- **Out-of-domain queries:** semantic search always returns the nearest passage; only the
  minimum-score threshold prevents nonsense answers, and the right threshold depends on the model.
- **Typos:** BM25 fails completely on misspelled words; semantic search is more tolerant because
  sub-word pieces still overlap, but scores drop.

In practice a **hybrid** approach combines the strengths: meaning from embeddings and precision on
exact terms from BM25. The evaluation table above compares the three modes on the same queries.

## Limitations and data quality

- **Small collection:** 11 short documents; scores and thresholds would need re-tuning for a larger
  or different collection.
- **Chunking trade-offs:** section-based chunks work well for these structured notes; badly
  formatted text (no headings, scanned PDFs without a text layer) would give worse chunks.
- **Scores are relative, not truth:** a high cosine score means "similar according to the model",
  not "correct answer". The threshold (0.25) was chosen by looking at the test queries.
- **Language and domain:** the model is trained mainly on English web data; Finnish queries or very
  specialised jargon would work worse.
- **Data quality:** outdated or duplicated documents would be returned just as confidently as good
  ones. A real system needs owners, dates and a process for removing old documents.
- **Synthetic data:** the documents are clean and well structured, which makes search easier than
  with real, messy notes.

## Privacy, copyright and responsible use

- **Only appropriate documents:** all documents are synthetic course-style notes created for this
  project. They contain no personal, confidential or copyrighted material.
- **No data leaves the computer:** the embedding model and reranker run **locally**; documents and
  queries are never sent to a cloud API. Only the model weights are downloaded once from Hugging Face
  (both models are released under the Apache 2.0 licence).
- **Embeddings are sensitive too:** stored embeddings can partly reveal the content they were made
  from, so the `index/` folder is excluded from Git and should be protected like the documents
  themselves.
- **Access control:** anyone who can run the app can search every indexed document. With real
  company or course documents, access rules and a way to exclude files would be needed.
- **Source awareness:** every result shows its file, section and chunk number, so users can check
  the original text instead of trusting a score.
- **Copyright:** real course material or published documents should only be indexed with
  permission and should not be uploaded to cloud services without understanding their data handling.

## AI assistance

As encouraged in the course, AI assistance (Claude) was used for code, the synthetic documents and
drafting this README. Scoping, testing, checking the results and final decisions were done by the
author.

## References

- Reimers, N. & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.* EMNLP. https://arxiv.org/abs/1908.10084
- Sentence Transformers documentation: https://sbert.net/
- Semantic search with Sentence Transformers: https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html
- Model card, multi-qa-MiniLM-L6-cos-v1: https://huggingface.co/sentence-transformers/multi-qa-MiniLM-L6-cos-v1
- Model card, ms-marco-MiniLM-L-6-v2: https://huggingface.co/cross-encoder/ms-marco-MiniLM-L-6-v2
- Robertson, S. & Zaragoza, H. (2009). *The Probabilistic Relevance Framework: BM25 and Beyond.*
- rank-bm25: https://github.com/dorianbrown/rank_bm25
- scikit-learn, cosine similarity: https://scikit-learn.org/stable/modules/metrics.html
- FAISS: https://faiss.ai/
- Streamlit documentation: https://docs.streamlit.io/

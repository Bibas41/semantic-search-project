"""
search_cli.py - search from the terminal.

Examples:
    python search_cli.py "how do I detect a broken sensor cable"
    python search_cli.py --mode keyword "74LS08"
    python search_cli.py            (interactive mode, type 'quit' to exit)
"""
import argparse
import sys

from search_engine import DEFAULT_MIN_SCORE, SearchEngine


def print_results(results: list[dict], mode: str) -> None:
    if not results:
        print("  No results. Try other words or a lower --min-score.\n")
        return
    for r in results:
        print(f"  {r['rank']}. [{r['score']:.3f}] {r['doc']} > {r['section']} (chunk {r['chunk_no']})")
        text = r["text"] if len(r["text"]) <= 200 else r["text"][:200] + "..."
        print(f"     {text}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic search over the docs folder.")
    parser.add_argument("query", nargs="*", help="search query (leave empty for interactive mode)")
    parser.add_argument("--mode", choices=["semantic", "keyword", "hybrid"], default="semantic")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE)
    parser.add_argument("--rerank", action="store_true", help="rerank with a cross-encoder")
    parser.add_argument("--rebuild", action="store_true", help="rebuild the index")
    args = parser.parse_args()

    try:
        engine = SearchEngine()
        status = engine.build_or_load(force_rebuild=args.rebuild)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)
    for warning in engine.warnings:
        print(f"Warning: {warning}")
    print(f"Index {status}: {len(engine.doc_names)} documents, {len(engine.chunks)} chunks.\n")

    def run(q: str) -> None:
        try:
            print_results(engine.search(q, args.mode, args.top_k, args.min_score,
                                        rerank=args.rerank), args.mode)
        except ValueError as exc:
            print(f"  {exc}\n")

    if args.query:
        run(" ".join(args.query))
        return
    while True:
        q = input("Query (or 'quit'): ").strip()
        if q.lower() in ("quit", "exit", "q"):
            break
        run(q)


if __name__ == "__main__":
    main()

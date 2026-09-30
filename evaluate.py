"""
evaluate.py - tests the search with varied queries and compares
semantic, keyword (BM25) and hybrid search.

Writes results/evaluation_results.md and updates the results section in README.md.
Run:  python evaluate.py
"""
from datetime import date
from pathlib import Path

from search_engine import DEFAULT_MIN_SCORE, EMBEDDING_MODEL, SearchEngine

# (category, query, documents that count as a correct answer; [] = should find nothing)
TESTS = [
    ("Paraphrase", "How can I tell when a machine part is about to fail?", ["predictive_maintenance.md"]),
    ("Paraphrase", "keep workers from getting hurt by automated arms", ["robot_safety.md"]),
    ("Paraphrase", "send small sensor messages over a weak network connection", ["mqtt_iot_communication.md"]),
    ("Paraphrase", "try out the control program before the real line exists", ["digital_twin.md"]),
    ("Paraphrase", "cameras that spot scratches on products", ["machine_vision_quality.md"]),
    ("Paraphrase", "make a boolean expression shorter", ["logic_gates_74ls.txt"]),
    ("Paraphrase", "notice that a cable from a sensor is cut", ["industrial_sensors.md", "faq.csv"]),
    ("Synonym", "motor speed controller", ["energy_efficiency_motors.md"]),
    ("Synonym", "tank fill height measurement", ["industrial_sensors.md"]),
    ("Synonym", "fault prediction", ["predictive_maintenance.md"]),
    ("Synonym", "machines from different manufacturers talking to each other", ["opc_ua.md"]),
    ("Exact term / code", "74LS08", ["logic_gates_74ls.txt"]),
    ("Exact term / code", "port 8883", ["mqtt_iot_communication.md", "faq.csv"]),
    ("Exact term / code", "IEC 61131-3", ["plc_basics.md"]),
    ("Exact term / code", "ISO 10218", ["robot_safety.md"]),
    ("Question", "What happens during a PLC scan cycle?", ["plc_basics.md"]),
    ("Question", "Which QoS level avoids duplicate messages?", ["mqtt_iot_communication.md", "faq.csv"]),
    ("Ambiguous", "security", ["mqtt_iot_communication.md", "opc_ua.md"]),
    ("Ambiguous", "light", ["industrial_sensors.md", "machine_vision_quality.md", "robot_safety.md"]),
    ("Ambiguous", "model", ["digital_twin.md", "predictive_maintenance.md", "opc_ua.md",
                            "machine_vision_quality.md"]),
    ("Poor / typo", "compresed air leeks", ["energy_efficiency_motors.md"]),
    ("Poor / typo", "machine broke what do", ["predictive_maintenance.md"]),
    ("Poor / typo", "stuff about gates chips", ["logic_gates_74ls.txt"]),
    ("Out of domain", "best pizza recipe", []),
    ("Out of domain", "who won the football match yesterday", []),
]
MODES = ["semantic", "keyword", "hybrid"]
RESULTS_FILE = Path("results") / "evaluation_results.md"
README = Path("README.md")


def first_hit(results: list[dict], expected: list[str]):
    for r in results:
        if r["doc"] in expected:
            return r["rank"]
    return None


def top3_table(results: list[dict]) -> list[str]:
    if not results:
        return ["_No results above the threshold._", ""]
    lines = ["| Rank | Document | Section | Score |", "|---|---|---|---|"]
    for r in results[:3]:
        lines.append(f"| {r['rank']} | {r['doc']} | {r['section']} | {r['score']:.3f} |")
    return lines + [""]


def main() -> None:
    engine = SearchEngine()
    status = engine.build_or_load()
    print(f"Index {status}: {len(engine.doc_names)} documents, {len(engine.chunks)} chunks.")

    stats = {m: {"hit1": 0, "hit3": 0, "rr": 0.0, "n": 0, "ood_ok": 0, "ood_n": 0} for m in MODES}
    per_category: dict[tuple[str, str], list[int]] = {}
    query_rows, details = [], []

    for category, query, expected in TESTS:
        row = [category, f'"{query}"', ", ".join(expected) or "nothing"]
        details += [f"### {category}: \"{query}\"",
                    f"Expected: {', '.join(expected) or 'no relevant result (out of domain)'}", ""]
        for mode in MODES:
            s = stats[mode]
            if expected:
                results = engine.search(query, mode, top_k=5, min_score=-1.0)
                rank = first_hit(results, expected)
                s["n"] += 1
                s["hit1"] += rank == 1
                s["hit3"] += bool(rank and rank <= 3)
                s["rr"] += 1 / rank if rank else 0
                ok = bool(rank and rank <= 3)
                row.append(str(rank) if rank else "miss")
            else:
                results = engine.search(query, mode, top_k=5, min_score=DEFAULT_MIN_SCORE)
                ok = not results
                s["ood_n"] += 1
                s["ood_ok"] += ok
                row.append("rejected" if ok else f"returned {results[0]['doc']}")
            cell = per_category.setdefault((category, mode), [0, 0])
            cell[0] += ok
            cell[1] += 1
            if mode in ("semantic", "keyword"):
                details.append(f"**{mode.capitalize()} search**")
                details += top3_table(results)
        if not expected:
            best = engine.search(query, "semantic", top_k=1, min_score=-1.0)[0]
            details += [f"Best raw semantic score: {best['score']:.3f} ({best['doc']}), "
                        f"threshold is {DEFAULT_MIN_SCORE}.", ""]
        query_rows.append("| " + " | ".join(row) + " |")

    # summary tables
    summary = ["| Mode | Hit@1 | Hit@3 | MRR | Out-of-domain queries rejected |",
               "|---|---|---|---|---|"]
    for mode in MODES:
        s = stats[mode]
        summary.append(f"| {mode} | {s['hit1']}/{s['n']} | {s['hit3']}/{s['n']} | "
                       f"{s['rr'] / s['n']:.2f} | {s['ood_ok']}/{s['ood_n']} |")
    categories = list(dict.fromkeys(c for c, _, _ in TESTS))
    cat_table = ["| Category | " + " | ".join(MODES) + " |", "|---|" + "---|" * len(MODES)]
    for cat in categories:
        cells = [f"{per_category[(cat, m)][0]}/{per_category[(cat, m)][1]}" for m in MODES]
        cat_table.append(f"| {cat} | " + " | ".join(cells) + " |")

    header = [
        f"_Generated by `python evaluate.py` on {date.today()} with `{EMBEDDING_MODEL}`, "
        f"{len(engine.chunks)} chunks from {len(engine.doc_names)} documents, "
        f"{len(TESTS)} test queries._", "",
        "**Overall** (Hit@k = a correct document is in the top k; MRR = mean reciprocal rank)", "",
        *summary, "",
        "**Per category** (correct document in top 3; out-of-domain = correctly returned nothing)", "",
        *cat_table, "",
    ]
    report = [
        "# Evaluation results", "", *header,
        "## Rank of the first correct document per query", "",
        "| Category | Query | Expected | Semantic | Keyword | Hybrid |",
        "|---|---|---|---|---|---|", *query_rows, "",
        "## Top 3 results per query", "", *details,
    ]
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    RESULTS_FILE.write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote {RESULTS_FILE}")

    # update README between the markers
    start, end = "<!-- EVAL_START -->", "<!-- EVAL_END -->"
    if README.exists():
        text = README.read_text(encoding="utf-8")
        if start in text and end in text:
            before, rest = text.split(start, 1)
            after = rest.split(end, 1)[1]
            block = "\n".join(header + [f"Full per-query results: [{RESULTS_FILE.as_posix()}]"
                                        f"({RESULTS_FILE.as_posix()})"])
            README.write_text(f"{before}{start}\n{block}\n{end}{after}", encoding="utf-8")
            print("Updated the results section in README.md")

    print("\n" + "\n".join(summary))


if __name__ == "__main__":
    main()

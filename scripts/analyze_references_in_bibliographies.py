#!/usr/bin/env python3
"""Analyze cited references inside bibliographies of a sampled set of PDFs.

Goal:
- Sample 500 diverse papers from Qdrant (clustered by embedding)
- For each PDF, extract the References section (fast mode: last 3 pages)
- Parse individual reference entries and extract:
  - cited year (best-effort)
  - venue/journal string (best-effort)
  - publisher family bucket (heuristic)

Outputs (written to output/):
- references_analysis_summary.json
- references_cited_years_hist.csv
- references_top_venues.csv
- references_top_publisher_families.csv
- references_per_paper_stats.csv
- references_sample_manifest.csv
"""

import argparse
import csv
import json
import os
import re
import time
from datetime import datetime
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
COLLECTION_NAME = "academic_papers_full_specter2"
METADATA_FILE = "pdf_metadata.json"
OUTPUT_DIR = "output"
PDF_FOLDER = "downloaded_pdfs"

CHECKPOINT_DIR = os.path.join(OUTPUT_DIR, "checkpoints")
PROGRESS_JSONL = os.path.join(CHECKPOINT_DIR, "references_bibliography_progress.jsonl")


YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2})\b")
REF_ENTRY_RE = re.compile(r"\[(\d+)\]\s*(.*?)\s*(?=(?:\n\[\d+\])|\Z)", re.DOTALL)

# Common venue tokens for normalization
_VENUE_TOKEN_RE = re.compile(
    r"\b(Proc\.|Proceedings|Conf\.|Conference|Symp\.|Symposium|Workshop|Journal|Trans\.|Transactions|Int\.|International|J\.|IEEE|ACM|Springer|Elsevier|Nature|Wiley|arXiv)\b",
    re.IGNORECASE,
)


@dataclass
class PaperResult:
    paper_id: str
    pdf_path: str
    ok: bool
    error: str = ""
    refs_extracted: int = 0
    years_extracted: int = 0
    venues_extracted: int = 0
    ref_words: int = 0
    duration_s: float = 0.0


def load_processed_from_progress(progress_path: str) -> Dict[str, Dict]:
    """Load prior per-paper results from JSONL to support resume/no-duplicates."""
    processed: Dict[str, Dict] = {}
    if not os.path.exists(progress_path):
        return processed

    try:
        with open(progress_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                pid = obj.get("paper_id")
                if pid:
                    processed[pid] = obj
    except Exception:
        return processed

    return processed


def count_words(text: str) -> int:
    if not text:
        return 0
    toks = re.findall(r"\b\w+\b", text)
    return len(toks)


def merge_counter_dict(dst: Counter, src_obj: object) -> None:
    """Merge a JSON-serialized counter dict {key: count} into a Counter."""
    if not src_obj or not isinstance(src_obj, dict):
        return
    for k, v in src_obj.items():
        try:
            dst[str(k)] += int(v)
        except Exception:
            continue


def append_progress(progress_path: str, obj: Dict) -> None:
    os.makedirs(os.path.dirname(progress_path), exist_ok=True)
    with open(progress_path, "a") as f:
        f.write(json.dumps(obj) + "\n")


def load_pdf_metadata(path: str = METADATA_FILE) -> Dict[str, Dict]:
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def iter_unique_papers_from_qdrant(client) -> List[Tuple[str, List[float]]]:
    """Return list of (paper_id, vector) using one vector per filename."""
    seen = set()
    items: List[Tuple[str, List[float]]] = []

    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        if not points:
            break

        for p in points:
            payload = p.payload or {}
            paper_id = payload.get("filename") or payload.get("paper_id") or str(p.id)
            if not paper_id or paper_id in seen:
                continue
            if p.vector is None:
                continue
            seen.add(paper_id)
            items.append((paper_id, p.vector))

        if offset is None:
            break

    return items


def sample_diverse_papers(
    client,
    metadata: Dict[str, Dict],
    sample_size: int,
    candidate_limit: int,
    random_state: int,
) -> List[Dict]:
    """Sample papers via KMeans on embeddings to maximize diversity."""
    import numpy as np
    from sklearn.cluster import KMeans
    # Grab a candidate pool (one vector per unique paper) by scrolling once.
    # NOTE: Candidate pool size is limited for runtime/memory.
    items = []
    seen = set()
    offset = None
    while len(items) < candidate_limit:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        if not points:
            break

        for p in points:
            payload = p.payload or {}
            paper_id = payload.get("filename") or payload.get("paper_id") or str(p.id)
            if not paper_id or paper_id in seen:
                continue
            if p.vector is None:
                continue
            seen.add(paper_id)
            items.append((paper_id, p.vector))
            if len(items) >= candidate_limit:
                break

        if offset is None:
            break

    if not items:
        return []

    paper_ids = [pid for pid, _ in items]
    vectors = np.array([v for _, v in items])

    n_clusters = min(sample_size, len(paper_ids))
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(vectors)

    selected: List[Dict] = []
    for cluster_id in range(n_clusters):
        cluster_indices = np.where(labels == cluster_id)[0]
        if cluster_indices.size == 0:
            continue
        centroid = kmeans.cluster_centers_[cluster_id]
        dists = np.linalg.norm(vectors[cluster_indices] - centroid, axis=1)
        best_local = int(cluster_indices[int(np.argmin(dists))])
        pid = paper_ids[best_local]
        meta = metadata.get(pid, {})
        pdf_path = meta.get("path") or os.path.join(PDF_FOLDER, pid)
        selected.append(
            {
                "paper_id": pid,
                "title": meta.get("title", "Unknown"),
                "year": meta.get("year", "Unknown"),
                "doi": meta.get("doi"),
                "pdf_path": pdf_path,
                "cluster_id": cluster_id,
            }
        )

    return selected


def extract_references_section_fast(pdf_path: str, last_pages: int = 3) -> str:
    """Extract References section text from last N pages using PyMuPDF."""
    try:
        import fitz  # type: ignore  # lazy import (PyMuPDF)
    except ModuleNotFoundError as e:
        # Make the dependency obvious in the per-paper error log.
        raise ModuleNotFoundError(
            "Missing dependency for PDF extraction. Install: pip install pymupdf"
        ) from e

    doc = fitz.open(pdf_path)
    try:
        start = max(0, doc.page_count - last_pages)
        text_parts = []
        for i in range(start, doc.page_count):
            text_parts.append(doc.load_page(i).get_text())
        text = "\n".join(text_parts)
    finally:
        doc.close()

    # Find references start
    m = re.search(r"(?:^|\n)\s*(REFERENCES|References)\s*(?:\n|$)", text)
    if not m:
        return ""

    return text[m.end() :]


def split_reference_entries(ref_text: str) -> List[str]:
    """Split IEEE-style reference list into individual entries."""
    if not ref_text.strip():
        return []

    # Normalize whitespace
    txt = ref_text.replace("\r\n", "\n").replace("\r", "\n")
    txt = re.sub(r"\n{3,}", "\n\n", txt)

    entries = []
    for _, ref_body in REF_ENTRY_RE.findall(txt):
        body = re.sub(r"\s+", " ", ref_body).strip()
        if body:
            entries.append(body)
    return entries


def extract_year_from_entry(entry: str) -> Optional[int]:
    years = [int(y) for y in YEAR_RE.findall(entry)]
    years = [y for y in years if 1950 <= y <= 2026]
    if not years:
        return None
    # IEEE refs often include the publication year near the end
    return years[-1]


def extract_venue_from_entry(entry: str) -> Optional[str]:
    """Best-effort venue extraction from IEEE reference entry."""
    # Heuristic: try to find quoted title, then take the next chunk (publication string)
    # Example: Authors, "Title," IEEE Trans. Something, vol..., no..., pp..., 2020.
    q = re.search(r'"([^"]{5,300})"\s*,\s*(.*)$', entry)
    candidate = None
    if q:
        tail = q.group(2)
        # Cut at DOI marker if present
        tail = re.split(r"\bdoi\b", tail, flags=re.IGNORECASE)[0]
        # Cut at year if present (but keep the venue before that)
        y = YEAR_RE.search(tail)
        if y:
            tail = tail[: y.start()]
        # Prefer the first clause (venue/journal tends to appear early)
        tail = tail.split(".")[0]
        candidate = tail
    else:
        candidate = entry

    if not candidate:
        return None

    # Strip common trailing parts
    candidate = re.sub(r"\bvol\.?\b.*", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\bno\.?\b.*", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\bpp\.?\b.*", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\bpages\b.*", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"\bdoi\b.*", "", candidate, flags=re.IGNORECASE)
    candidate = candidate.strip(" ,.;: ")

    # Keep it short-ish
    candidate = re.sub(r"\s+", " ", candidate).strip()
    if len(candidate) < 6:
        return None
    if len(candidate) > 200:
        candidate = candidate[:200].rstrip()

    return normalize_venue(candidate)


def normalize_venue(venue: str) -> str:
    """Normalize venue string for counting (reduce duplicates)."""
    v = venue.replace("\n", " ")
    v = re.sub(r"\s+", " ", v).strip()

    # Common canonicalizations
    subs = [
        (r"Adv\. Neural Inf\. Process\. Syst.*", "NeurIPS"),
        (r"Neural Inf\. Process\. Syst.*", "NeurIPS"),
        (r"IEEE/CVF Conf\. Comput\. Vis\. Pattern Recognit\..*", "CVPR"),
        (r"IEEE Conf\. Comput\. Vis\. Pattern Recognit\..*", "CVPR"),
        (r"Int\. Conf\. Comput\. Vis\..*", "ICCV"),
        (r"Eur\. Conf\. Comput\. Vis\..*", "ECCV"),
        (r"J\. Mach\. Learn\. R.*", "JMLR"),
        (r"Mach\. Learn\b.*", "Machine Learning (journal)"),
        (r"Neural Comput\b.*", "Neural Computation"),
        (r"Proc\. IEEE\b.*", "Proceedings of the IEEE"),
        (r"Commun\. ACM\b.*", "Communications of the ACM"),
    ]
    for pat, repl in subs:
        if re.search(pat, v, flags=re.IGNORECASE):
            return repl

    # If it's very long and doesn't include typical venue tokens, keep only a shorter suffix/prefix
    if len(v) > 120 and not _VENUE_TOKEN_RE.search(v):
        v = v[:120].rstrip()

    return v


def map_publisher_family(entry: str, venue: Optional[str]) -> str:
    text = (entry + " " + (venue or "")).lower()

    rules = [
        ("ieee", ["ieee", "trans.", "transactions", "proc. ieee", "ieee access", "ieee/cvf"]),
        ("acm", ["acm", "commun. acm", "sig", "sigcomm", "sigkdd", "sigir", "sigchi", "sigmod", "siggraph"]),
        ("arxiv", ["arxiv", "arxiv preprint"]),
        ("springer", ["springer", "lncs", "lecture notes in computer science"]),
        ("elsevier", ["elsevier", "sciencedirect", "pattern recognition", "information sciences"]),
        ("wiley", ["wiley"]),
        ("nature", ["nature", "nature communications", "nat."] ),
        ("mdpi", ["mdpi"]),
        ("taylor_francis", ["taylor", "francis"]),
        ("sage", ["sage"]),

        # Major ML/CV venues (not publishers but critical buckets for your analysis)
        ("neurips", ["neurips", "nips", "neural inf. process. syst", "adv. neural inf. process. syst"]),
        ("icml", ["icml", "int. conf. on machine learning", "international conference on machine learning"]),
        ("iclr", ["iclr", "int. conf. on learning representations", "international conference on learning representations"]),
        ("cvpr", ["cvpr", "comput. vis. pattern recognit"]),
        ("iccv", ["iccv", "int. conf. comput. vis"]),
        ("eccv", ["eccv", "eur. conf. comput. vis"]),
        ("aaai", ["aaai"]),
        ("ijcai", ["ijcai"]),
        ("usenix", ["usenix"]),
    ]

    for family, needles in rules:
        for n in needles:
            if n in text:
                return family

    return "other"


def process_pdf(paper_id: str, pdf_path: str, last_pages: int) -> Tuple[PaperResult, List[int], List[str], List[str]]:
    t0 = time.time()
    if not pdf_path or not os.path.exists(pdf_path):
        return PaperResult(paper_id=paper_id, pdf_path=pdf_path, ok=False, error="pdf_missing", duration_s=time.time() - t0), [], [], []

    try:
        ref_text = extract_references_section_fast(pdf_path, last_pages=last_pages)
        if not ref_text.strip():
            return PaperResult(paper_id=paper_id, pdf_path=pdf_path, ok=False, error="references_not_found", duration_s=time.time() - t0), [], [], []

        entries = split_reference_entries(ref_text)
        ref_words = count_words(ref_text)
        years: List[int] = []
        venues: List[str] = []
        families: List[str] = []

        for e in entries:
            y = extract_year_from_entry(e)
            if y is not None:
                years.append(y)
            v = extract_venue_from_entry(e)
            if v:
                venues.append(v)
            families.append(map_publisher_family(e, v))

        res = PaperResult(
            paper_id=paper_id,
            pdf_path=pdf_path,
            ok=True,
            refs_extracted=len(entries),
            years_extracted=len(years),
            venues_extracted=len(venues),
            ref_words=ref_words,
            duration_s=time.time() - t0,
        )
        return res, years, venues, families

    except ModuleNotFoundError as e:
        return PaperResult(
            paper_id=paper_id,
            pdf_path=pdf_path,
            ok=False,
            error=f"module_missing:{getattr(e, 'name', 'unknown')}",
            duration_s=time.time() - t0,
        ), [], [], []

    except Exception as e:
        return PaperResult(
            paper_id=paper_id,
            pdf_path=pdf_path,
            ok=False,
            error=f"exception:{type(e).__name__}",
            duration_s=time.time() - t0,
        ), [], [], []


def write_csv(path: str, header: List[str], rows: Iterable[List]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def load_sample_manifest_csv(path: str) -> List[Dict]:
    """Load an existing sample manifest produced by this script.

    Expected columns: paper_id,title,year,doi,pdf_path,cluster_id
    """
    sample: List[Dict] = []
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            paper_id = (row.get("paper_id") or "").strip()
            if not paper_id:
                continue
            sample.append(
                {
                    "paper_id": paper_id,
                    "title": row.get("title", "Unknown"),
                    "year": row.get("year", "Unknown"),
                    "doi": row.get("doi") or None,
                    "pdf_path": row.get("pdf_path") or row.get("source_path") or "",
                    "cluster_id": row.get("cluster_id", "manifest"),
                }
            )
    return sample


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample-size", type=int, default=500, help="Number of papers to analyze. Use 0 to analyze all papers in the manifest/mode.")
    ap.add_argument("--candidate-limit", type=int, default=15000)
    ap.add_argument("--last-pages", type=int, default=3)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--random-state", type=int, default=42)
    ap.add_argument(
        "--use-manifest",
        type=str,
        default="",
        help="Use an existing sample manifest CSV (skips Qdrant sampling).",
    )
    ap.add_argument(
        "--manifest-from-metadata",
        type=str,
        default="",
        help="Write a manifest CSV for ALL PDFs from pdf_metadata.json to this path, then exit (no Qdrant).",
    )
    ap.add_argument(
        "--qdrant-timeout",
        type=float,
        default=60.0,
        help="Qdrant client timeout (seconds) used only when sampling from Qdrant.",
    )
    ap.add_argument(
        "--rerun-failed",
        action="store_true",
        help="If set, reprocess papers that previously had ok=0 in the progress log.",
    )
    ap.add_argument(
        "--force-recompute",
        action="store_true",
        help="If set, ignore the existing progress log and write to a new timestamped progress file.",
    )
    args = ap.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)

    progress_path = PROGRESS_JSONL
    if args.force_recompute:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        progress_path = os.path.join(CHECKPOINT_DIR, f"references_bibliography_progress_{ts}.jsonl")

    processed = load_processed_from_progress(progress_path)
    processed_ids = set(processed.keys())
    processed_failed_ids = {pid for pid, obj in processed.items() if not obj.get("ok", False)}

    def _needs_new_fields(obj: Dict) -> bool:
        # Older progress entries won't have these; reprocess so summary is correct.
        if not obj.get("ok", False):
            return False
        if obj.get("ref_words") in (None, ""):
            return True
        if obj.get("year_counts") is None:
            return True
        if obj.get("venue_counts") is None:
            return True
        if obj.get("family_counts") is None:
            return True
        return False

    if args.manifest_from_metadata:
        metadata = load_pdf_metadata()
        manifest_rows = []
        for paper_id, meta in metadata.items():
            pdf_path = meta.get("path") or os.path.join(PDF_FOLDER, paper_id)
            manifest_rows.append(
                [
                    paper_id,
                    meta.get("title", "Unknown"),
                    meta.get("year", "Unknown"),
                    meta.get("doi"),
                    pdf_path,
                    "metadata",
                ]
            )

        write_csv(
            args.manifest_from_metadata,
            ["paper_id", "title", "year", "doi", "pdf_path", "cluster_id"],
            manifest_rows,
        )
        print(f"Wrote manifest for {len(manifest_rows)} papers to: {args.manifest_from_metadata}")
        return 0

    if args.use_manifest:
        print(f"Loading sample from manifest: {args.use_manifest}")
        sample = load_sample_manifest_csv(args.use_manifest)
        if args.sample_size and args.sample_size > 0 and len(sample) > args.sample_size:
            sample = sample[: args.sample_size]
    else:
        metadata = load_pdf_metadata()
        from qdrant_client import QdrantClient
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=args.qdrant_timeout)

        print(f"Sampling {args.sample_size} diverse papers from Qdrant (candidate_limit={args.candidate_limit})...")
        sample = sample_diverse_papers(
            client=client,
            metadata=metadata,
            sample_size=args.sample_size,
            candidate_limit=args.candidate_limit,
            random_state=args.random_state,
        )

    if not sample:
        print("No sample produced (Qdrant empty or unavailable?)")
        return 1

    manifest_path = os.path.join(OUTPUT_DIR, "references_sample_manifest.csv")
    if not args.use_manifest:
        write_csv(
            manifest_path,
            ["paper_id", "title", "year", "doi", "pdf_path", "cluster_id"],
            [[s["paper_id"], s["title"], s["year"], s.get("doi"), s["pdf_path"], s["cluster_id"]] for s in sample],
        )
    else:
        # Keep summary pointing at the manifest we used.
        manifest_path = args.use_manifest

    from concurrent.futures import ProcessPoolExecutor, as_completed

    # Filter out already-processed papers to avoid duplicate work.
    to_process = []
    for s in sample:
        pid = s["paper_id"]
        if pid in processed_ids:
            if args.rerun_failed and pid in processed_failed_ids:
                to_process.append(s)
            else:
                # If the script was upgraded (new fields added), reprocess ok papers missing the new fields.
                if _needs_new_fields(processed.get(pid, {})):
                    to_process.append(s)
                else:
                    continue
        else:
            to_process.append(s)

    print(f"Previously processed (from {progress_path}): {len(processed_ids)}")
    print(f"Submitting {len(to_process)} PDFs for processing (skipping {len(sample) - len(to_process)})")

    start = time.time()
    year_counter: Counter = Counter()
    venue_counter: Counter = Counter()
    family_counter: Counter = Counter()
    ref_words_all: List[int] = []
    paper_stats: List[PaperResult] = []

    # Incorporate previously processed papers into the aggregate counters so resume updates summary correctly.
    for pid, obj in processed.items():
        if not obj.get("ok", False):
            continue
        merge_counter_dict(year_counter, obj.get("year_counts"))
        merge_counter_dict(venue_counter, obj.get("venue_counts"))
        merge_counter_dict(family_counter, obj.get("family_counts"))
        try:
            w = int(obj.get("ref_words", 0))
            if w > 0:
                ref_words_all.append(w)
        except Exception:
            pass

        paper_stats.append(
            PaperResult(
                paper_id=pid,
                pdf_path=obj.get("pdf_path", ""),
                ok=True,
                error=obj.get("error", ""),
                refs_extracted=int(obj.get("refs_extracted", 0) or 0),
                years_extracted=int(obj.get("years_extracted", 0) or 0),
                venues_extracted=int(obj.get("venues_extracted", 0) or 0),
                ref_words=int(obj.get("ref_words", 0) or 0),
                duration_s=float(obj.get("duration_s", 0.0) or 0.0),
            )
        )

    print(f"Processing PDFs (last_pages={args.last_pages}) with {args.workers} workers...")

    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        inflight = {}
        it = iter(to_process)

        def submit_next() -> bool:
            try:
                s = next(it)
            except StopIteration:
                return False
            fut = ex.submit(process_pdf, s["paper_id"], s["pdf_path"], args.last_pages)
            inflight[fut] = s
            return True

        # Prime a small buffer of work to limit memory growth on large manifests.
        for _ in range(max(1, args.workers * 4)):
            if not submit_next():
                break

        done = 0
        while inflight:
            for fut in as_completed(list(inflight.keys()), timeout=None):
                _ = inflight.pop(fut, None)

                res, ys, vs, fs = fut.result()
                paper_stats.append(res)

                # Update global counters incrementally (more scalable than storing all lists)
                year_counter.update([str(y) for y in ys])
                venue_counter.update(vs)
                family_counter.update(fs)
                if res.ref_words and res.ref_words > 0:
                    ref_words_all.append(int(res.ref_words))

                append_progress(
                    progress_path,
                    {
                        "paper_id": res.paper_id,
                        "pdf_path": res.pdf_path,
                        "ok": bool(res.ok),
                        "error": res.error,
                        "refs_extracted": res.refs_extracted,
                        "years_extracted": res.years_extracted,
                        "venues_extracted": res.venues_extracted,
                        "ref_words": int(res.ref_words or 0),
                        "duration_s": round(res.duration_s, 4),
                        "year_counts": dict(Counter([int(y) for y in ys])),
                        "venue_counts": dict(Counter(vs)),
                        "family_counts": dict(Counter(fs)),
                    },
                )

                done += 1
                if done % 25 == 0:
                    print(f"  {done}/{len(to_process)} complete")

                # Keep the pipeline full
                submit_next()

                break

    elapsed = time.time() - start

    durations = [r.duration_s for r in paper_stats if r.duration_s is not None]
    avg_s = (sum(durations) / len(durations)) if durations else 0.0
    max_s = max(durations) if durations else 0.0

    ok_count = sum(1 for r in paper_stats if r.ok)
    total_refs = sum(r.refs_extracted for r in paper_stats if r.ok)

    # Outputs
    write_csv(
        os.path.join(OUTPUT_DIR, "references_cited_years_hist.csv"),
        ["year", "count"],
        [[int(y), c] for y, c in sorted(year_counter.items(), key=lambda x: int(x[0]))],
    )

    write_csv(
        os.path.join(OUTPUT_DIR, "references_top_venues.csv"),
        ["venue", "count"],
        [[v, c] for v, c in venue_counter.most_common(200)],
    )

    write_csv(
        os.path.join(OUTPUT_DIR, "references_top_publisher_families.csv"),
        ["publisher_family", "count"],
        [[fam, c] for fam, c in family_counter.most_common()],
    )

    write_csv(
        os.path.join(OUTPUT_DIR, "references_per_paper_stats.csv"),
        ["paper_id", "pdf_path", "ok", "error", "refs_extracted", "years_extracted", "venues_extracted", "ref_words"],
        [[r.paper_id, r.pdf_path, int(r.ok), r.error, r.refs_extracted, r.years_extracted, r.venues_extracted, r.ref_words] for r in paper_stats],
    )

    # Summary JSON
    years_sorted = sorted([int(y) for y in year_counter.elements()])
    def pct(p: float) -> Optional[int]:
        if not years_sorted:
            return None
        idx = int(round((len(years_sorted) - 1) * p))
        return years_sorted[idx]

    ref_words_sorted = sorted([w for w in ref_words_all if w is not None])
    def pct_words(p: float) -> Optional[int]:
        if not ref_words_sorted:
            return None
        idx = int(round((len(ref_words_sorted) - 1) * p))
        return int(ref_words_sorted[idx])

    summary = {
        "run_config": {
            "sample_size": args.sample_size,
            "candidate_limit": args.candidate_limit,
            "last_pages": args.last_pages,
            "workers": args.workers,
            "collection": COLLECTION_NAME,
            "rerun_failed": bool(args.rerun_failed),
        },
        "sampling": {
            "method": "manifest" if args.use_manifest else "qdrant_kmeans_diverse",
            "manifest": manifest_path,
        },
        "processing": {
            "papers_ok": ok_count,
            "papers_total": len(paper_stats),
            "seconds": round(elapsed, 2),
            "avg_seconds_per_paper": round(avg_s, 4),
            "max_seconds_per_paper": round(max_s, 4),
            "progress_log": progress_path,
            "total_reference_entries_extracted": total_refs,
            "total_reference_years_extracted": sum(year_counter.values()),
            "total_reference_venues_extracted": sum(venue_counter.values()),
        },
        "references_text": {
            "ref_words_min": min(ref_words_sorted) if ref_words_sorted else None,
            "ref_words_max": max(ref_words_sorted) if ref_words_sorted else None,
            "ref_words_p10": pct_words(0.10),
            "ref_words_p25": pct_words(0.25),
            "ref_words_p50": pct_words(0.50),
            "ref_words_p75": pct_words(0.75),
            "ref_words_p90": pct_words(0.90),
            "ref_words_avg": round((sum(ref_words_sorted) / len(ref_words_sorted)), 2) if ref_words_sorted else None,
        },
        "cited_years": {
            "min": min(years_sorted) if years_sorted else None,
            "max": max(years_sorted) if years_sorted else None,
            "p10": pct(0.10),
            "p25": pct(0.25),
            "p50": pct(0.50),
            "p75": pct(0.75),
            "p90": pct(0.90),
        },
        "top_years": [(int(y), c) for y, c in Counter({int(k): v for k, v in year_counter.items()}).most_common(20)],
        "top_venues": venue_counter.most_common(50),
        "top_publisher_families": family_counter.most_common(),
        "notes": [
            "Venue extraction is best-effort based on IEEE reference formatting heuristics.",
            "Publisher family mapping is heuristic (keyword-based).",
            "references_text.ref_words_* are word-count statistics of the extracted References section text (post 'REFERENCES' header, limited to last_pages).",
        ],
    }

    with open(os.path.join(OUTPUT_DIR, "references_analysis_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\nWrote outputs to output/:")
    print("- references_analysis_summary.json")
    print("- references_cited_years_hist.csv")
    print("- references_top_venues.csv")
    print("- references_top_publisher_families.csv")
    print("- references_per_paper_stats.csv")
    print("- references_sample_manifest.csv")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

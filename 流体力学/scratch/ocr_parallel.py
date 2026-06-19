import os
import sys

# Crucial: Limit threads BEFORE importing numpy, ONNX Runtime, etc.
# This completely prevents multi-process thread thrashing on 24-core CPU.
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import time
import json
import argparse
import subprocess
import fitz
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add RAG scripts directory to path to import layout ordering
sys.path.append(r"D:\虚拟C盘\RAG\scripts")
from ocr_scanned_pdfs import make_line_payload, order_lines_layout_aware

PDF_PATH = Path(r"d:\虚拟C盘\学习\流体力学\流力瞎整\流体力学 张兆顺 第三版.pdf")
TEMP_DIR = Path(r"d:\虚拟C盘\学习\流体力学\流力瞎整\ocr_temp")
MASTER_JSONL_PATH = Path(r"d:\虚拟C盘\学习\流体力学\流力瞎整\流体力学_张兆顺_第三版_pages.jsonl")
TXT_PATH = Path(r"d:\虚拟C盘\学习\流体力学\流力瞎整\流体力学_张兆顺_第三版_OCR.txt")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-id", type=int, default=-1, help="Worker ID. If -1, runs as master.")
    parser.add_argument("--pages", type=str, default="", help="Comma separated page numbers for worker.")
    parser.add_argument("--workers-count", type=int, default=12, help="Number of workers for parallel execution.")
    return parser.parse_args()

def load_jsonl_pages(path: Path) -> dict[int, dict]:
    pages = {}
    if not path.exists():
        return pages
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                pages[int(data["page_num"])] = data
            except Exception as e:
                pass
    return pages

# Worker implementation
def run_worker(worker_id: int, page_list: list[int]):
    print(f"[Worker {worker_id}] Initializing with {len(page_list)} pages...")
    from rapidocr_onnxruntime import RapidOCR
    
    # Configure RapidOCR to use exactly 1 thread for detection, classification, and recognition
    ocr = RapidOCR(
        **{
            "Det.intra_op_num_threads": 1,
            "Det.inter_op_num_threads": 1,
            "Cls.intra_op_num_threads": 1,
            "Cls.inter_op_num_threads": 1,
            "Rec.intra_op_num_threads": 1,
            "Rec.inter_op_num_threads": 1,
        }
    )

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    worker_jsonl_path = TEMP_DIR / f"worker_{worker_id:02d}.jsonl"
    existing_pages = load_jsonl_pages(worker_jsonl_path)
    print(f"[Worker {worker_id}] Loaded {len(existing_pages)} already completed pages.")

    doc = fitz.open(PDF_PATH)
    pages_to_do = [p for p in page_list if p not in existing_pages]
    print(f"[Worker {worker_id}] Starting {len(pages_to_do)} pages...")

    with worker_jsonl_path.open("a", encoding="utf-8") as out_file:
        for index, page_num in enumerate(pages_to_do):
            page_index = page_num - 1
            page = doc.load_page(page_index)
            start_time = time.perf_counter()

            # Render at scale 1.35
            pix = page.get_pixmap(matrix=fitz.Matrix(1.35, 1.35), alpha=False)
            image_bytes = pix.tobytes("png")

            # OCR
            result, timings = ocr(image_bytes)

            lines = []
            if result:
                for item in result:
                    line = make_line_payload(item, pix.width)
                    if line:
                        lines.append(line)

            # Reorder lines layout-aware
            ordered_lines, layout = order_lines_layout_aware(lines, pix.width)
            page_text = "\n".join(line["text"] for line in ordered_lines).strip()
            avg_confidence = (
                round(sum(float(l["confidence"]) for l in ordered_lines) / len(ordered_lines), 4)
                if ordered_lines
                else 0.0
            )

            # Record payload
            payload = {
                "page_num": page_num,
                "text": page_text,
                "char_count": len(page_text),
                "line_count": len(ordered_lines),
                "avg_confidence": avg_confidence,
                "layout": layout,
                "status": "ok"
            }

            # Write to worker file
            out_file.write(json.dumps(payload, ensure_ascii=False) + "\n")
            out_file.flush()

            elapsed = time.perf_counter() - start_time
            print(f"[Worker {worker_id}] Page {page_num} completed in {elapsed:.2f}s ({index+1}/{len(pages_to_do)})")

    print(f"[Worker {worker_id}] Finished processing all assigned pages.")

# Master implementation
def run_master(num_workers: int):
    print("=== Master Coordinate Starting ===")
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    print(f"Total pages in PDF: {total_pages}")

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Gather all completed pages from existing worker logs
    completed_pages = set()
    for worker_file in TEMP_DIR.glob("worker_*.jsonl"):
        pages_dict = load_jsonl_pages(worker_file)
        completed_pages.update(pages_dict.keys())
    
    print(f"Already completed pages in temp directory: {len(completed_pages)} / {total_pages}")

    # Determine remaining pages
    remaining_pages = [p for p in range(1, total_pages + 1) if p not in completed_pages]
    print(f"Pages left to process: {len(remaining_pages)}")

    if not remaining_pages:
        print("All pages already completed. Merging...")
        merge_all_workers(total_pages)
        return

    # Split remaining pages evenly among workers
    worker_buckets = [[] for _ in range(num_workers)]
    for idx, page in enumerate(remaining_pages):
        worker_buckets[idx % num_workers].append(page)

    # Start subprocesses
    processes = []
    python_exe = sys.executable  # Use current Python interpreter (the virtualenv one)
    script_path = __file__

    print(f"Spawning {num_workers} parallel workers...")
    for worker_id in range(num_workers):
        pages_to_process = worker_buckets[worker_id]
        if not pages_to_process:
            continue
        
        pages_str = ",".join(map(str, pages_to_process))
        cmd = [
            python_exe,
            "-u",
            script_path,
            "--worker-id", str(worker_id),
            "--pages", pages_str
        ]
        
        # Open separate log file for each worker's print statements
        log_file = (TEMP_DIR / f"worker_{worker_id:02d}.log").open("w", encoding="utf-8")
        
        p = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append((worker_id, p, log_file))
        print(f"Started worker {worker_id} (PID: {p.pid}) with {len(pages_to_process)} pages.")

    # Master non-blocking polling loop
    start_time = time.perf_counter()
    try:
        while processes:
            # Check worker process status
            alive_processes = []
            for worker_id, p, log_file in processes:
                ret = p.poll()
                if ret is None:
                    alive_processes.append((worker_id, p, log_file))
                else:
                    log_file.close()
                    if ret != 0:
                        print(f"Worker {worker_id} terminated with ERROR exit code {ret}!")
                    else:
                        print(f"Worker {worker_id} finished successfully.")
            
            processes = alive_processes
            
            # Count completed pages from temp files
            completed_now = 0
            for worker_file in TEMP_DIR.glob("worker_*.jsonl"):
                try:
                    completed_now += sum(1 for _ in worker_file.open("r", encoding="utf-8"))
                except Exception:
                    pass
            
            elapsed = time.perf_counter() - start_time
            print(f"Progress: {completed_now} / {total_pages} pages ({completed_now/total_pages*100:.1f}%) | "
                  f"Active workers: {len(processes)} | Elapsed: {elapsed/60:.1f}m")
            
            if processes:
                time.sleep(3.0)
    except KeyboardInterrupt:
        print("Master interrupted! Terminating all workers...")
        for worker_id, p, log_file in processes:
            p.terminate()
            log_file.close()
        sys.exit(1)

    print("All workers finished processing. Verifying and merging results...")
    merge_all_workers(total_pages)

def merge_all_workers(total_pages: int):
    # Collect all pages from all worker logs
    all_pages = {}
    
    # First load from TEMP_DIR worker files
    for worker_file in TEMP_DIR.glob("worker_*.jsonl"):
        worker_pages = load_jsonl_pages(worker_file)
        all_pages.update(worker_pages)

    # Also load from master JSONL if it has some data
    if MASTER_JSONL_PATH.exists():
        master_pages = load_jsonl_pages(MASTER_JSONL_PATH)
        all_pages.update(master_pages)

    print(f"Collected total of {len(all_pages)} pages for merging.")

    # Write Master JSONL
    print(f"Writing master JSONL log to {MASTER_JSONL_PATH}")
    with MASTER_JSONL_PATH.open("w", encoding="utf-8") as f:
        for page_num in sorted(all_pages.keys()):
            f.write(json.dumps(all_pages[page_num], ensure_ascii=False) + "\n")

    # Write final TXT file
    print(f"Compiling final text document to {TXT_PATH}")
    with TXT_PATH.open("w", encoding="utf-8") as f:
        f.write("流体力学 张兆顺 第三版 OCR文本\n")
        f.write("="*40 + "\n\n")
        for page_num in range(1, total_pages + 1):
            f.write(f"--- 第 {page_num} 页 ---\n\n")
            if page_num in all_pages:
                f.write(all_pages[page_num].get("text", "").strip() + "\n\n")
            else:
                f.write("[缺失该页OCR数据]\n\n")

    print(f"Merge completed! Final text size: {TXT_PATH.stat().st_size} bytes.")

if __name__ == "__main__":
    args = parse_args()
    if args.worker_id == -1:
        run_master(args.workers_count)
    else:
        page_list = map(int, args.pages.split(",")) if args.pages else []
        run_worker(args.worker_id, list(page_list))

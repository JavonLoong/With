import os
import sys
import time
import json
import fitz
from pathlib import Path

# Ensure UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add RAG scripts directory to path to import layout ordering
sys.path.append(r"D:\虚拟C盘\RAG\scripts")
from ocr_scanned_pdfs import make_line_payload, order_lines_layout_aware, order_lines_visual

from rapidocr_onnxruntime import RapidOCR

PDF_PATH = r"d:\虚拟C盘\学习\流体力学\流力瞎整\流体力学 张兆顺 第三版.pdf"
JSONL_PATH = r"d:\虚拟C盘\学习\流体力学\流力瞎整\流体力学_张兆顺_第三版_pages.jsonl"
TXT_PATH = r"d:\虚拟C盘\学习\流体力学\流力瞎整\流体力学_张兆顺_第三版_OCR.txt"

def load_existing_pages(path: Path) -> dict[int, dict]:
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
                print(f"Error reading JSONL line: {e}")
    return pages

def main():
    print(f"Opening PDF: {PDF_PATH}")
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    print(f"Total pages: {total_pages}")

    jsonl_path = Path(JSONL_PATH)
    existing_pages = load_existing_pages(jsonl_path)
    print(f"Loaded {len(existing_pages)} already processed pages.")

    print("Initializing RapidOCR...")
    ocr = RapidOCR()

    # Determine pages to process
    pages_to_process = [p for p in range(1, total_pages + 1) if p not in existing_pages]
    print(f"Remaining pages to process: {len(pages_to_process)}")

    if not pages_to_process:
        print("All pages already processed.")
        merge_results(doc, jsonl_path, Path(TXT_PATH))
        return

    # Process loop
    started_time = time.perf_counter()
    processed_count = 0
    total_remaining = len(pages_to_process)

    # Open JSONL in append mode
    with jsonl_path.open("a", encoding="utf-8") as out_file:
        for page_num in pages_to_process:
            page_index = page_num - 1
            page = doc.load_page(page_index)
            page_start = time.perf_counter()

            # Render page
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

            # Order lines (use layout-aware)
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

            # Write to JSONL
            out_file.write(json.dumps(payload, ensure_ascii=False) + "\n")
            out_file.flush()

            processed_count += 1
            elapsed = time.perf_counter() - started_time
            avg_time_per_page = elapsed / processed_count
            eta = avg_time_per_page * (total_remaining - processed_count)

            print(f"Page {page_num}/{total_pages} processed in {time.perf_counter() - page_start:.2f}s | "
                  f"Avg: {avg_time_per_page:.2f}s | ETA: {eta/60:.2f}m | Conf: {avg_confidence:.3f}")

    print("OCR run completed successfully.")
    merge_results(doc, jsonl_path, Path(TXT_PATH))

def merge_results(doc, jsonl_path: Path, txt_path: Path):
    print(f"Merging results to: {txt_path}")
    pages = load_existing_pages(jsonl_path)
    total_pages = len(doc)

    with txt_path.open("w", encoding="utf-8") as f:
        f.write("流体力学 张兆顺 第三版 OCR文本\n")
        f.write("="*40 + "\n\n")

        for page_num in range(1, total_pages + 1):
            f.write(f"--- 第 {page_num} 页 ---\n\n")
            if page_num in pages:
                f.write(pages[page_num].get("text", "").strip() + "\n\n")
            else:
                f.write("[Missing Page Data]\n\n")

    print(f"Merge completed. Output file size: {txt_path.stat().st_size} bytes.")

if __name__ == "__main__":
    main()

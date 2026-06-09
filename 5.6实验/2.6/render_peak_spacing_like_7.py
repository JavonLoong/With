from __future__ import annotations

import csv
import json
import math
import shutil
from pathlib import Path

import cv2
import matplotlib
import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import find_peaks, savgol_filter


matplotlib.use("Agg")
import matplotlib.pyplot as plt


VIDEO = Path("3.mp4")
OUT_DIR = Path("analysis_outputs")

PX_PER_CM = 18.7
SURFACE_ROI = {"x1": 20, "x2": 940, "y1": 170, "y2": 360}
LOCAL_WAVE_TREND_WINDOW_PX = 401
PEAK_PROMINENCE_THRESHOLD_PX = 3.0
PEAK_MIN_DISTANCE_PX = 220
VALID_SPACING_RANGE_CM = (18.0, 28.0)
STABLE_TIME_S = 18.0
STABLE_MIN_PEAK_COUNT = 2


def odd_window(length: int, preferred: int, minimum: int = 5) -> int:
    win = min(preferred, length if length % 2 else length - 1)
    win = max(minimum, win)
    if win % 2 == 0:
        win -= 1
    return max(3, win)


def fmt_list(values: list[float] | list[int], digits: int = 3) -> str:
    if not values:
        return ""
    if isinstance(values[0], (int, np.integer)):
        return ";".join(str(int(v)) for v in values)
    return ";".join(f"{float(v):.{digits}f}" for v in values)


def stats(values: list[float]) -> dict[str, float | int | None]:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {
            "n": 0,
            "mean": None,
            "median": None,
            "std": None,
            "q1": None,
            "q3": None,
            "trimmed_mean_10pct": None,
            "min": None,
            "max": None,
        }
    sorted_arr = np.sort(arr)
    trim = int(math.floor(0.1 * sorted_arr.size))
    trimmed = sorted_arr[trim : sorted_arr.size - trim] if sorted_arr.size - 2 * trim > 0 else sorted_arr
    return {
        "n": int(arr.size),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "std": float(np.std(arr)),
        "q1": float(np.percentile(arr, 25)),
        "q3": float(np.percentile(arr, 75)),
        "trimmed_mean_10pct": float(np.mean(trimmed)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def load_frames(video: Path) -> tuple[list[np.ndarray], float]:
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open {video}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    frames: list[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    if not frames:
        raise RuntimeError(f"no frames decoded from {video}")
    return frames, fps


def detect_surface(frame: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    x1, x2 = SURFACE_ROI["x1"], SURFACE_ROI["x2"]
    y1, y2 = SURFACE_ROI["y1"], SURFACE_ROI["y2"]
    crop = frame[y1:y2, x1:x2]
    b, g, r = cv2.split(crop)
    score = 0.58 * g.astype(np.float32) + 0.52 * b.astype(np.float32) - 0.16 * r.astype(np.float32)
    score = cv2.GaussianBlur(score, (5, 5), 0)
    grad = np.gradient(score, axis=0)

    lo = max(3, int(0.06 * grad.shape[0]))
    hi = min(grad.shape[0] - 3, int(0.94 * grad.shape[0]))
    sub = grad[lo:hi]
    rel_y = np.argmax(sub, axis=0)
    strengths = sub[rel_y, np.arange(sub.shape[1])]
    y = y1 + lo + rel_y.astype(np.float32)

    weak = strengths < np.percentile(strengths, 12)
    y[weak] = np.nan
    xs_local = np.arange(x2 - x1)
    valid = np.isfinite(y)
    if valid.sum() >= max(30, int(0.10 * y.size)):
        y = np.interp(xs_local, xs_local[valid], y[valid]).astype(np.float32)
    else:
        y = np.full_like(xs_local, np.nanmedian(y), dtype=np.float32)

    y = median_filter(y, size=11, mode="nearest")
    y = savgol_filter(y, odd_window(y.size, 121), 3, mode="interp").astype(np.float32)
    xs = np.arange(x1, x2)
    return xs, y, float(np.mean(strengths))


def analyze_frame(frame: np.ndarray, idx: int, fps: float) -> dict[str, object]:
    xs, surface_y, contrast = detect_surface(frame)
    trend = savgol_filter(surface_y, odd_window(surface_y.size, LOCAL_WAVE_TREND_WINDOW_PX), 3, mode="interp")
    local_crests = trend - surface_y
    local_crests -= float(np.median(local_crests))
    peaks, props = find_peaks(
        local_crests,
        prominence=PEAK_PROMINENCE_THRESHOLD_PX,
        distance=PEAK_MIN_DISTANCE_PX,
    )
    peak_x = [int(xs[p]) for p in peaks]
    prominences = [float(p) for p in props.get("prominences", [])]
    spacing_px = [float(b - a) for a, b in zip(peak_x, peak_x[1:])]
    spacing_cm = [d / PX_PER_CM for d in spacing_px]
    valid_spacing = [
        d for d in spacing_cm if VALID_SPACING_RANGE_CM[0] <= d <= VALID_SPACING_RANGE_CM[1]
    ]
    mean_spacing = float(np.mean(valid_spacing)) if valid_spacing else None
    median_spacing = float(np.median(valid_spacing)) if valid_spacing else None
    return {
        "frame": idx,
        "time_s": idx / fps,
        "xs": xs,
        "surface_y": surface_y,
        "peak_x_px": peak_x,
        "peak_y_px": [float(surface_y[p]) for p in peaks],
        "peak_prominence_px": prominences,
        "spacing_px_all": spacing_px,
        "spacing_cm_all": spacing_cm,
        "spacing_cm_valid": valid_spacing,
        "frame_mean_spacing_cm": mean_spacing,
        "frame_median_spacing_cm": median_spacing,
        "surface_contrast_mean": contrast,
        "valid_spacing_count": len(valid_spacing),
    }


def draw_annotation(frame: np.ndarray, result: dict[str, object], fps: float) -> np.ndarray:
    img = frame.copy()
    xs = result["xs"]
    surface_y = result["surface_y"]
    pts = np.column_stack([xs, np.round(surface_y).astype(int)]).reshape(-1, 1, 2)
    cv2.polylines(img, [pts], False, (0, 0, 255), 2, cv2.LINE_AA)

    for x, y in zip(result["peak_x_px"], result["peak_y_px"]):
        cv2.circle(img, (int(x), int(round(y))), 5, (255, 0, 0), -1, cv2.LINE_AA)
        cv2.putText(
            img,
            str(int(x)),
            (int(x) + 5, max(18, int(round(y)) - 9)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

    valid = result["spacing_cm_valid"]
    valid_text = fmt_list(valid, 2) if valid else "NA"
    mean_val = result["frame_mean_spacing_cm"]
    mean_text = f"{mean_val:.2f} cm" if mean_val is not None else "NA"
    cv2.rectangle(img, (0, 0), (img.shape[1] - 1, 68), (0, 0, 0), -1)
    line1 = (
        f"frame {int(result['frame']):03d}  t={float(result['time_s']):.3f}s  "
        f"valid spacings={valid_text}  frame mean={mean_text}"
    )
    line2 = "red: detected surface   blue: local wave crests after detrending"
    cv2.putText(img, line1, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(img, line2, (8, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (235, 235, 235), 1, cv2.LINE_AA)
    return img


def write_contact_sheet(frames: list[np.ndarray], picks: list[int], out: Path) -> None:
    tile_w, tile_h = 320, 180
    label_h, gap = 32, 20
    canvas = np.full((3 * (tile_h + label_h) + 2 * gap, 3 * tile_w + 2 * gap, 3), 255, dtype=np.uint8)
    for k, idx in enumerate(picks):
        r, c = divmod(k, 3)
        x = c * (tile_w + gap)
        y = r * (tile_h + label_h + gap)
        cv2.putText(canvas, f"frame {idx}", (x + 3, y + 23), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 1, cv2.LINE_AA)
        thumb = cv2.resize(frames[idx], (tile_w, tile_h), interpolation=cv2.INTER_AREA)
        canvas[y + label_h : y + label_h + tile_h, x : x + tile_w] = thumb
    cv2.imwrite(str(out), canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 92])


def write_overlay_sheet(annotated: list[np.ndarray], picks: list[int], out: Path) -> None:
    tile_w, tile_h = 426, 240
    label_h = 36
    canvas = np.full((3 * (tile_h + label_h), 3 * tile_w, 3), 255, dtype=np.uint8)
    for k, (idx, img) in enumerate(zip(picks, annotated)):
        r, c = divmod(k, 3)
        x = c * tile_w
        y = r * (tile_h + label_h)
        thumb = cv2.resize(img, (tile_w, tile_h), interpolation=cv2.INTER_AREA)
        canvas[y : y + tile_h, x : x + tile_w] = thumb
        cv2.putText(
            canvas,
            f"frame {idx}",
            (x + 8, y + tile_h + 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.70,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )
    cv2.imwrite(str(out), canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 92])


def write_csvs(results: list[dict[str, object]], out_dir: Path) -> None:
    frame_fields = [
        "frame",
        "time_s",
        "peak_count",
        "peak_x_px",
        "peak_prominence_px",
        "spacing_px_all",
        "spacing_cm_all",
        "spacing_cm_valid",
        "frame_mean_spacing_cm",
        "frame_median_spacing_cm",
        "surface_contrast_mean",
        "valid_spacing_count",
    ]
    with (out_dir / "frame_by_frame_peak_spacing.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=frame_fields)
        writer.writeheader()
        for res in results:
            writer.writerow(
                {
                    "frame": res["frame"],
                    "time_s": res["time_s"],
                    "peak_count": len(res["peak_x_px"]),
                    "peak_x_px": fmt_list(res["peak_x_px"]),
                    "peak_prominence_px": fmt_list(res["peak_prominence_px"], 3),
                    "spacing_px_all": fmt_list(res["spacing_px_all"], 1),
                    "spacing_cm_all": fmt_list(res["spacing_cm_all"], 3),
                    "spacing_cm_valid": fmt_list(res["spacing_cm_valid"], 3),
                    "frame_mean_spacing_cm": "" if res["frame_mean_spacing_cm"] is None else res["frame_mean_spacing_cm"],
                    "frame_median_spacing_cm": "" if res["frame_median_spacing_cm"] is None else res["frame_median_spacing_cm"],
                    "surface_contrast_mean": res["surface_contrast_mean"],
                    "valid_spacing_count": res["valid_spacing_count"],
                }
            )

    with (out_dir / "interval_measurements.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["frame", "time_s", "interval_index", "spacing_cm", "valid"])
        writer.writeheader()
        for res in results:
            for i, spacing in enumerate(res["spacing_cm_all"], start=1):
                writer.writerow(
                    {
                        "frame": res["frame"],
                        "time_s": res["time_s"],
                        "interval_index": i,
                        "spacing_cm": spacing,
                        "valid": VALID_SPACING_RANGE_CM[0] <= spacing <= VALID_SPACING_RANGE_CM[1],
                    }
                )


def write_plots(results: list[dict[str, object]], summary: dict[str, object], out_dir: Path) -> None:
    times = [float(r["time_s"]) for r in results if r["frame_mean_spacing_cm"] is not None]
    means = [float(r["frame_mean_spacing_cm"]) for r in results if r["frame_mean_spacing_cm"] is not None]
    recommended = summary["recommended_average_cm"]
    duration = summary["video"]["duration_s"]

    fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
    if means:
        ax.plot(times, means, "-o", ms=2.5, lw=1.0, label="valid frame mean")
    if recommended is not None:
        ax.axhline(float(recommended), color="crimson", ls="--", label=f"recommended avg = {float(recommended):.2f} cm")
    ax.axvspan(0, STABLE_TIME_S, color="gray", alpha=0.12, label="onset / low-confidence region")
    ax.set_title("Frame-by-frame local peak spacing")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("peak spacing (cm)")
    ax.set_xlim(0, duration)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right")
    plt.tight_layout()
    fig.savefig(out_dir / "peak_spacing_time_series.png")
    plt.close(fig)

    valid_intervals = [d for r in results for d in r["spacing_cm_valid"]]
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
    if valid_intervals:
        ax.hist(valid_intervals, bins=18, color="#1f77b4", alpha=0.9)
        interval_median = float(np.median(valid_intervals))
        ax.axvline(interval_median, color="black", ls="--", label=f"interval median {interval_median:.2f} cm")
    if recommended is not None:
        ax.axvline(float(recommended), color="crimson", ls="--", label=f"recommended avg {float(recommended):.2f} cm")
    ax.set_title("Distribution of valid adjacent peak spacings")
    ax.set_xlabel("spacing (cm)")
    ax.set_ylabel("count")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(loc="upper right")
    plt.tight_layout()
    fig.savefig(out_dir / "peak_spacing_histogram.png")
    plt.close(fig)


def build_summary(frames: list[np.ndarray], fps: float, results: list[dict[str, object]]) -> dict[str, object]:
    valid_frame_means = [float(r["frame_mean_spacing_cm"]) for r in results if r["frame_mean_spacing_cm"] is not None]
    valid_intervals = [float(d) for r in results for d in r["spacing_cm_valid"]]
    stable_means = [
        float(r["frame_mean_spacing_cm"])
        for r in results
        if r["frame_mean_spacing_cm"] is not None
        and float(r["time_s"]) >= STABLE_TIME_S
        and len(r["peak_x_px"]) >= STABLE_MIN_PEAK_COUNT
    ]
    recommended = float(np.median(stable_means)) if stable_means else (float(np.median(valid_frame_means)) if valid_frame_means else None)
    h, w = frames[0].shape[:2]
    return {
        "video": {
            "frames": len(frames),
            "fps": fps,
            "duration_s": len(frames) / fps,
            "width": w,
            "height": h,
        },
        "method_parameters": {
            "px_per_cm": PX_PER_CM,
            "calibration_note": "Estimated from the visible ruler grid for this clip; 1 cm is about 18.7 px.",
            "surface_roi_px": SURFACE_ROI,
            "local_wave_trend_window_px": LOCAL_WAVE_TREND_WINDOW_PX,
            "peak_prominence_threshold_px": PEAK_PROMINENCE_THRESHOLD_PX,
            "peak_min_distance_px": PEAK_MIN_DISTANCE_PX,
            "valid_spacing_range_cm": list(VALID_SPACING_RANGE_CM),
        },
        "valid_frame_count": len(valid_frame_means),
        "valid_interval_count": len(valid_intervals),
        "interval_spacing_cm_stats": stats(valid_intervals),
        "frame_mean_spacing_cm_stats": stats(valid_frame_means),
        f"stable_frame_mean_spacing_cm_stats_time_ge_{int(STABLE_TIME_S)}s_peak_count_ge_{STABLE_MIN_PEAK_COUNT}": stats(stable_means),
        "recommended_average_cm": recommended,
        "recommended_average_rule": (
            f"Median of per-frame valid mean spacings for stable frames "
            f"(time >= {STABLE_TIME_S:.1f} s and at least {STABLE_MIN_PEAK_COUNT} detected peaks), "
            "matching the 7.0 analysis-output format so each frame has equal weight."
        ),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames, fps = load_frames(VIDEO)
    results = [analyze_frame(frame, idx, fps) for idx, frame in enumerate(frames)]
    summary = build_summary(frames, fps, results)

    picks = [int(round(i)) for i in np.linspace(0, len(frames) - 1, 9)]
    write_contact_sheet(frames, picks, OUT_DIR / "contact_sheet.jpg")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    h, w = frames[0].shape[:2]
    video_out = cv2.VideoWriter(str(OUT_DIR / "annotated_peak_detection.mp4"), fourcc, fps, (w, h))
    if not video_out.isOpened():
        raise RuntimeError("cannot open annotated video writer")
    annotated_picks = []
    for frame, result in zip(frames, results):
        annotated = draw_annotation(frame, result, fps)
        video_out.write(annotated)
        if int(result["frame"]) in picks:
            annotated_picks.append(annotated)
    video_out.release()

    write_overlay_sheet(annotated_picks, picks, OUT_DIR / "representative_overlay_sheet.jpg")
    write_csvs(results, OUT_DIR)
    write_plots(results, summary, OUT_DIR)
    with (OUT_DIR / "peak_spacing_summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"completed {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()

from __future__ import annotations

from pathlib import Path
import csv
import json
import math
import shutil

import cv2
import imageio_ffmpeg
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.signal import find_peaks, savgol_filter, detrend


plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


OUT_DIR = Path("peak_spacing_frame_analysis")
VIDEO_NAME = "6.mp4"
DEFAULT_PERIOD_BAND_CM = (12.0, 36.0)


def write_png(path: Path, img: np.ndarray) -> None:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError(f"cannot encode {path}")
    path.write_bytes(buf.tobytes())


def load_video(video: Path) -> tuple[list[np.ndarray], float, dict[str, object]]:
    reader = imageio_ffmpeg.read_frames(str(video), pix_fmt="bgr24")
    meta = next(reader)
    fps = float(meta.get("fps", 30.0) or 30.0)
    w, h = meta["size"]
    frames: list[np.ndarray] = []
    for raw in reader:
        arr = np.frombuffer(raw, dtype=np.uint8)
        if arr.size == w * h * 3:
            frames.append(arr.reshape((h, w, 3)).copy())
    return frames, fps, meta


def select_valid_frames(frames: list[np.ndarray]) -> tuple[list[int], list[int]]:
    valid: list[int] = []
    bad: list[int] = []
    for i, frame in enumerate(frames):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if gray.mean() < 8 or gray.std() < 3:
            bad.append(i)
        else:
            valid.append(i)
    return valid, bad


def find_ruler_band(frame: np.ndarray) -> tuple[int, int]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    dark_threshold = max(70.0, float(np.percentile(gray, 18)))
    dark = (gray < dark_threshold).astype(np.uint8)
    row_score = gaussian_filter1d(dark.sum(axis=1).astype(float), 1.2)
    search0, search1 = int(h * 0.20), int(h * 0.58)
    search = row_score[search0:search1]
    threshold = max(0.36 * w, float(np.percentile(search, 91)))
    ys = np.where((np.arange(h) >= search0) & (np.arange(h) < search1) & (row_score >= threshold))[0]

    groups: list[tuple[int, int, float]] = []
    if ys.size:
        start = prev = int(ys[0])
        for y_abs in ys[1:]:
            y = int(y_abs)
            if y <= prev + 2:
                prev = y
            else:
                if prev - start >= 3:
                    groups.append((start, prev, float(row_score[start : prev + 1].max())))
                start = prev = y
        if prev - start >= 3:
            groups.append((start, prev, float(row_score[start : prev + 1].max())))

    if groups:
        top, bot, _ = max(groups, key=lambda g: (g[2], g[1] - g[0]))
        return max(0, top - 2), min(h, bot + 3)

    yc = search0 + int(np.argmax(search))
    return max(0, yc - int(h * 0.03)), min(h, yc + int(h * 0.03))


def detect_ruler_edges(gray: np.ndarray) -> tuple[int, int]:
    h = gray.shape[0]
    search_y = np.arange(int(0.48 * h), int(0.68 * h))
    row_mean = gray.mean(axis=1)
    row_grad = gaussian_filter1d(np.abs(np.gradient(row_mean)), 1.4)
    peaks, _ = find_peaks(
        row_grad[search_y],
        distance=8,
        prominence=max(float(np.std(row_grad[search_y]) * 0.35), 0.5),
    )
    candidates = sorted(
        [(int(search_y[p]), float(row_grad[search_y[p]])) for p in peaks],
        key=lambda item: item[1],
        reverse=True,
    )
    if len(candidates) >= 2:
        pairs: list[tuple[float, int, int]] = []
        for i, (y1, s1) in enumerate(candidates[:8]):
            for y2, s2 in candidates[i + 1 : 8]:
                a, b = sorted([y1, y2])
                if 8 <= b - a <= 45:
                    pairs.append((s1 + s2, a, b))
        if pairs:
            _, y1, y2 = max(pairs)
            return y1, y2
        y1, y2 = sorted([candidates[0][0], candidates[1][0]])
        return y1, y2
    return int(0.565 * h), int(0.620 * h)


def fft_period(profile: np.ndarray, min_period_px: float, max_period_px: float) -> tuple[float, float]:
    y = np.asarray(profile, dtype=float)
    detrend_width = int(max(9, round(max_period_px * 5)))
    if detrend_width % 2 == 0:
        detrend_width += 1
    high = y - gaussian_filter1d(y, detrend_width / 6.0)
    high *= np.hanning(high.size)
    spec = np.abs(np.fft.rfft(high))
    freqs = np.fft.rfftfreq(high.size, d=1.0)
    mask = (freqs >= 1.0 / max_period_px) & (freqs <= 1.0 / min_period_px)
    if not np.any(mask):
        return float("nan"), 0.0
    idxs = np.where(mask)[0]
    j = int(idxs[np.argmax(spec[idxs])])
    period = 1.0 / freqs[j]
    if 1 <= j < len(spec) - 1:
        y0 = math.log(float(spec[j - 1]) + 1e-12)
        y1 = math.log(float(spec[j]) + 1e-12)
        y2 = math.log(float(spec[j + 1]) + 1e-12)
        denom = y0 - 2.0 * y1 + y2
        if abs(denom) > 1e-12:
            delta = 0.5 * (y0 - y2) / denom
            refined_freq = freqs[j] + delta * (freqs[1] - freqs[0])
            if refined_freq > 0:
                period = 1.0 / refined_freq
    return float(period), float(spec[j])


def decade_label_check(gray: np.ndarray, y1: int, y2: int) -> tuple[list[float], float]:
    crop = gray[max(0, y1 + 5) : min(gray.shape[0], y2 - 4), :]
    if crop.size == 0:
        return [], float("nan")
    threshold = float(np.percentile(crop, 18))
    mask = crop < threshold
    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    centers: list[float] = []
    for label in range(1, n_labels):
        _x, _y, ww, hh, area = stats[label]
        if 18 <= ww <= 55 and 9 <= hh <= 30 and area >= 120:
            centers.append(float(centroids[label][0]))
    centers = sorted(centers)
    if len(centers) >= 3:
        px_per_cm = float(np.median(np.diff(centers) / 10.0))
    else:
        px_per_cm = float("nan")
    return centers, px_per_cm


def estimate_px_per_cm(frames: list[np.ndarray], out_dir: Path) -> tuple[float, float, dict[str, float]]:
    h, w = frames[0].shape[:2]
    sample_ids = np.linspace(0, len(frames) - 1, min(12, len(frames)), dtype=int)
    rows: list[dict[str, object]] = []
    estimates: list[float] = []
    label_estimates: list[float] = []
    last_edges = (0, 0)

    for frame_id in sample_ids:
        gray = cv2.cvtColor(frames[int(frame_id)], cv2.COLOR_BGR2GRAY).astype(np.float32)
        y1, y2 = detect_ruler_edges(gray)
        last_edges = (y1, y2)
        bands = [
            ("upper_mm_ticks", max(0, y1 - 1), min(h, y1 + 8)),
            ("upper_mm_ticks_wide", max(0, y1 + 1), min(h, y1 + 15)),
            ("lower_mm_ticks", max(0, y2 - 12), min(h, y2 + 2)),
            ("lower_mm_ticks_wide", max(0, y2 - 8), min(h, y2 + 4)),
            ("whole_ruler_band", max(0, y1), min(h, y2)),
        ]
        for name, a, b in bands:
            if b <= a:
                continue
            profile = 255.0 - gray[a:b, :].mean(axis=0)
            mm_period, strength = fft_period(profile, 2.3, 3.4)
            px_per_cm = mm_period * 10.0
            used = bool(np.isfinite(px_per_cm) and 24.0 <= px_per_cm <= 34.0)
            if used:
                estimates.append(px_per_cm)
            rows.append(
                {
                    "frame": int(frame_id),
                    "ruler_y1_px": int(y1),
                    "ruler_y2_px": int(y2),
                    "strip": name,
                    "period_px": f"{mm_period:.6f}",
                    "px_per_cm": f"{px_per_cm:.6f}",
                    "strength": f"{strength:.6f}",
                    "used": int(used),
                }
            )
        labels, label_px_per_cm = decade_label_check(gray, y1, y2)
        if np.isfinite(label_px_per_cm):
            label_estimates.append(label_px_per_cm)
        rows.append(
            {
                "frame": int(frame_id),
                "ruler_y1_px": int(y1),
                "ruler_y2_px": int(y2),
                "strip": "ten_cm_label_check",
                "period_px": "",
                "px_per_cm": f"{label_px_per_cm:.6f}" if np.isfinite(label_px_per_cm) else "",
                "strength": json.dumps(labels),
                "used": 0,
            }
        )

    if len(estimates) < 6:
        raise RuntimeError("ruler calibration failed: too few millimeter tick estimates")
    arr = np.array(estimates, dtype=float)
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    keep = np.abs(arr - med) <= max(3.0 * mad, 0.35)
    used = arr[keep] if keep.sum() >= 6 else arr
    px_per_cm = float(np.median(used))
    spread = float(max(np.std(used, ddof=1) if used.size > 1 else 0.0, 0.08))

    with (out_dir / "ruler_calibration.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["frame", "ruler_y1_px", "ruler_y2_px", "strip", "period_px", "px_per_cm", "strength", "used"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    diag = frames[int(sample_ids[len(sample_ids) // 2])].copy()
    gray_diag = cv2.cvtColor(diag, cv2.COLOR_BGR2GRAY).astype(np.float32)
    y1, y2 = detect_ruler_edges(gray_diag)
    cv2.rectangle(diag, (0, y1), (w - 1, y2), (0, 0, 255), 2)
    label_scale = float(np.median(label_estimates)) if label_estimates else float("nan")
    cv2.putText(
        diag,
        f"px/cm={px_per_cm:.3f}, std={spread:.3f}, label_check={label_scale:.2f}",
        (20, max(35, y1 - 18)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2,
    )
    write_png(out_dir / "ruler_calibration_diagnostic.png", diag)
    return px_per_cm, spread, {"ruler_y0": int(y1), "ruler_y1": int(y2), "label_px_per_cm": label_scale, "last_y0": int(last_edges[0]), "last_y1": int(last_edges[1])}


def extract_waterline(frames: list[np.ndarray]) -> tuple[np.ndarray, tuple[int, int], np.ndarray]:
    h, w = frames[0].shape[:2]
    xs = np.arange(w)
    ruler_top, _ = find_ruler_band(frames[min(len(frames) - 1, len(frames) // 2)])
    y0 = max(8, int(h * 0.08))
    y1 = min(max(y0 + 40, ruler_top - 28), int(h * 0.44))
    lines: list[np.ndarray] = []
    reliability: list[np.ndarray] = []

    for frame in frames:
        b, g, r = cv2.split(frame)
        score = 0.95 * g.astype(np.float32) + 0.65 * b.astype(np.float32) - 0.30 * r.astype(np.float32)
        score = cv2.GaussianBlur(score, (7, 7), 0)
        roi = score[y0:y1]
        grad = np.gradient(roi, axis=0)
        grad = gaussian_filter1d(grad, 1.0, axis=0)
        lo, hi = max(2, int(0.03 * (y1 - y0))), max(8, int(0.98 * (y1 - y0)))
        sub = np.maximum(grad[lo:hi], 0)
        krel = np.argmax(sub, axis=0)
        strengths = sub[krel, np.arange(w)]
        y = (y0 + lo + krel).astype(np.float32)
        strength_scale = float(np.percentile(strengths, 90) - np.percentile(strengths, 10) + 1e-6)
        rel = np.clip((strengths - np.percentile(strengths, 10)) / strength_scale, 0, 1).astype(np.float32)

        weak = strengths < np.percentile(strengths, 12)
        y[weak] = np.nan
        valid = np.isfinite(y)
        if valid.sum() > max(50, int(0.20 * w)):
            y = np.interp(xs, xs[valid], y[valid]).astype(np.float32)
        else:
            y = np.nan_to_num(y, nan=np.nanmedian(y)).astype(np.float32)
        med = float(np.median(y))
        mad = float(np.median(np.abs(y - med)))
        y[np.abs(y - med) > max(24.0, 4.0 * mad)] = np.nan
        valid = np.isfinite(y)
        if valid.sum() > max(50, int(0.20 * w)):
            y = np.interp(xs, xs[valid], y[valid]).astype(np.float32)
        else:
            y = np.nan_to_num(y, nan=med).astype(np.float32)

        y = median_filter(y, size=max(9, (w // 90) | 1), mode="nearest")
        win = max(31, ((w // 16) | 1))
        if win >= w:
            win = w - 1 if (w - 1) % 2 else w - 2
        y = savgol_filter(y, win, 3, mode="interp").astype(np.float32)
        lines.append(y)
        reliability.append(rel)
    return np.vstack(lines), (y0, y1), np.vstack(reliability)


def repair_waterline_artifacts(ylines: np.ndarray, px_per_cm: float) -> tuple[np.ndarray, np.ndarray]:
    y = ylines.astype(np.float32).copy()
    repair_mask = np.zeros(y.shape, dtype=bool)

    temporal = median_filter(y, size=(5, 1), mode="nearest")
    residual = y - temporal
    for i in range(y.shape[0]):
        med = float(np.median(residual[i]))
        mad = float(np.median(np.abs(residual[i] - med)))
        bad = np.abs(residual[i] - med) > max(8.0, 5.0 * mad)
        if bad.any():
            y[i, bad] = temporal[i, bad]
            repair_mask[i, bad] = True

    n = y.shape[1]
    broad_win = odd_window(n, int(round(max(91.0, 2.2 * px_per_cm))))
    narrow_win = max(9, int(round(0.35 * px_per_cm)) | 1)
    for i in range(y.shape[0]):
        baseline = savgol_filter(y[i], broad_win, 3, mode="interp")
        residual = y[i] - baseline
        med = float(np.median(residual))
        mad = float(np.median(np.abs(residual - med)))
        bad = np.abs(residual - med) > max(7.0, 4.5 * mad)
        if bad.any():
            y[i, bad] = baseline[bad]
            repair_mask[i, bad] = True
        y[i] = median_filter(y[i], size=narrow_win, mode="nearest")
        y[i] = savgol_filter(y[i], broad_win, 3, mode="interp").astype(np.float32)
    return y, repair_mask


def odd_window(n: int, preferred: int) -> int:
    value = min(preferred, n if n % 2 else n - 1)
    value = max(5, value)
    if value % 2 == 0:
        value -= 1
    return value


def frame_autocorr_period(row: np.ndarray, dx_cm: float, band: tuple[float, float]) -> tuple[float, float]:
    row = detrend(row.astype(float), type="linear")
    row -= np.nanmean(row)
    den = float(np.dot(row, row))
    if den < 1e-12:
        return float("nan"), float("nan")
    corr = np.correlate(row, row, mode="full")[len(row) - 1 :] / den
    lags = np.arange(len(corr)) * dx_cm
    mask = (lags >= band[0]) & (lags <= band[1])
    idxs = np.where(mask)[0]
    if idxs.size < 5:
        return float("nan"), float("nan")
    win = odd_window(idxs.size, 51)
    sm = savgol_filter(corr, win, 3, mode="interp")
    peaks, props = find_peaks(sm[idxs], prominence=0.01)
    if len(peaks):
        local = peaks[np.argmax(sm[idxs][peaks])]
        idx = int(idxs[local])
    else:
        idx = int(idxs[np.argmax(sm[idxs])])
    return float(lags[idx]), float(sm[idx])


def robust_global_period(eta: np.ndarray, dx_cm: float, band: tuple[float, float]) -> tuple[float, float, int]:
    periods = []
    strengths = []
    for row in eta:
        p, s = frame_autocorr_period(row, dx_cm, band)
        if np.isfinite(p) and np.isfinite(s):
            periods.append(p)
            strengths.append(s)
    if not periods:
        return float("nan"), float("nan"), 0
    arr = np.array(periods)
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    keep = np.abs(arr - med) <= max(3.0 * mad, 0.18 * med)
    if keep.sum() >= 3:
        arr = arr[keep]
    return float(np.median(arr)), float(np.median(np.abs(arr - np.median(arr)))), int(arr.size)


def direct_peak_spacing(
    row: np.ndarray,
    dx_cm: float,
    period_hint: float,
    band: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    n = len(row)
    smooth = savgol_filter(row.astype(float), odd_window(n, 81), 3, mode="interp")
    smooth = detrend(smooth, type="linear")
    smooth -= np.median(smooth)
    amp = float(np.percentile(smooth, 95) - np.percentile(smooth, 5))
    prom = max(0.12 * np.std(smooth), 0.08 * amp, 0.10)
    if np.isfinite(period_hint):
        min_dist_cm = max(0.35 * period_hint, band[0] * 0.45)
    else:
        min_dist_cm = band[0] * 0.55
    min_dist = max(5, int(round(min_dist_cm / dx_cm)))
    peaks, props = find_peaks(smooth, distance=min_dist, prominence=prom)
    if len(peaks) >= 2:
        ds = np.diff(peaks) * dx_cm
        lo = max(band[0], 0.55 * period_hint) if np.isfinite(period_hint) else band[0]
        hi = min(band[1], 1.55 * period_hint) if np.isfinite(period_hint) else band[1]
        if np.isfinite(period_hint):
            lo = max(band[0], 0.45 * period_hint)
        if lo >= hi:
            lo, hi = band
        keep = (ds >= lo) & (ds <= hi)
        ds = ds[keep]
        if len(ds):
            left_peaks = peaks[:-1][keep]
            right_peaks = peaks[1:][keep]
            return peaks, left_peaks, ds, prom
    return peaks, np.array([], dtype=int), np.array([], dtype=float), prom


def weighted_trimmed_mean(values: np.ndarray, weights: np.ndarray) -> tuple[float, np.ndarray]:
    finite = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values = values[finite]
    weights = weights[finite]
    if values.size == 0:
        return float("nan"), finite
    med = float(np.median(values))
    mad = float(np.median(np.abs(values - med)))
    keep = np.abs(values - med) <= max(3.0 * mad, 0.12 * med, 0.75)
    if keep.sum() < max(3, int(0.35 * values.size)):
        keep = np.ones_like(values, dtype=bool)
    mean = float(np.average(values[keep], weights=weights[keep]))
    full_keep = np.zeros(finite.shape, dtype=bool)
    full_keep[np.where(finite)[0][keep]] = True
    return mean, full_keep


def save_contact_sheet(frames: list[np.ndarray], ylines: np.ndarray, rows: list[dict[str, object]], out: Path) -> None:
    n = len(frames)
    picks = sorted(set([0, n // 5, 2 * n // 5, 3 * n // 5, 4 * n // 5, n - 1]))
    thumbs = []
    for idx in picks:
        img = frames[idx].copy()
        yline = ylines[idx]
        pts = np.column_stack([np.arange(len(yline)), np.round(yline).astype(int)]).reshape(-1, 1, 2)
        cv2.polylines(img, [pts], False, (0, 0, 255), 2, cv2.LINE_AA)
        peaks = rows[idx]["peak_x_px_all"]
        for p in peaks:
            p_int = int(p)
            cv2.drawMarker(img, (p_int, int(round(yline[p_int]))), (255, 0, 0), cv2.MARKER_CROSS, 18, 2)
        label = f"f{idx} t={rows[idx]['time_s']:.2f}s best={rows[idx]['best_spacing_cm']:.2f}cm"
        cv2.putText(img, label, (18, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.78, (0, 255, 255), 2)
        thumbs.append(cv2.resize(img, (480, 270)))
    while len(thumbs) < 6:
        thumbs.append(np.zeros_like(thumbs[0]))
    canvas = np.vstack([np.hstack(thumbs[:3]), np.hstack(thumbs[3:6])])
    write_png(out, canvas)


def plot_spacing(rows: list[dict[str, object]], summary: dict[str, object], out: Path) -> None:
    t = np.array([float(r["time_s"]) for r in rows])
    best = np.array([float(r["best_spacing_cm"]) for r in rows])
    direct = np.array([float(r["direct_spacing_cm"]) for r in rows])
    ac = np.array([float(r["autocorr_spacing_cm"]) for r in rows])
    quality = np.array([float(r["quality_weight"]) for r in rows])
    keep = np.array([bool(r["used_for_average"]) for r in rows])

    fig, ax = plt.subplots(figsize=(10, 5.4), dpi=160)
    ax.plot(t, ac, color="#A6A6A6", lw=1, alpha=0.65, label="autocorr fallback")
    ax.scatter(t, best, c=quality, cmap="viridis", s=30, edgecolor="black", linewidth=0.25, label="per-frame best")
    ax.scatter(t[keep], best[keep], facecolors="none", edgecolors="#D55E00", s=72, linewidth=1.2, label="used for average")
    finite_direct = np.isfinite(direct)
    ax.scatter(t[finite_direct], direct[finite_direct], color="#0072B2", s=16, alpha=0.65, label="direct peak spacing")
    avg = float(summary["recommended_average_cm"])
    ax.axhline(avg, color="#D55E00", ls="--", lw=1.5, label=f"recommended average {avg:.2f} cm")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("crest spacing (cm)")
    ax.set_title("Frame-by-frame crest spacing")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=8)
    plt.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_profile_diagnostics(
    eta: np.ndarray,
    x_cm: np.ndarray,
    frame_indices: list[int],
    rows: list[dict[str, object]],
    out: Path,
) -> None:
    n = eta.shape[0]
    picks = sorted(set([0, n // 5, 2 * n // 5, 3 * n // 5, 4 * n // 5, n - 1]))
    fig, axes = plt.subplots(len(picks), 1, figsize=(10, 2.1 * len(picks)), dpi=140, sharex=True)
    if len(picks) == 1:
        axes = [axes]
    for ax, idx in zip(axes, picks):
        row = rows[idx]
        peaks = np.array(row["peak_x_px_all"], dtype=int)
        ax.plot(x_cm, eta[idx], lw=1.1)
        if peaks.size:
            ax.scatter(x_cm[peaks], eta[idx, peaks], color="red", s=14, zorder=3)
        ax.set_title(
            f"frame {frame_indices[idx]}  t={float(row['time_s']):.2f}s  "
            f"best={float(row['best_spacing_cm']):.2f} cm  "
            f"direct={float(row['direct_spacing_cm']):.2f} cm  peaks={int(row['n_peaks'])}"
        )
        ax.grid(True, alpha=0.25)
    axes[-1].set_xlabel("x (cm)")
    plt.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def list_to_text(values: np.ndarray, precision: int = 3) -> str:
    if values.size == 0:
        return ""
    return ";".join(f"{float(v):.{precision}f}" for v in values)


def main() -> None:
    root = Path.cwd()
    video = root / VIDEO_NAME
    if not video.exists():
        raise FileNotFoundError(video)
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()

    frames_all, fps, video_meta = load_video(video)
    valid_idx, bad_idx = select_valid_frames(frames_all)
    frames = [frames_all[i] for i in valid_idx]
    if len(frames) < 10:
        raise RuntimeError("too few valid video frames")

    n = len(frames)
    h, w = frames[0].shape[:2]
    time = np.array(valid_idx, dtype=float) / fps

    px_per_cm, px_spread, cal_diag = estimate_px_per_cm(frames, OUT_DIR)
    dx_cm = 1.0 / px_per_cm
    ylines_raw, roi, reliability = extract_waterline(frames)
    ylines, waterline_repair_mask = repair_waterline_artifacts(ylines_raw, px_per_cm)

    eta = -ylines.astype(float)
    eta -= np.median(eta, axis=1, keepdims=True)
    eta -= np.median(eta, axis=0, keepdims=True)
    eta = median_filter(eta, size=(1, 5), mode="nearest")

    field_width_cm = (w - 1) * dx_cm
    period_band = (max(DEFAULT_PERIOD_BAND_CM[0], 0.25 * field_width_cm), min(DEFAULT_PERIOD_BAND_CM[1], 0.92 * field_width_cm))
    if period_band[1] <= period_band[0] + 2:
        period_band = DEFAULT_PERIOD_BAND_CM
    global_period, global_period_mad, global_period_n = robust_global_period(eta, dx_cm, period_band)

    rows: list[dict[str, object]] = []
    sample_rows: list[dict[str, object]] = []
    for local_i, frame_no in enumerate(valid_idx):
        row = eta[local_i]
        peaks, left_peaks, distances, prom = direct_peak_spacing(row, dx_cm, global_period, period_band)
        ac_period, ac_strength = frame_autocorr_period(row, dx_cm, period_band)
        direct_spacing = float(np.median(distances)) if distances.size else float("nan")
        direct_mad = float(np.median(np.abs(distances - direct_spacing))) if distances.size else float("nan")
        if np.isfinite(direct_spacing):
            best_spacing = direct_spacing
            method = "direct_peaks"
        elif np.isfinite(ac_period):
            best_spacing = ac_period
            method = "autocorr_fallback"
        else:
            best_spacing = float("nan")
            method = "invalid"
        amp_px = float(np.percentile(row, 95) - np.percentile(row, 5))
        consistency = 1.0
        if distances.size >= 2 and np.isfinite(direct_spacing) and direct_spacing > 0:
            consistency = float(np.clip(1.0 - np.std(distances) / max(direct_spacing, 1e-6), 0.0, 1.0))
        peak_count_score = min(1.0, max(0.0, (len(peaks) - 1) / 2.0))
        ac_score = float(np.clip((ac_strength - 0.08) / 0.25, 0, 1)) if np.isfinite(ac_strength) else 0.0
        direct_score = 1.0 if distances.size else 0.0
        rel_score = float(np.nanmedian(reliability[local_i]))
        repaired_columns = int(waterline_repair_mask[local_i].sum())
        repair_fraction = repaired_columns / float(w)
        repair_score = float(np.clip(1.0 - repair_fraction / 0.12, 0.0, 1.0))
        quality = float(
            np.clip(
                0.40 * direct_score + 0.20 * peak_count_score + 0.20 * consistency + 0.10 * ac_score + 0.10 * rel_score,
                0,
                1,
            )
        )
        quality *= repair_score
        if method == "autocorr_fallback":
            quality *= 0.55
        if not np.isfinite(best_spacing):
            quality = 0.0

        peak_x_all_cm = peaks * dx_cm
        row_record = {
            "frame": int(frame_no),
            "time_s": float(frame_no / fps),
            "valid_video_frame_index": int(local_i),
            "method": method,
            "best_spacing_cm": float(best_spacing),
            "direct_spacing_cm": float(direct_spacing),
            "direct_spacing_mad_cm": float(direct_mad),
            "autocorr_spacing_cm": float(ac_period),
            "autocorr_strength": float(ac_strength),
            "n_peaks": int(len(peaks)),
            "n_direct_intervals": int(distances.size),
            "quality_weight": float(quality),
            "waterline_amp_px_p95_p5": amp_px,
            "waterline_repaired_columns": repaired_columns,
            "waterline_repaired_fraction": repair_fraction,
            "prominence_threshold_px": float(prom),
            "peak_x_px_all": peaks.astype(int).tolist(),
            "peak_x_cm_all": peak_x_all_cm.astype(float).tolist(),
            "direct_interval_cm_list": distances.astype(float).tolist(),
            "used_for_average": False,
        }
        rows.append(row_record)

        for j, d in enumerate(distances):
            p1 = int(left_peaks[j])
            p2 = int(peaks[np.where(peaks == p1)[0][0] + 1]) if p1 in set(peaks.tolist()) else int(left_peaks[j])
            sample_rows.append(
                {
                    "frame": int(frame_no),
                    "time_s": float(frame_no / fps),
                    "left_peak_x_px": p1,
                    "right_peak_x_px": p2,
                    "left_peak_x_cm": float(p1 * dx_cm),
                    "right_peak_x_cm": float(p2 * dx_cm),
                    "distance_cm": float(d),
                    "frame_quality_weight": float(quality),
                }
            )

    best_values = np.array([float(r["best_spacing_cm"]) for r in rows])
    direct_values = np.array([float(r["direct_spacing_cm"]) for r in rows])
    weights = np.array([float(r["quality_weight"]) for r in rows])
    fallback_recommended, keep_best = weighted_trimmed_mean(best_values, weights)
    direct_recommended, keep_direct = weighted_trimmed_mean(direct_values, weights)
    if keep_direct.sum() >= max(10, int(0.15 * len(rows))):
        recommended = direct_recommended
        recommended_source = "direct_peak_weighted_trimmed_mean"
        keep_average = keep_direct
    else:
        recommended = fallback_recommended
        recommended_source = "best_spacing_weighted_trimmed_mean"
        keep_average = keep_best

    for row, keep in zip(rows, keep_average):
        row["used_for_average"] = bool(keep)

    source_values = direct_values if recommended_source.startswith("direct_peak") else best_values
    used_values = source_values[keep_average]
    used_weights = weights[keep_average]
    if used_values.size:
        weighted_var = float(np.average((used_values - recommended) ** 2, weights=used_weights))
        recommended_std = math.sqrt(weighted_var)
        recommended_median = float(np.median(used_values))
        recommended_mad = float(np.median(np.abs(used_values - recommended_median)))
    else:
        recommended_std = float("nan")
        recommended_median = float("nan")
        recommended_mad = float("nan")

    direct_used_values = direct_values[keep_direct]
    direct_median = float(np.nanmedian(direct_used_values)) if direct_used_values.size else float("nan")
    all_direct_samples = np.array([r["distance_cm"] for r in sample_rows], dtype=float)
    sample_avg = float(np.nanmean(all_direct_samples)) if all_direct_samples.size else float("nan")
    sample_median = float(np.nanmedian(all_direct_samples)) if all_direct_samples.size else float("nan")

    summary = {
        "video": str(video.resolve()),
        "frame_count_total": int(len(frames_all)),
        "frame_count_valid": int(len(frames)),
        "invalid_frame_indices": bad_idx,
        "fps": float(fps),
        "duration_s": float((len(frames_all) - 1) / fps if frames_all else 0),
        "width_px": int(w),
        "height_px": int(h),
        "px_per_cm": float(px_per_cm),
        "cm_per_px": float(dx_cm),
        "px_per_cm_diagnostic_spread": float(px_spread),
        "field_width_cm": float(field_width_cm),
        "waterline_roi_y0_px": int(roi[0]),
        "waterline_roi_y1_px": int(roi[1]),
        "waterline_repaired_cells": int(waterline_repair_mask.sum()),
        "period_band_cm": [float(period_band[0]), float(period_band[1])],
        "global_autocorr_period_cm": float(global_period),
        "global_autocorr_period_mad_cm": float(global_period_mad),
        "global_autocorr_period_frame_count": int(global_period_n),
        "recommended_average_cm": float(recommended),
        "recommended_average_std_cm": float(recommended_std),
        "recommended_average_median_cm": float(recommended_median),
        "recommended_average_mad_cm": float(recommended_mad),
        "recommended_average_source": recommended_source,
        "fallback_best_spacing_weighted_average_cm": float(fallback_recommended),
        "recommended_average_used_frames": int(keep_average.sum()),
        "direct_peak_weighted_average_cm": float(direct_recommended),
        "direct_peak_median_cm": float(direct_median),
        "direct_peak_frames_used": int(keep_direct.sum()),
        "direct_peak_interval_sample_average_cm": float(sample_avg),
        "direct_peak_interval_sample_median_cm": float(sample_median),
        "direct_peak_interval_sample_count": int(all_direct_samples.size),
        "calibration_diagnostic": cal_diag,
        "video_meta": {k: (float(v) if isinstance(v, (int, float)) else v) for k, v in video_meta.items() if k != "ffmpeg_version"},
    }

    with (OUT_DIR / "frame_peak_spacing_timeseries.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fieldnames = [
            "frame",
            "time_s",
            "method",
            "best_spacing_cm",
            "direct_spacing_cm",
            "direct_spacing_mad_cm",
            "autocorr_spacing_cm",
            "autocorr_strength",
            "n_peaks",
            "n_direct_intervals",
            "quality_weight",
            "used_for_average",
            "waterline_amp_px_p95_p5",
            "waterline_repaired_columns",
            "waterline_repaired_fraction",
            "prominence_threshold_px",
            "peak_x_px_all",
            "peak_x_cm_all",
            "direct_interval_cm_list",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out_row = dict(row)
            out_row["peak_x_px_all"] = ";".join(str(v) for v in row["peak_x_px_all"])
            out_row["peak_x_cm_all"] = ";".join(f"{float(v):.4f}" for v in row["peak_x_cm_all"])
            out_row["direct_interval_cm_list"] = ";".join(f"{float(v):.4f}" for v in row["direct_interval_cm_list"])
            writer.writerow({k: out_row.get(k, "") for k in fieldnames})

    with (OUT_DIR / "direct_peak_interval_samples.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fieldnames = [
            "frame",
            "time_s",
            "left_peak_x_px",
            "right_peak_x_px",
            "left_peak_x_cm",
            "right_peak_x_cm",
            "distance_cm",
            "frame_quality_weight",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_rows)

    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    with (OUT_DIR / "summary_cn.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["项目", "数值", "说明"])
        writer.writerow(["最合理平均波峰间距_cm", f"{recommended:.6f}", "高质量逐帧直接相邻波峰的稳健加权截尾均值；直接样本不足时才退回 best_spacing"])
        writer.writerow(["平均值标准差_cm", f"{recommended_std:.6f}", "用于平均的逐帧值的加权标准差"])
        writer.writerow(["平均值中位数_cm", f"{recommended_median:.6f}", "用于平均的逐帧值中位数"])
        writer.writerow(["平均值MAD_cm", f"{recommended_mad:.6f}", "用于平均的逐帧值中位绝对偏差"])
        writer.writerow(["直接波峰加权平均_cm", f"{direct_recommended:.6f}", "仅使用检测到相邻波峰的帧"])
        writer.writerow(["直接波峰样本中位数_cm", f"{sample_median:.6f}", "所有相邻波峰间距样本"])
        writer.writerow(["直接波峰样本数", all_direct_samples.size, "逐帧相邻波峰间距条目数"])
        writer.writerow(["逐帧总数", len(frames_all), "视频解码帧数"])
        writer.writerow(["有效分析帧数", len(frames), "剔除黑帧/坏帧后"])
        writer.writerow(["用于平均帧数", int(keep_average.sum()), "通过稳健过滤的帧"])
        writer.writerow(["fps", f"{fps:.6f}", "帧率"])
        writer.writerow(["px_per_cm", f"{px_per_cm:.6f}", "背景直尺估计"])
        writer.writerow(["cm_per_px", f"{dx_cm:.9f}", "像素到厘米换算"])
        writer.writerow(["视场宽度_cm", f"{field_width_cm:.6f}", "水平像素宽度换算"])
        writer.writerow(["全局自相关周期_cm", f"{global_period:.6f}", "辅助确定逐帧搜索范围"])

    report = f"""# 4.4 视频逐帧波峰间距分析

## 结论

- 最合理平均波峰间距：**{recommended:.3f} cm**
- 用于该平均值的帧数：{int(keep_average.sum())} / {len(frames)} 帧
- 对应用于平均的逐帧离散度：标准差 {recommended_std:.3f} cm，MAD {recommended_mad:.3f} cm
- 仅直接相邻波峰检测得到的加权平均：{direct_recommended:.3f} cm
- 直接相邻波峰间距样本：{all_direct_samples.size} 个，样本中位数 {sample_median:.3f} cm

## 方法

1. 使用 ffmpeg 解码 `6.mp4` 的全部 {len(frames_all)} 帧，帧率 {fps:.6f} fps。
2. 用背景直尺估计比例尺：{px_per_cm:.3f} px/cm，即 {dx_cm:.6f} cm/px。
3. 每帧提取水线，转为相对水面位移曲线 `eta(x,t)`。
4. 每帧先找相邻波峰并计算直接峰距；若当帧可见波峰不足，则用同一帧空间自相关作为 fallback。
5. 最终平均值优先采用逐帧直接相邻波峰的质量加权稳健截尾均值；只有直接波峰帧不足时才使用自相关 fallback。

## 输出文件

- `frame_peak_spacing_timeseries.csv`：逐帧完整时间序列。
- `direct_peak_interval_samples.csv`：每一对相邻波峰的间距样本。
- `summary_cn.csv` / `summary.json`：汇总统计。
- `peak_spacing_vs_time.png`：波峰间距随时间变化图。
- `waterline_and_peaks_contact_sheet.png`：抽样帧水线和波峰叠加复核图。
- `profile_peak_diagnostics.png`：抽样帧水线剖面与峰点复核图。
- `ruler_calibration_diagnostic.png`：直尺标定复核图。
"""
    (OUT_DIR / "peak_spacing_report_cn.md").write_text(report, encoding="utf-8")

    save_contact_sheet(frames, ylines, rows, OUT_DIR / "waterline_and_peaks_contact_sheet.png")
    plot_spacing(rows, summary, OUT_DIR / "peak_spacing_vs_time.png")
    plot_profile_diagnostics(eta, np.arange(w) * dx_cm, valid_idx, rows, OUT_DIR / "profile_peak_diagnostics.png")

    np.savez_compressed(
        OUT_DIR / "analysis_data.npz",
        ylines_px=ylines,
        ylines_raw_px=ylines_raw,
        waterline_repair_mask=waterline_repair_mask,
        eta_px=eta,
        time_s=time,
        x_cm=np.arange(w) * dx_cm,
        px_per_cm=px_per_cm,
        frame_indices=np.array(valid_idx, dtype=np.int32),
        best_spacing_cm=best_values,
        quality_weight=weights,
        used_for_average=keep_average,
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

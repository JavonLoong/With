# -*- coding: utf-8 -*-
"""Data group 12 water-wave reflection / standing-wave analysis.

All outputs are written next to this script.  The video filename itself is
ASCII, so the decoder is opened from this directory with a relative path; this
avoids the OpenCV/PowerShell non-ASCII path issue seen on this workstation.
"""

from __future__ import annotations

import csv
import json
import math
import os
from pathlib import Path

import cv2
import imageio.v3 as iio
import numpy as np
from scipy.ndimage import gaussian_filter, gaussian_filter1d, median_filter, uniform_filter1d
from scipy.signal import find_peaks, savgol_filter


BASE_DIR = Path(__file__).resolve().parent
VIDEO_NAME = "906c14e37f39c284cb542371456ef8e7.mp4"

os.chdir(BASE_DIR)
os.environ.setdefault("MPLCONFIGDIR", str(BASE_DIR))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.font_manager as fm  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


def configure_chinese_font() -> None:
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttf"),
    ]
    for font_path in candidates:
        if font_path.exists():
            fm.fontManager.addfont(str(font_path))
            prop = fm.FontProperties(fname=str(font_path))
            plt.rcParams["font.family"] = "sans-serif"
            plt.rcParams["font.sans-serif"] = [prop.get_name()]
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 150


def save_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_video() -> tuple[np.ndarray, dict[str, object]]:
    frames = [frame for frame in iio.imiter(VIDEO_NAME, plugin="FFMPEG")]
    if not frames:
        raise RuntimeError(f"未能从视频读取任何帧: {VIDEO_NAME}")
    arr = np.stack(frames, axis=0).astype(np.uint8)
    try:
        meta_raw = iio.immeta(VIDEO_NAME, plugin="FFMPEG")
    except Exception:
        meta_raw = {}
    fps = float(meta_raw.get("fps") or 30.0)
    meta = {
        "video": VIDEO_NAME,
        "codec": meta_raw.get("codec", "unknown"),
        "fps": fps,
        "frame_count": int(arr.shape[0]),
        "height": int(arr.shape[1]),
        "width": int(arr.shape[2]),
        "duration_s": float(arr.shape[0] / fps),
        "decoder": "imageio_ffmpeg / FFMPEG",
        "note": "OpenCV 直接打开中文完整路径失败；本脚本在视频所在目录用 ASCII 文件名逐帧读取原 MP4。",
    }
    return arr, meta


def rgb_to_gray(frame: np.ndarray) -> np.ndarray:
    return (
        0.299 * frame[:, :, 0].astype(np.float32)
        + 0.587 * frame[:, :, 1].astype(np.float32)
        + 0.114 * frame[:, :, 2].astype(np.float32)
    )


def detect_ruler_edges(gray: np.ndarray) -> tuple[int, int]:
    h = gray.shape[0]
    search_y = np.arange(int(0.55 * h), int(0.80 * h))
    row_mean = gray.mean(axis=1)
    row_grad = uniform_filter1d(np.abs(np.gradient(row_mean)), size=5, mode="nearest")
    peaks, _ = find_peaks(
        row_grad[search_y],
        distance=18,
        prominence=max(float(np.std(row_grad[search_y]) * 0.5), 1.0),
    )
    candidates = sorted(
        [(int(search_y[p]), float(row_grad[search_y[p]])) for p in peaks],
        key=lambda item: item[1],
        reverse=True,
    )
    if len(candidates) >= 2:
        y1, y2 = sorted([candidates[0][0], candidates[1][0]])
    else:
        # Ruler is visible in this video; this branch is only a guard against
        # a single bad sample frame.  The final estimate uses many frames.
        y1, y2 = int(0.692 * h), int(0.738 * h)
    if y2 - y1 < 24:
        y2 = y1 + 32
    return y1, y2


def fft_period(profile: np.ndarray, min_period_px: float, max_period_px: float) -> tuple[float, float]:
    y = np.asarray(profile, dtype=float)
    detrend_width = int(max(9, round(max_period_px * 4)))
    if detrend_width % 2 == 0:
        detrend_width += 1
    high = y - uniform_filter1d(y, size=detrend_width, mode="nearest")
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
    centers = []
    for label in range(1, n_labels):
        x, y, w, h, area = stats[label]
        if 25 <= w <= 45 and 12 <= h <= 24 and area >= 180:
            centers.append(float(centroids[label][0]))
    centers = sorted(centers)
    if len(centers) >= 3:
        spacings = np.diff(centers) / 10.0
        px_per_cm = float(np.median(spacings))
    else:
        px_per_cm = float("nan")
    return centers, px_per_cm


def calibrate_ruler(frames: np.ndarray) -> dict[str, object]:
    h = frames.shape[1]
    sample_ids = np.linspace(0, frames.shape[0] - 1, min(12, frames.shape[0]), dtype=int)
    rows: list[dict[str, object]] = []
    estimates: list[float] = []
    label_checks: list[tuple[list[float], float]] = []

    for frame_id in sample_ids:
        gray = rgb_to_gray(frames[int(frame_id)])
        y1, y2 = detect_ruler_edges(gray)
        bands = [
            ("上沿毫米刻度", max(0, y1 - 1), min(h, y1 + 8)),
            ("上沿扩展毫米刻度", max(0, y1 + 1), min(h, y1 + 15)),
            ("下沿毫米刻度", max(0, y2 - 12), min(h, y2 + 2)),
            ("下沿扩展毫米刻度", max(0, y2 - 8), min(h, y2 + 4)),
        ]
        strip_estimates = []
        for name, a, b in bands:
            if b <= a:
                continue
            profile = 255.0 - gray[a:b, :].mean(axis=0)
            mm_period, strength = fft_period(profile, 2.60, 2.90)
            px_per_cm = mm_period * 10.0
            if np.isfinite(px_per_cm) and 24.0 <= px_per_cm <= 31.0:
                estimates.append(px_per_cm)
                strip_estimates.append(px_per_cm)
            rows.append(
                {
                    "frame": int(frame_id),
                    "ruler_y1_px": int(y1),
                    "ruler_y2_px": int(y2),
                    "strip": name,
                    "period_px": f"{mm_period:.6f}",
                    "px_per_cm": f"{px_per_cm:.6f}",
                    "strength": f"{strength:.6f}",
                    "used": int(np.isfinite(px_per_cm) and 24.0 <= px_per_cm <= 31.0),
                }
        )
        labels, label_px_per_cm = decade_label_check(gray, y1, y2)
        label_checks.append((labels, label_px_per_cm))
        rows.append(
            {
                "frame": int(frame_id),
                "ruler_y1_px": int(y1),
                "ruler_y2_px": int(y2),
                "strip": "十厘米数字标签辅助检查",
                "period_px": "",
                "px_per_cm": f"{label_px_per_cm:.6f}" if np.isfinite(label_px_per_cm) else "",
                "strength": json.dumps(labels, ensure_ascii=False),
                "used": 0,
            }
        )

    if len(estimates) < 6:
        raise RuntimeError("直尺刻度可见，但毫米刻度周期估计样本不足，不能可靠标定。")
    estimates_np = np.asarray(estimates, dtype=float)
    med = float(np.median(estimates_np))
    mad = float(np.median(np.abs(estimates_np - med)))
    keep = np.abs(estimates_np - med) <= max(0.35, 3.0 * mad)
    used = estimates_np[keep]
    px_per_cm = float(np.median(used))
    px_per_cm_std = float(max(np.std(used, ddof=1) if used.size > 1 else 0.0, 0.08))

    avg_gray = rgb_to_gray(np.mean(frames.astype(np.float32), axis=0).astype(np.uint8))
    diag_y1, diag_y2 = detect_ruler_edges(avg_gray)
    avg_labels, avg_label_scale = decade_label_check(avg_gray, diag_y1, diag_y2)
    finite_label_scales = [scale for _, scale in label_checks if np.isfinite(scale)]
    best_labels = max([labels for labels, _ in label_checks] + [avg_labels], key=len)
    diag_label_scale = (
        float(np.median(finite_label_scales))
        if finite_label_scales
        else float(avg_label_scale)
        if np.isfinite(avg_label_scale)
        else float("nan")
    )

    return {
        "px_per_cm": px_per_cm,
        "cm_per_px": 1.0 / px_per_cm,
        "px_per_cm_std": px_per_cm_std,
        "relative_scale_uncertainty_percent": 100.0 * px_per_cm_std / px_per_cm,
        "sample_count": int(used.size),
        "ruler_y1_px": int(diag_y1),
        "ruler_y2_px": int(diag_y2),
        "diagnostic_label_centers_px": best_labels,
        "diagnostic_label_px_per_cm": diag_label_scale,
        "calibration_rows": rows,
        "basis": "背景直尺清晰可见；采用多帧上/下沿毫米小刻度的空间频率估计，十厘米数字标签仅作透视/定位辅助检查。",
    }


def extract_surface(frames: np.ndarray, ruler: dict[str, object]) -> dict[str, object]:
    n_t, h, w, _ = frames.shape
    px_per_cm = float(ruler["px_per_cm"])
    y1 = int(max(90, 0.13 * h))
    y2 = int(min(float(ruler["ruler_y1_px"]) - 120, 0.43 * h))
    if y2 <= y1 + 50:
        y2 = int(0.43 * h)
    xs = np.arange(w)
    surface_y = np.zeros((n_t, w), dtype=np.float32)
    edge_strength = np.zeros((n_t, w), dtype=np.float32)

    for i, frame in enumerate(frames):
        green = frame[:, :, 1].astype(np.float32)
        smooth = cv2.GaussianBlur(green, (7, 7), 0)
        grad = cv2.Sobel(smooth, cv2.CV_32F, 0, 1, ksize=3)
        roi = grad[y1:y2, :]
        local_idx = np.argmax(roi, axis=0)
        y = local_idx.astype(np.float32) + y1
        strength = roi[local_idx, xs]

        wide = int(round(max(61.0, px_per_cm * 2.8)))
        if wide % 2 == 0:
            wide += 1
        y_med = median_filter(y, size=wide, mode="nearest")
        bad = (np.abs(y - y_med) > max(7.0, 0.25 * px_per_cm)) | (
            strength < np.percentile(strength, 10)
        )
        y[bad] = y_med[bad]

        mid = int(round(max(31.0, px_per_cm * 1.1)))
        if mid % 2 == 0:
            mid += 1
        y = median_filter(y, size=mid, mode="nearest")
        win = int(round(max(91.0, px_per_cm * 3.4)))
        win = min(win, 181)
        if win % 2 == 0:
            win += 1
        y = savgol_filter(y, window_length=win, polyorder=3, mode="interp")

        surface_y[i] = y
        edge_strength[i] = strength

    baseline_n = int(min(35, max(8, round(0.20 * n_t))))
    baseline_y = np.median(surface_y[:baseline_n], axis=0)
    baseline_y = savgol_filter(baseline_y, window_length=101, polyorder=2, mode="interp")
    eta_cm = (baseline_y[None, :] - surface_y) / px_per_cm
    eta_cm -= np.median(eta_cm, axis=1, keepdims=True)
    eta_cm = gaussian_filter(eta_cm, sigma=(0.35, 1.0), mode="nearest").astype(np.float32)

    return {
        "surface_y_px": surface_y,
        "baseline_y_px": baseline_y.astype(np.float32),
        "eta_cm": eta_cm,
        "edge_strength": edge_strength,
        "surface_search_y1": int(y1),
        "surface_search_y2": int(y2),
        "baseline_frame_count": baseline_n,
    }


def directional_separation(eta_cm: np.ndarray, fps: float, px_per_cm: float) -> dict[str, object]:
    eta = np.asarray(eta_cm, dtype=float)
    eta = eta - np.mean(eta, axis=0, keepdims=True)
    eta = eta - np.mean(eta, axis=1, keepdims=True)
    eta = gaussian_filter(eta, sigma=(0.30, 1.0), mode="nearest")
    n_t, n_x = eta.shape
    dt = 1.0 / fps
    dx_cm = 1.0 / px_per_cm

    f = np.fft.fftfreq(n_t, d=dt)[:, None]
    k = np.fft.fftfreq(n_x, d=dx_cm)[None, :]
    f_abs = np.abs(f)
    k_abs = np.abs(k)
    f_min = max(0.22, 1.3 / (n_t * dt))
    f_max = min(8.0, 0.45 * fps)
    k_min = max(1.0 / 80.0, 1.0 / (n_x * dx_cm * 1.3))
    k_max = 1.0 / 4.5
    band = (f_abs >= f_min) & (f_abs <= f_max) & (k_abs >= k_min) & (k_abs <= k_max)
    branch_same = band & (f * k > 0)
    branch_opposite = band & (f * k < 0)

    window = np.hanning(n_t)[:, None] * np.hanning(n_x)[None, :]
    spectrum_windowed = np.fft.fft2(eta * window)
    energy_same = float(np.sum(np.abs(spectrum_windowed[branch_same]) ** 2))
    energy_opposite = float(np.sum(np.abs(spectrum_windowed[branch_opposite]) ** 2))
    if energy_opposite >= energy_same:
        incident_mask = branch_opposite
        reflected_mask = branch_same
        incident_direction = "向右(+x)"
        incident_branch = "f*k<0"
    else:
        incident_mask = branch_same
        reflected_mask = branch_opposite
        incident_direction = "向左(-x)"
        incident_branch = "f*k>0"

    spectrum = np.fft.fft2(eta)
    eta_inc = np.fft.ifft2(spectrum * incident_mask).real.astype(np.float32)
    eta_ref = np.fft.ifft2(spectrum * reflected_mask).real.astype(np.float32)

    inc_energy_t = gaussian_filter1d(np.mean(eta_inc**2, axis=1), sigma=max(1.0, fps * 0.16))
    ref_energy_t = gaussian_filter1d(np.mean(eta_ref**2, axis=1), sigma=max(1.0, fps * 0.16))
    ratio_t = ref_energy_t / np.maximum(inc_energy_t, 1e-10)

    peak = diagnostic_fft_peak(eta, fps, px_per_cm, incident_branch)
    global_ref_inc = min(energy_same, energy_opposite) / max(energy_same, energy_opposite, 1e-12)

    return {
        "eta_for_fft_cm": eta.astype(np.float32),
        "eta_incident_cm": eta_inc,
        "eta_reflected_cm": eta_ref,
        "incident_direction": incident_direction,
        "incident_branch": incident_branch,
        "energy_same_fk": energy_same,
        "energy_opposite_fk": energy_opposite,
        "global_reflection_ratio_fft": float(global_ref_inc),
        "incident_energy_t": inc_energy_t.astype(np.float32),
        "reflected_energy_t": ref_energy_t.astype(np.float32),
        "reflection_ratio_t": ratio_t.astype(np.float32),
        "fft_diagnostic": peak,
        "band_f_min_hz": float(f_min),
        "band_f_max_hz": float(f_max),
        "band_k_min_cyc_cm": float(k_min),
        "band_k_max_cyc_cm": float(k_max),
    }


def diagnostic_fft_peak(
    eta: np.ndarray, fps: float, px_per_cm: float, incident_branch: str
) -> dict[str, float]:
    n_t, n_x = eta.shape
    dt = 1.0 / fps
    dx_cm = 1.0 / px_per_cm
    nt_pad = 2 ** int(math.ceil(math.log2(n_t * 4)))
    nx_pad = 2 ** int(math.ceil(math.log2(n_x * 4)))
    window = np.hanning(n_t)[:, None] * np.hanning(n_x)[None, :]
    spec = np.fft.fft2(eta * window, s=(nt_pad, nx_pad))
    f = np.fft.fftfreq(nt_pad, d=dt)[:, None]
    k = np.fft.fftfreq(nx_pad, d=dx_cm)[None, :]
    branch = (f * k < 0) if incident_branch == "f*k<0" else (f * k > 0)
    mask = (
        branch
        & (f > 0.20)
        & (f < min(7.0, fps * 0.45))
        & (np.abs(k) >= 1.0 / 60.0)
        & (np.abs(k) <= 1.0 / 6.0)
    )
    power = np.where(mask, np.abs(spec) ** 2, 0.0)
    idx = np.unravel_index(int(np.argmax(power)), power.shape)
    freq_hz = float(abs(f[idx[0], 0]))
    k_cyc_cm = float(abs(k[0, idx[1]]))
    wavelength = float(1.0 / k_cyc_cm) if k_cyc_cm > 0 else float("nan")
    return {
        "frequency_hz": freq_hz,
        "k_cyc_per_cm": k_cyc_cm,
        "lambda_cm": wavelength,
        "note": "短视频且视场不足两倍主波长；该 2D FFT 波长只作方向/频带诊断，不作为最终高精度波长。",
    }


def choose_stable_window(sep: dict[str, object], fps: float) -> dict[str, object]:
    ratio = np.asarray(sep["reflection_ratio_t"], dtype=float)
    inc = np.asarray(sep["incident_energy_t"], dtype=float)
    n = ratio.size
    window = int(min(n, max(18, round(0.85 * fps))))
    inc_threshold = max(float(np.percentile(inc, 45)), float(0.12 * np.max(inc)))
    candidates = []
    for start in range(0, n - window + 1):
        sl = slice(start, start + window)
        if float(np.median(inc[sl])) < inc_threshold:
            continue
        med_ratio = float(np.median(ratio[sl]))
        inc_cv = float(np.std(inc[sl]) / max(np.mean(inc[sl]), 1e-12))
        ratio_iqr = float(np.percentile(ratio[sl], 75) - np.percentile(ratio[sl], 25))
        energy_penalty = max(0.0, inc_threshold - float(np.median(inc[sl]))) / max(inc_threshold, 1e-12)
        score = med_ratio + 0.12 * inc_cv + 0.05 * ratio_iqr + 0.08 * energy_penalty
        candidates.append((score, med_ratio, inc_cv, ratio_iqr, start))
    if not candidates:
        start = max(0, int(np.argmax(inc) - window // 2))
        start = min(start, n - window)
        note = "未找到满足入射能量阈值的低反射窗口，改用入射能量峰值附近窗口。"
    else:
        _, med_ratio, inc_cv, ratio_iqr, start = min(candidates, key=lambda item: item[0])
        note = "在入射能量足够的候选窗口中，选择反射/入射能量比中位数最低且波动较小的窗口。"
    end = int(start + window - 1)
    sl = slice(start, end + 1)
    return {
        "start_frame": int(start),
        "end_frame": int(end),
        "start_time_s": float(start / fps),
        "end_time_s": float(end / fps),
        "window_frames": int(window),
        "median_reflection_ratio": float(np.median(ratio[sl])),
        "p25_reflection_ratio": float(np.percentile(ratio[sl], 25)),
        "p75_reflection_ratio": float(np.percentile(ratio[sl], 75)),
        "median_incident_energy_cm2": float(np.median(inc[sl])),
        "incident_energy_cv": float(np.std(inc[sl]) / max(np.mean(inc[sl]), 1e-12)),
        "selection_note": note,
    }


def subpixel_peak_x(values: np.ndarray, index: int) -> float:
    if index <= 0 or index >= len(values) - 1:
        return float(index)
    y0, y1, y2 = float(values[index - 1]), float(values[index]), float(values[index + 1])
    denom = y0 - 2.0 * y1 + y2
    if abs(denom) < 1e-12:
        return float(index)
    delta = 0.5 * (y0 - y2) / denom
    return float(index + np.clip(delta, -0.75, 0.75))


def peak_measurements_for_field(
    field_cm: np.ndarray,
    fps: float,
    px_per_cm: float,
    stable: dict[str, object],
    ratio_t: np.ndarray,
    incident_energy_t: np.ndarray,
    kind: str,
    expected_lambda_cm: float | None = None,
) -> dict[str, object]:
    n_t, n_x = field_cm.shape
    x_cm = np.arange(n_x, dtype=float) / px_per_cm
    margin_px = int(round(max(35, 1.2 * px_per_cm)))
    min_cm = 14.0
    max_cm = min(38.0, x_cm[-1] * 0.92)
    min_px = int(round(min_cm * px_per_cm))
    if expected_lambda_cm and np.isfinite(expected_lambda_cm):
        min_px = int(round(max(0.45 * expected_lambda_cm * px_per_cm, 10.0 * px_per_cm)))

    stable_frames = np.arange(int(stable["start_frame"]), int(stable["end_frame"]) + 1)
    active_ratio_limit = float(np.percentile(ratio_t, 70))
    active_energy_limit = max(float(np.percentile(incident_energy_t, 45)), float(0.10 * np.max(incident_energy_t)))
    extra_frames = np.where((ratio_t <= active_ratio_limit) & (incident_energy_t >= active_energy_limit))[0]
    frame_order = list(dict.fromkeys([int(i) for i in np.r_[stable_frames, extra_frames]]))

    rows = []

    def smoothed_profile(frame_id: int) -> np.ndarray:
        profile = field_cm[frame_id].astype(float).copy()
        profile -= np.median(profile)
        profile = gaussian_filter1d(profile, sigma=max(2.0, 0.22 * px_per_cm))
        profile -= np.polyval(np.polyfit(x_cm, profile, 1), x_cm)
        return profile

    for frame_id in frame_order:
        if frame_id < 0 or frame_id >= n_t:
            continue
        profile = smoothed_profile(frame_id)
        valid = profile[margin_px : n_x - margin_px]
        if valid.size < 10:
            continue
        prominence = max(float(np.std(valid) * 0.28), 0.015)
        peaks, props = find_peaks(valid, distance=max(20, min_px), prominence=prominence)
        peaks = peaks + margin_px
        if peaks.size < 2:
            continue
        for p1, p2 in zip(peaks[:-1], peaks[1:]):
            sx1 = subpixel_peak_x(profile, int(p1))
            sx2 = subpixel_peak_x(profile, int(p2))
            spacing_cm = (sx2 - sx1) / px_per_cm
            if min_cm <= spacing_cm <= max_cm:
                row = {
                    "kind": kind,
                    "frame": int(frame_id),
                    "time_s": float(frame_id / fps),
                    "x1_px": float(sx1),
                    "x2_px": float(sx2),
                    "x1_cm": float(sx1 / px_per_cm),
                    "x2_cm": float(sx2 / px_per_cm),
                    "spacing_cm": float(spacing_cm),
                    "eta1_cm": float(np.interp(sx1, np.arange(n_x), profile)),
                    "eta2_cm": float(np.interp(sx2, np.arange(n_x), profile)),
                    "from_stable_window": int(stable["start_frame"] <= frame_id <= stable["end_frame"]),
                }
                rows.append(row)

    stable_count = int(sum(r["from_stable_window"] for r in rows))
    stable_rows = [r for r in rows if r["from_stable_window"]]
    if len(stable_rows) >= 4:
        stat_rows = stable_rows
        measurement_scope = "低反射稳定窗口"
    else:
        stat_rows = rows
        measurement_scope = "低反射候选帧（稳定窗口样本不足时补充）"
    used_ids = {id(r) for r in stat_rows}
    for r in rows:
        r["used_for_summary"] = int(id(r) in used_ids)
    spacings = np.asarray([r["spacing_cm"] for r in stat_rows], dtype=float)
    if spacings.size:
        mean = float(np.mean(spacings))
        median = float(np.median(spacings))
        std = float(np.std(spacings, ddof=1)) if spacings.size > 1 else 0.0
        p25 = float(np.percentile(spacings, 25))
        p75 = float(np.percentile(spacings, 75))
    else:
        mean = median = std = p25 = p75 = float("nan")
    selected = None
    if stat_rows and np.isfinite(median):
        best_row = min(stat_rows, key=lambda r: abs(r["spacing_cm"] - median))
        frame_id = int(best_row["frame"])
        profile = smoothed_profile(frame_id)
        peaks, _ = find_peaks(
            profile[margin_px : n_x - margin_px],
            distance=max(20, min_px),
            prominence=max(float(np.std(profile) * 0.28), 0.015),
        )
        selected = {"frame": frame_id, "profile": profile, "peaks": peaks + margin_px, "row": best_row}
    note = "优先使用低反射稳定窗口内峰距；若稳定窗口样本不足，则补充同一视频内反射较低且入射能量足够的帧。"
    return {
        "rows": rows,
        "mean_cm": mean,
        "median_cm": median,
        "std_cm": std,
        "p25_cm": p25,
        "p75_cm": p75,
        "n": int(spacings.size),
        "total_candidate_n": int(len(rows)),
        "stable_window_n": stable_count,
        "measurement_scope": measurement_scope,
        "selected": selected,
        "note": note,
    }


def classify_result(
    direct: dict[str, object],
    incident_profile: dict[str, object],
    stable: dict[str, object],
) -> tuple[str, str, float, float]:
    direct_lambda = float(direct["median_cm"])
    inc_lambda = float(incident_profile["median_cm"])
    if np.isfinite(direct_lambda) and np.isfinite(inc_lambda) and inc_lambda > 0:
        diff_cm = abs(direct_lambda - inc_lambda)
        diff_percent = 100.0 * diff_cm / inc_lambda
    else:
        diff_cm = float("nan")
        diff_percent = float("nan")
    ratio = float(stable["median_reflection_ratio"])
    if (np.isfinite(diff_percent) and diff_percent >= 10.0) or ratio >= 0.18:
        judgement = "需要考虑驻波/反射"
        recommendation = "反射或分离前后峰距差异已经足以改变主波长，应优先报告方向分离后的入射分量，并把直接峰距作为含反射扰动的表观值。"
    elif (np.isfinite(diff_percent) and diff_percent >= 5.0) or ratio >= 0.07:
        judgement = "反射影响中等，建议纳入不确定度"
        recommendation = "可报告低反射窗口的直接峰距，但需同时列出入射分量峰距，并把两者差异计入波长不确定度。"
    else:
        judgement = "低反射窗口内驻波/反射影响较小"
        recommendation = "主波长可优先采用低反射窗口直接峰距，并用方向分离入射剖面作为一致性检查；全帧 2D FFT 仅作方向诊断。"
    return judgement, recommendation, diff_cm, diff_percent


def plot_ruler(path: Path, frames: np.ndarray, ruler: dict[str, object]) -> None:
    avg = np.mean(frames.astype(np.float32), axis=0).astype(np.uint8)
    y1 = int(ruler["ruler_y1_px"])
    y2 = int(ruler["ruler_y2_px"])
    fig, axes = plt.subplots(2, 1, figsize=(12, 5.2), constrained_layout=True)
    crop_y1 = max(0, y1 - 24)
    crop_y2 = min(avg.shape[0], y2 + 30)
    axes[0].imshow(avg[crop_y1:crop_y2])
    axes[0].axhline(y1 - crop_y1, color="red", lw=1.2, label="直尺上沿")
    axes[0].axhline(y2 - crop_y1, color="cyan", lw=1.2, label="直尺下沿")
    for x in ruler["diagnostic_label_centers_px"]:
        axes[0].axvline(x, color="yellow", lw=0.8, alpha=0.7)
    axes[0].set_title(
        f"直尺标定诊断：{ruler['px_per_cm']:.3f} px/cm，"
        f"估计不确定度 {ruler['relative_scale_uncertainty_percent']:.2f}%"
    )
    axes[0].set_axis_off()
    axes[0].legend(loc="upper right")

    estimates = [
        float(r["px_per_cm"])
        for r in ruler["calibration_rows"]
        if str(r["used"]) == "1" and str(r["px_per_cm"]).strip()
    ]
    axes[1].plot(estimates, "o-", ms=3)
    axes[1].axhline(float(ruler["px_per_cm"]), color="red", lw=1, label="采用值")
    axes[1].set_xlabel("多帧/多条毫米刻度估计样本")
    axes[1].set_ylabel("px/cm")
    axes[1].grid(alpha=0.25)
    axes[1].legend()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_surface_check(path: Path, frames: np.ndarray, surface: dict[str, object], stable: dict[str, object]) -> None:
    ids = sorted(
        set(
            [
                0,
                int(surface["baseline_frame_count"]) - 1,
                int(stable["start_frame"]),
                int((stable["start_frame"] + stable["end_frame"]) // 2),
                int(stable["end_frame"]),
                frames.shape[0] - 1,
            ]
        )
    )
    ids = [i for i in ids if 0 <= i < frames.shape[0]]
    n = len(ids)
    fig, axes = plt.subplots(n, 1, figsize=(12, 2.05 * n), constrained_layout=True)
    if n == 1:
        axes = [axes]
    xs = np.arange(frames.shape[2])
    for ax, frame_id in zip(axes, ids):
        ax.imshow(frames[frame_id])
        ax.plot(xs, surface["surface_y_px"][frame_id], color="red", lw=1.1, label="提取水线")
        ax.axhline(surface["surface_search_y1"], color="yellow", lw=0.6, alpha=0.75)
        ax.axhline(surface["surface_search_y2"], color="yellow", lw=0.6, alpha=0.75)
        ax.set_title(f"水线检查：frame {frame_id}, t={frame_id / 30.0:.2f}s")
        ax.set_axis_off()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_xt_panels(
    path: Path,
    x_cm: np.ndarray,
    time_s: np.ndarray,
    eta_raw: np.ndarray,
    eta_inc: np.ndarray,
    eta_ref: np.ndarray,
    stable: dict[str, object],
) -> None:
    vmax = float(np.percentile(np.abs(eta_raw), 98))
    vmax = max(vmax, 0.05)
    panels = [
        ("原始 eta(x,t) 去均值", eta_raw),
        ("方向分离：入射分量", eta_inc),
        ("方向分离：反射分量", eta_ref),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True, constrained_layout=True)
    for ax, (title, arr) in zip(axes, panels):
        im = ax.imshow(
            arr,
            origin="lower",
            aspect="auto",
            extent=[x_cm[0], x_cm[-1], time_s[0], time_s[-1]],
            cmap="RdBu_r",
            vmin=-vmax,
            vmax=vmax,
        )
        ax.axhspan(stable["start_time_s"], stable["end_time_s"], color="gold", alpha=0.14)
        ax.set_ylabel("t (s)")
        ax.set_title(title)
        fig.colorbar(im, ax=ax, label="eta (cm)", shrink=0.85)
    axes[-1].set_xlabel("x (cm)")
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_reflection(path: Path, time_s: np.ndarray, sep: dict[str, object], stable: dict[str, object]) -> None:
    ratio = np.asarray(sep["reflection_ratio_t"], dtype=float)
    inc = np.asarray(sep["incident_energy_t"], dtype=float)
    ref = np.asarray(sep["reflected_energy_t"], dtype=float)
    fig, axes = plt.subplots(2, 1, figsize=(10.5, 6.2), sharex=True, constrained_layout=True)
    axes[0].plot(time_s, ratio, color="#185abd", lw=1.8)
    axes[0].axhspan(0, stable["median_reflection_ratio"], color="#185abd", alpha=0.08)
    axes[0].axvspan(stable["start_time_s"], stable["end_time_s"], color="gold", alpha=0.25)
    axes[0].set_ylabel("反射/入射能量比")
    axes[0].set_title(
        f"反射强度：稳定窗口中位数 {stable['median_reflection_ratio']:.4f}"
    )
    axes[0].grid(alpha=0.25)
    axes[1].plot(time_s, inc, color="#117a65", lw=1.5, label="入射能量")
    axes[1].plot(time_s, ref, color="#a93226", lw=1.5, label="反射能量")
    axes[1].axvspan(stable["start_time_s"], stable["end_time_s"], color="gold", alpha=0.25)
    axes[1].set_xlabel("t (s)")
    axes[1].set_ylabel("空间均方能量 (cm²)")
    axes[1].grid(alpha=0.25)
    axes[1].legend()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_peak_measurement(
    path: Path,
    frames: np.ndarray,
    surface: dict[str, object],
    x_cm: np.ndarray,
    direct: dict[str, object],
    incident: dict[str, object],
    px_per_cm: float,
) -> None:
    selected = direct["selected"] or incident["selected"]
    frame_id = int(selected["frame"]) if selected else int(frames.shape[0] // 2)
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(12, 8.4),
        gridspec_kw={"height_ratios": [1.0, 1.18]},
        constrained_layout=True,
    )
    axes[0].imshow(frames[frame_id])
    axes[0].plot(np.arange(frames.shape[2]), surface["surface_y_px"][frame_id], color="red", lw=1.2)
    axes[0].set_title(f"峰距测量代表帧：frame {frame_id}, t={frame_id / 30.0:.2f}s")
    axes[0].set_axis_off()

    notes = []
    if direct["selected"] is not None:
        dprof = direct["selected"]["profile"]
        axes[1].plot(x_cm, dprof, color="#1f618d", lw=1.5, label="未分离直接剖面")
        row = direct["selected"]["row"]
        axes[1].scatter([row["x1_cm"], row["x2_cm"]], [row["eta1_cm"], row["eta2_cm"]], color="#1f618d")
        axes[1].axvline(row["x1_cm"], color="#1f618d", lw=0.9, alpha=0.45)
        axes[1].axvline(row["x2_cm"], color="#1f618d", lw=0.9, alpha=0.45)
        notes.append(f"直接峰距 {row['spacing_cm']:.2f} cm")
    if incident["selected"] is not None:
        iprof = incident["selected"]["profile"]
        axes[1].plot(x_cm, iprof, color="#b03a2e", lw=1.5, label="分离后入射剖面")
        row = incident["selected"]["row"]
        axes[1].scatter([row["x1_cm"], row["x2_cm"]], [row["eta1_cm"], row["eta2_cm"]], color="#b03a2e")
        axes[1].axvline(row["x1_cm"], color="#b03a2e", lw=0.9, alpha=0.38, linestyle="--")
        axes[1].axvline(row["x2_cm"], color="#b03a2e", lw=0.9, alpha=0.38, linestyle="--")
        notes.append(f"入射剖面峰距 {row['spacing_cm']:.2f} cm")
    if notes:
        axes[1].text(
            0.015,
            0.96,
            "；".join(notes),
            transform=axes[1].transAxes,
            ha="left",
            va="top",
            fontsize=11,
            bbox={"boxstyle": "round,pad=0.32", "facecolor": "white", "edgecolor": "#d0d3d4", "alpha": 0.92},
        )
    axes[1].set_xlabel("x (cm)")
    axes[1].set_ylabel("eta (cm)")
    axes[1].set_xlim(x_cm[0], x_cm[-1])
    axes[1].grid(alpha=0.25)
    axes[1].legend()
    axes[1].set_title(f"剖面峰距标注（像素标定：{px_per_cm:.3f} px/cm）", pad=14)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def plot_judgement(
    path: Path,
    direct: dict[str, object],
    incident: dict[str, object],
    sep: dict[str, object],
    stable: dict[str, object],
    judgement: str,
    diff_percent: float,
) -> None:
    fft_lambda = float(sep["fft_diagnostic"]["lambda_cm"])
    labels = ["直接峰距", "入射剖面峰距", "2D FFT诊断"]
    values = [float(direct["median_cm"]), float(incident["median_cm"]), fft_lambda]
    errors = [
        float(direct["std_cm"]) if np.isfinite(float(direct["std_cm"])) else 0.0,
        float(incident["std_cm"]) if np.isfinite(float(incident["std_cm"])) else 0.0,
        0.0,
    ]
    colors = ["#1f618d", "#b03a2e", "#7d3c98"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)
    axes[0].bar(labels, values, yerr=errors, color=colors, alpha=0.88, capsize=4)
    axes[0].set_ylabel("波长/峰距 (cm)")
    axes[0].set_title("直接峰距 vs 分离后入射波长")
    axes[0].grid(axis="y", alpha=0.25)
    text = (
        f"{judgement}\n"
        f"稳定窗口反射/入射能量比中位数：{stable['median_reflection_ratio']:.4f}\n"
        f"直接-入射剖面相对差异：{diff_percent:.2f}%\n"
        f"FFT 波长：{fft_lambda:.2f} cm（诊断值）"
    )
    axes[1].axis("off")
    axes[1].text(
        0.02,
        0.95,
        text,
        va="top",
        ha="left",
        fontsize=12,
        bbox={"boxstyle": "round,pad=0.45", "facecolor": "#f8f9f9", "edgecolor": "#d5d8dc"},
    )
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_eta_csv(path: Path, time_s: np.ndarray, x_cm: np.ndarray, eta_cm: np.ndarray) -> None:
    header = ["frame", "time_s"] + [f"x_{x:.3f}_cm" for x in x_cm]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for i, t in enumerate(time_s):
            writer.writerow([i, f"{t:.6f}"] + [f"{v:.7f}" for v in eta_cm[i]])


def write_report(
    path: Path,
    meta: dict[str, object],
    ruler: dict[str, object],
    surface: dict[str, object],
    sep: dict[str, object],
    stable: dict[str, object],
    direct: dict[str, object],
    incident: dict[str, object],
    judgement: str,
    recommendation: str,
    diff_cm: float,
    diff_percent: float,
) -> None:
    fft_diag = sep["fft_diagnostic"]
    label_scale = ruler["diagnostic_label_px_per_cm"]
    if np.isfinite(label_scale):
        label_note = f"标签中心给出的表观比例约 {label_scale:.3f} px/cm。"
    else:
        label_note = "标签中心样本不足，未形成独立比例值。"
    lines = [
        "# 数据组 12 水波视频驻波/反射分析报告",
        "",
        "## 结论",
        "",
        f"- 判断：**{judgement}**。",
        f"- 建议：{recommendation}",
        f"- 低反射稳定窗口：frame {stable['start_frame']}--{stable['end_frame']}，"
        f"t={stable['start_time_s']:.3f}--{stable['end_time_s']:.3f} s；"
        f"反射/入射能量比中位数 {stable['median_reflection_ratio']:.4f}"
        f"（四分位 {stable['p25_reflection_ratio']:.4f}--{stable['p75_reflection_ratio']:.4f}）。",
        f"- 直接峰距（未分离，统计范围：{direct['measurement_scope']}）：{direct['median_cm']:.3f} cm"
        f"（均值 {direct['mean_cm']:.3f} cm，用于汇总 n={direct['n']}，候选总 n={direct['total_candidate_n']}，"
        f"稳定窗口内 n={direct['stable_window_n']}，"
        f"std={direct['std_cm']:.3f} cm）。",
        f"- 分离后入射剖面峰距（统计范围：{incident['measurement_scope']}）：{incident['median_cm']:.3f} cm"
        f"（均值 {incident['mean_cm']:.3f} cm，用于汇总 n={incident['n']}，候选总 n={incident['total_candidate_n']}，"
        f"稳定窗口内 n={incident['stable_window_n']}，"
        f"std={incident['std_cm']:.3f} cm）。",
        f"- 直接峰距与入射剖面峰距差异：{diff_cm:.3f} cm，{diff_percent:.2f}%。",
        f"- 全帧 2D FFT 入射分支主峰波长：{fft_diag['lambda_cm']:.3f} cm；本视频仅 5.83 s、横向视场约"
        f" {meta['width'] / ruler['px_per_cm']:.2f} cm，完整可见周期少，因此该 FFT 值标为诊断值，不作为最终高精度波长。",
        "",
        "## 视频与逐帧读取",
        "",
        f"- 输入视频：`{meta['video']}`。",
        f"- 解码器：{meta['decoder']}；codec={meta['codec']}。",
        f"- 逐帧读取完整视频：{meta['frame_count']} 帧，fps={meta['fps']:.3f}，"
        f"分辨率 {meta['width']}x{meta['height']}，时长 {meta['duration_s']:.3f} s。",
        f"- 路径说明：{meta['note']}",
        "",
        "## 直尺标定",
        "",
        f"- 标定依据：{ruler['basis']}",
        f"- 自动定位直尺带：y={ruler['ruler_y1_px']}--{ruler['ruler_y2_px']} px。",
        f"- 采用比例：{ruler['px_per_cm']:.6f} px/cm，即 {ruler['cm_per_px']:.7f} cm/px。",
        f"- 多帧刻度估计样本数：{ruler['sample_count']}；尺度离散度约 ±{ruler['px_per_cm_std']:.4f} px/cm"
        f"（约 ±{ruler['relative_scale_uncertainty_percent']:.2f}%）。",
        f"- 十厘米数字标签辅助检查中心：{json.dumps(ruler['diagnostic_label_centers_px'], ensure_ascii=False)}；"
        f"{label_note}该项受数字宽度、透视和标签中心偏移影响，只用于检查，不替代毫米刻度。",
        "",
        "## 方法摘要",
        "",
        f"- 水面轮廓：在 y={surface['surface_search_y1']}--{surface['surface_search_y2']} px 搜索绿色通道向下亮度突变的最大垂直梯度，"
        "逐列得到 waterline，再做中值去异常、Savitzky-Golay 空间平滑。",
        f"- eta(x,t)：以前 {surface['baseline_frame_count']} 帧中位水线作为静水基线，"
        "正值表示水面上抬，并逐帧去掉整体平移。",
        f"- 方向分离：对 eta(x,t) 做 2D FFT，保留 {sep['band_f_min_hz']:.3f}--{sep['band_f_max_hz']:.3f} Hz、"
        f"{sep['band_k_min_cyc_cm']:.4f}--{sep['band_k_max_cyc_cm']:.4f} cycles/cm 波动频带，按 k-f 象限分离双向行波；"
        f"能量较强分支定义为入射波，方向为 {sep['incident_direction']}（{sep['incident_branch']}）。",
        "- 反射强度：分离后分别计算入射/反射场的空间均方能量，并用约 0.3 s 的平滑得到反射/入射能量比时序。",
        "- 峰距：优先在低反射稳定窗口内测未分离直接剖面和入射剖面相邻主峰间距；若样本不足，再补充同一视频中反射较低且入射能量足够的帧。",
        "",
        "## 局限与注意事项",
        "",
        "- 视频较短，且视场宽度不足两倍主波长；x-t 全帧 2D FFT 的空间频率分辨率有限，容易落在视场基频或谐波附近。",
        "- 后段波形更强但同时更容易混入边界反射；最终判断优先使用低反射窗口直接峰距和分离后入射剖面峰距，而不是把全帧 FFT 主峰当作高精度波长。",
        "- 直尺可见且已用于标定；没有启用非直尺替代标定。",
        "",
        "## 输出文件",
        "",
        "- `standing_wave_summary_cn.csv`：中文汇总指标。",
        "- `standing_wave_cn_report.md`：本报告。",
        "- `standing_wave_judgement_cn.png`：反射/驻波判断图。",
        "- `wave_peak_measurement.png`：直接峰距与入射剖面峰距标注图。",
        "- `xt_raw_incident_reflected_panels.png`：原始、入射、反射 x-t 三联图。",
        "- `reflection_strength.png`：反射强度随时间变化。",
        "- `ruler_calibration_diagnostic.png`：直尺标定诊断图。",
        "- `surface_detection_check.png`：surface/waterline 检查图。",
        "- `standing_wave_analysis_data.npz`：核心矩阵和参数。",
        "- `eta_xt_surface_cm.csv`：完整 eta(x,t) 宽表。",
        "- `reflection_time_series.csv`：反射/入射能量比时间序列。",
        "- `peak_measurements.csv`：直接峰距和入射剖面峰距逐样本。",
        "- `ruler_calibration.csv`：直尺标定逐样本。",
        "- `directional_fft_summary.csv`：方向分离和 FFT 诊断摘要。",
        "- `analyze_standing_wave_group12.py`：分析脚本。",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    configure_chinese_font()
    frames, meta = read_video()
    ruler = calibrate_ruler(frames)
    surface = extract_surface(frames, ruler)
    fps = float(meta["fps"])
    px_per_cm = float(ruler["px_per_cm"])
    time_s = np.arange(int(meta["frame_count"]), dtype=float) / fps
    x_cm = np.arange(int(meta["width"]), dtype=float) / px_per_cm

    sep = directional_separation(surface["eta_cm"], fps, px_per_cm)
    stable = choose_stable_window(sep, fps)
    fft_lambda = float(sep["fft_diagnostic"]["lambda_cm"])
    direct = peak_measurements_for_field(
        surface["eta_cm"],
        fps,
        px_per_cm,
        stable,
        np.asarray(sep["reflection_ratio_t"], dtype=float),
        np.asarray(sep["incident_energy_t"], dtype=float),
        "直接未分离峰距",
        expected_lambda_cm=fft_lambda if np.isfinite(fft_lambda) else None,
    )
    incident = peak_measurements_for_field(
        np.asarray(sep["eta_incident_cm"], dtype=float),
        fps,
        px_per_cm,
        stable,
        np.asarray(sep["reflection_ratio_t"], dtype=float),
        np.asarray(sep["incident_energy_t"], dtype=float),
        "分离后入射剖面峰距",
        expected_lambda_cm=float(direct["median_cm"]) if np.isfinite(float(direct["median_cm"])) else fft_lambda,
    )
    judgement, recommendation, diff_cm, diff_percent = classify_result(direct, incident, stable)

    plot_ruler(BASE_DIR / "ruler_calibration_diagnostic.png", frames, ruler)
    plot_surface_check(BASE_DIR / "surface_detection_check.png", frames, surface, stable)
    plot_xt_panels(
        BASE_DIR / "xt_raw_incident_reflected_panels.png",
        x_cm,
        time_s,
        np.asarray(sep["eta_for_fft_cm"], dtype=float),
        np.asarray(sep["eta_incident_cm"], dtype=float),
        np.asarray(sep["eta_reflected_cm"], dtype=float),
        stable,
    )
    plot_reflection(BASE_DIR / "reflection_strength.png", time_s, sep, stable)
    plot_peak_measurement(
        BASE_DIR / "wave_peak_measurement.png",
        frames,
        surface,
        x_cm,
        direct,
        incident,
        px_per_cm,
    )
    plot_judgement(BASE_DIR / "standing_wave_judgement_cn.png", direct, incident, sep, stable, judgement, diff_percent)

    summary_rows = [
        {
            "数据组": "12",
            "视频": VIDEO_NAME,
            "帧数": meta["frame_count"],
            "fps": f"{fps:.6f}",
            "时长_s": f"{meta['duration_s']:.6f}",
            "px_per_cm": f"{px_per_cm:.6f}",
            "px_per_cm_std": f"{ruler['px_per_cm_std']:.6f}",
            "cm_per_px": f"{ruler['cm_per_px']:.8f}",
            "入射方向": sep["incident_direction"],
            "全局FFT反射入射能量比": f"{sep['global_reflection_ratio_fft']:.8f}",
            "稳定窗口_start_frame": stable["start_frame"],
            "稳定窗口_end_frame": stable["end_frame"],
            "稳定窗口_start_s": f"{stable['start_time_s']:.6f}",
            "稳定窗口_end_s": f"{stable['end_time_s']:.6f}",
            "稳定窗口反射入射能量比中位数": f"{stable['median_reflection_ratio']:.8f}",
            "直接峰距_median_cm": f"{direct['median_cm']:.6f}",
            "直接峰距_mean_cm": f"{direct['mean_cm']:.6f}",
            "直接峰距_std_cm": f"{direct['std_cm']:.6f}",
            "直接峰距_n": direct["n"],
            "直接峰距_候选总_n": direct["total_candidate_n"],
            "直接峰距_稳定窗口_n": direct["stable_window_n"],
            "直接峰距_统计范围": direct["measurement_scope"],
            "入射剖面峰距_median_cm": f"{incident['median_cm']:.6f}",
            "入射剖面峰距_mean_cm": f"{incident['mean_cm']:.6f}",
            "入射剖面峰距_std_cm": f"{incident['std_cm']:.6f}",
            "入射剖面峰距_n": incident["n"],
            "入射剖面峰距_候选总_n": incident["total_candidate_n"],
            "入射剖面峰距_稳定窗口_n": incident["stable_window_n"],
            "入射剖面峰距_统计范围": incident["measurement_scope"],
            "FFT诊断波长_cm": f"{sep['fft_diagnostic']['lambda_cm']:.6f}",
            "FFT诊断频率_Hz": f"{sep['fft_diagnostic']['frequency_hz']:.6f}",
            "直接_入射差异_cm": f"{diff_cm:.6f}",
            "直接_入射相对差异_percent": f"{diff_percent:.6f}",
            "判断": judgement,
            "建议": recommendation,
        }
    ]
    save_csv(BASE_DIR / "standing_wave_summary_cn.csv", summary_rows, list(summary_rows[0].keys()))

    refl_rows = []
    for i, t in enumerate(time_s):
        refl_rows.append(
            {
                "frame": int(i),
                "time_s": f"{t:.6f}",
                "incident_energy_cm2": f"{float(sep['incident_energy_t'][i]):.10f}",
                "reflected_energy_cm2": f"{float(sep['reflected_energy_t'][i]):.10f}",
                "reflection_incident_energy_ratio": f"{float(sep['reflection_ratio_t'][i]):.10f}",
                "in_stable_window": int(stable["start_frame"] <= i <= stable["end_frame"]),
            }
        )
    save_csv(BASE_DIR / "reflection_time_series.csv", refl_rows, list(refl_rows[0].keys()))

    peak_rows = []
    for row in direct["rows"] + incident["rows"]:
        peak_rows.append(
            {
                "kind": row["kind"],
                "frame": row["frame"],
                "time_s": f"{row['time_s']:.6f}",
                "x1_px": f"{row['x1_px']:.6f}",
                "x2_px": f"{row['x2_px']:.6f}",
                "x1_cm": f"{row['x1_cm']:.6f}",
                "x2_cm": f"{row['x2_cm']:.6f}",
                "spacing_cm": f"{row['spacing_cm']:.6f}",
                "eta1_cm": f"{row['eta1_cm']:.6f}",
                "eta2_cm": f"{row['eta2_cm']:.6f}",
                "from_stable_window": row["from_stable_window"],
                "used_for_summary": row["used_for_summary"],
            }
        )
    save_csv(
        BASE_DIR / "peak_measurements.csv",
        peak_rows,
        [
            "kind",
            "frame",
            "time_s",
            "x1_px",
            "x2_px",
            "x1_cm",
            "x2_cm",
            "spacing_cm",
            "eta1_cm",
            "eta2_cm",
            "from_stable_window",
            "used_for_summary",
        ],
    )

    save_csv(
        BASE_DIR / "ruler_calibration.csv",
        ruler["calibration_rows"],
        ["frame", "ruler_y1_px", "ruler_y2_px", "strip", "period_px", "px_per_cm", "strength", "used"],
    )
    directional_rows = [
        {
            "metric": "incident_direction",
            "value": sep["incident_direction"],
            "unit": "",
            "note": sep["incident_branch"],
        },
        {
            "metric": "global_reflection_ratio_fft",
            "value": f"{sep['global_reflection_ratio_fft']:.10f}",
            "unit": "energy ratio",
            "note": "全局方向分支能量比，仅作方向分离诊断",
        },
        {
            "metric": "fft_diagnostic_lambda",
            "value": f"{sep['fft_diagnostic']['lambda_cm']:.10f}",
            "unit": "cm",
            "note": sep["fft_diagnostic"]["note"],
        },
        {
            "metric": "fft_diagnostic_frequency",
            "value": f"{sep['fft_diagnostic']['frequency_hz']:.10f}",
            "unit": "Hz",
            "note": "入射分支主峰频率",
        },
        {
            "metric": "stable_window_reflection_ratio_median",
            "value": f"{stable['median_reflection_ratio']:.10f}",
            "unit": "energy ratio",
            "note": stable["selection_note"],
        },
    ]
    save_csv(BASE_DIR / "directional_fft_summary.csv", directional_rows, ["metric", "value", "unit", "note"])

    save_eta_csv(BASE_DIR / "eta_xt_surface_cm.csv", time_s, x_cm, surface["eta_cm"])
    np.savez_compressed(
        BASE_DIR / "standing_wave_analysis_data.npz",
        video_name=VIDEO_NAME,
        fps=fps,
        time_s=time_s,
        x_cm=x_cm,
        px_per_cm=px_per_cm,
        px_per_cm_std=float(ruler["px_per_cm_std"]),
        surface_y_px=surface["surface_y_px"],
        baseline_y_px=surface["baseline_y_px"],
        eta_cm=surface["eta_cm"],
        eta_for_fft_cm=sep["eta_for_fft_cm"],
        eta_incident_cm=sep["eta_incident_cm"],
        eta_reflected_cm=sep["eta_reflected_cm"],
        incident_energy_t=sep["incident_energy_t"],
        reflected_energy_t=sep["reflected_energy_t"],
        reflection_ratio_t=sep["reflection_ratio_t"],
        stable_window_start_frame=int(stable["start_frame"]),
        stable_window_end_frame=int(stable["end_frame"]),
        direct_peak_spacing_median_cm=float(direct["median_cm"]),
        incident_profile_spacing_median_cm=float(incident["median_cm"]),
        fft_diagnostic_lambda_cm=float(sep["fft_diagnostic"]["lambda_cm"]),
        direct_incident_difference_percent=float(diff_percent),
    )

    write_report(
        BASE_DIR / "standing_wave_cn_report.md",
        meta,
        ruler,
        surface,
        sep,
        stable,
        direct,
        incident,
        judgement,
        recommendation,
        diff_cm,
        diff_percent,
    )

    for cache_file in BASE_DIR.glob("fontlist-v*.json"):
        try:
            cache_file.unlink()
        except OSError:
            pass

    print(
        json.dumps(
            {
                "video": VIDEO_NAME,
                "frames": meta["frame_count"],
                "fps": fps,
                "px_per_cm": px_per_cm,
                "stable_window": {
                    "start_frame": stable["start_frame"],
                    "end_frame": stable["end_frame"],
                    "start_s": stable["start_time_s"],
                    "end_s": stable["end_time_s"],
                    "reflection_ratio_median": stable["median_reflection_ratio"],
                },
                "direct_peak_spacing_median_cm": direct["median_cm"],
                "incident_profile_spacing_median_cm": incident["median_cm"],
                "fft_diagnostic_lambda_cm": sep["fft_diagnostic"]["lambda_cm"],
                "difference_percent": diff_percent,
                "judgement": judgement,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

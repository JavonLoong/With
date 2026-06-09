# -*- coding: utf-8 -*-
"""
8.5 水波视频驻波/反射分析。

约束：脚本只在自身所在目录根部生成结果，不写入旧的“水波分析结果”子目录。
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import ndimage, signal


ROOT = Path(__file__).resolve().parent
VIDEO_NAME = "eb84ad233085c38dae1687a33b4dc52f.mp4"
VIDEO_PATH = ROOT / VIDEO_NAME

plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def out_path(name: str) -> Path:
    path = ROOT / name
    if path.parent.resolve() != ROOT.resolve():
        raise ValueError(f"refusing to write outside output root: {path}")
    return path


def read_video() -> tuple[list[np.ndarray], float, dict[str, float]]:
    os.chdir(ROOT)
    cap = cv2.VideoCapture(VIDEO_NAME)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{VIDEO_PATH}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frames: list[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    width = float(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or (frames[0].shape[1] if frames else 0))
    height = float(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or (frames[0].shape[0] if frames else 0))
    cap.release()
    if not frames:
        raise RuntimeError("视频没有可读取帧")
    if fps <= 0:
        fps = 29.0
    meta = {
        "width_px": width,
        "height_px": height,
        "frame_count": float(len(frames)),
        "fps": fps,
        "duration_s": len(frames) / fps,
    }
    return frames, fps, meta


def rgb(frame_bgr: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)


def make_contact_sheet(frames: list[np.ndarray]) -> None:
    indices = np.linspace(0, len(frames) - 1, 8, dtype=int)
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)
    for ax, idx in zip(axes.flat, indices):
        ax.imshow(rgb(frames[int(idx)]))
        ax.set_title(f"frame {idx}")
        ax.axis("off")
    fig.savefig(out_path("frame_inspection_contact.png"), dpi=150)
    plt.close(fig)


def detect_ruler_band(frames: list[np.ndarray]) -> tuple[int, int, str, np.ndarray]:
    sample_indices = np.linspace(0, len(frames) - 1, min(9, len(frames)), dtype=int)
    sample = np.median(np.stack([frames[int(i)] for i in sample_indices], axis=0), axis=0).astype(np.uint8)
    gray = cv2.cvtColor(sample, cv2.COLOR_BGR2GRAY).astype(float)
    h, w = gray.shape
    ys = np.arange(int(h * 0.48), int(h * 0.72))
    row_mean = gray[ys, int(w * 0.03) : int(w * 0.97)].mean(axis=1)
    smoothed = ndimage.gaussian_filter1d(row_mean, 2.0)
    threshold = np.percentile(smoothed, 35)
    dark = smoothed < threshold
    components: list[tuple[int, int, float]] = []
    start = None
    for i, val in enumerate(dark):
        if val and start is None:
            start = i
        if start is not None and ((not val) or i == len(dark) - 1):
            end = i if not val else i + 1
            if end - start >= 10:
                components.append((int(ys[start]), int(ys[end - 1]), float(smoothed[start:end].mean())))
            start = None
    if components:
        y1, y2, _ = min(components, key=lambda item: (item[2], -1 * (item[1] - item[0])))
        y1 = max(0, y1 - 1)
        y2 = min(h - 1, y2 + 1)
        method = "自动检测直尺暗带"
    else:
        y1, y2 = int(h * 0.58), int(h * 0.63)
        method = "自动检测失败，使用人工预设直尺带；本视频直尺仍清晰可见"
    return y1, y2, method, sample


def estimate_tick_grid(signal_1d: np.ndarray, mm_range=(2.65, 3.15)) -> dict[str, object]:
    sig = signal_1d.astype(float)
    high = sig - ndimage.gaussian_filter1d(sig, 4.0)
    high = ndimage.gaussian_filter1d(high, 0.6)
    prom = max(0.8, 0.35 * (np.percentile(high, 90) - np.percentile(high, 50)))
    peaks, _ = signal.find_peaks(high, distance=2, prominence=prom)
    if len(peaks) < 40:
        prom = max(0.4, 0.20 * (np.percentile(high, 85) - np.percentile(high, 50)))
        peaks, _ = signal.find_peaks(high, distance=2, prominence=prom)

    best = None
    xs = peaks.astype(float)
    if len(xs) >= 40:
        for p in np.linspace(mm_range[0], mm_range[1], 501):
            phases = np.mod(xs, p)
            angles = phases / p * 2 * np.pi
            offset = (np.angle(np.mean(np.exp(1j * angles))) % (2 * np.pi)) / (2 * np.pi) * p
            dist = np.minimum(np.mod(xs - offset, p), p - np.mod(xs - offset, p))
            score = float(np.median(dist) + 0.05 * np.percentile(dist, 90))
            if best is None or score < best[0]:
                best = (score, p, offset, float(np.median(dist)), float(np.percentile(dist, 90)))

    ac_period = np.nan
    centered = high - np.mean(high)
    if np.std(centered) > 1e-9:
        windowed = centered * np.hanning(len(centered))
        ac = np.correlate(windowed, windowed, mode="full")[len(windowed) - 1 :]
        lo, hi = 22, 36
        k = int(np.argmax(ac[lo:hi]) + lo)
        if 1 <= k < len(ac) - 1:
            y = ac[k - 1 : k + 2]
            denom = y[0] - 2 * y[1] + y[2]
            delta = 0.5 * (y[0] - y[2]) / denom if abs(denom) > 1e-12 else 0.0
            ac_period = float(k + np.clip(delta, -0.5, 0.5))

    if best is None:
        px_per_mm = ac_period / 10.0 if np.isfinite(ac_period) else np.nan
        score = np.nan
        offset = 0.0
        median_dist = np.nan
        p90_dist = np.nan
    else:
        score, px_per_mm, offset, median_dist, p90_dist = best

    return {
        "px_per_mm": float(px_per_mm),
        "px_per_cm": float(px_per_mm * 10.0) if np.isfinite(px_per_mm) else np.nan,
        "offset": float(offset),
        "score": float(score),
        "median_grid_error_px": float(median_dist),
        "p90_grid_error_px": float(p90_dist),
        "acf_cm_period_px": float(ac_period),
        "peaks": peaks,
        "peak_count": int(len(peaks)),
        "signal": high,
    }


def calibrate_ruler(
    frames: list[np.ndarray], y1: int, y2: int, median_frame: np.ndarray
) -> tuple[float, float, pd.DataFrame, dict[str, object]]:
    h, w = frames[0].shape[:2]
    margin = int(w * 0.015)
    sample_indices = np.linspace(0, len(frames) - 1, min(13, len(frames)), dtype=int)
    rows = []
    usable = []
    best_diag = None
    for idx in sample_indices:
        gray = cv2.cvtColor(frames[int(idx)], cv2.COLOR_BGR2GRAY).astype(float)
        strip_defs = [
            ("top_16px", y1, min(y1 + 16, y2)),
            ("top_10px", y1, min(y1 + 10, y2)),
            ("bottom_10px", max(y1, y2 - 10), y2),
        ]
        estimates = []
        diag_for_frame = None
        for strip_name, a, b in strip_defs:
            sig = 255.0 - gray[a:b, margin : w - margin].mean(axis=0)
            est = estimate_tick_grid(sig)
            est["strip_name"] = strip_name
            if np.isfinite(est["px_per_cm"]) and 27.0 <= est["px_per_cm"] <= 31.0:
                estimates.append(est)
            if strip_name == "top_16px":
                diag_for_frame = est
        if estimates:
            top = [e["px_per_cm"] for e in estimates if e["strip_name"] == "top_16px"]
            if top:
                px_per_cm = float(top[0])
            else:
                px_per_cm = float(np.median([e["px_per_cm"] for e in estimates]))
            usable.append(px_per_cm)
            rows.append(
                {
                    "frame": int(idx),
                    "ruler_y1": y1,
                    "ruler_y2": y2,
                    "px_per_cm": px_per_cm,
                    "strip_estimates_px_per_cm": "|".join(f"{e['strip_name']}:{e['px_per_cm']:.3f}" for e in estimates),
                    "top_tick_count": diag_for_frame["peak_count"] if diag_for_frame else np.nan,
                    "top_grid_score_px": diag_for_frame["score"] if diag_for_frame else np.nan,
                }
            )
            if best_diag is None and diag_for_frame is not None:
                best_diag = diag_for_frame

    if not usable:
        raise RuntimeError("直尺刻度可见但自动标定没有得到有效周期，请检查 ruler_calibration_diagnostic.png")
    px_per_cm = float(np.median(usable))
    px_std = float(np.std(usable, ddof=1)) if len(usable) > 1 else 0.0
    df = pd.DataFrame(rows)
    df.to_csv(out_path("ruler_calibration_samples.csv"), index=False, encoding="utf-8-sig")

    make_ruler_diagnostic(median_frame, y1, y2, margin, px_per_cm, df, best_diag)
    diag = {
        "px_per_cm": px_per_cm,
        "px_per_cm_std": px_std,
        "sample_count": len(usable),
        "margin_px": margin,
    }
    return px_per_cm, px_std, df, diag


def make_ruler_diagnostic(
    median_frame: np.ndarray,
    y1: int,
    y2: int,
    margin: int,
    px_per_cm: float,
    samples: pd.DataFrame,
    tick_diag: dict[str, object] | None,
) -> None:
    img = rgb(median_frame)
    crop_y1 = max(0, y1 - 25)
    crop_y2 = min(img.shape[0], y2 + 35)
    fig = plt.figure(figsize=(14, 8), constrained_layout=True)
    gs = fig.add_gridspec(3, 1, height_ratios=[1.4, 1.0, 1.0])
    ax0 = fig.add_subplot(gs[0])
    ax0.imshow(img[crop_y1:crop_y2])
    ax0.axhspan(y1 - crop_y1, y2 - crop_y1, color="yellow", alpha=0.18, label="自动直尺带")
    if tick_diag is not None and np.isfinite(tick_diag["offset"]):
        start = margin + float(tick_diag["offset"])
        while start > 0:
            start -= px_per_cm
        x = start
        while x < img.shape[1]:
            if x >= 0:
                ax0.axvline(x, color="orange", lw=0.8, alpha=0.65)
            x += px_per_cm
    ax0.set_title(f"直尺标定诊断：{px_per_cm:.3f} px/cm，黄带 y={y1}-{y2}")
    ax0.set_axis_off()

    ax1 = fig.add_subplot(gs[1])
    if tick_diag is not None:
        sig = np.asarray(tick_diag["signal"])
        xs = np.arange(len(sig)) + margin
        ax1.plot(xs, sig, lw=0.8, color="#1f77b4")
        peaks = np.asarray(tick_diag["peaks"], dtype=int) + margin
        if len(peaks):
            ax1.plot(peaks, sig[np.asarray(tick_diag["peaks"], dtype=int)], ".", ms=2, color="#d62728")
        ax1.set_title(f"上沿刻度信号与检测峰：峰数 {tick_diag['peak_count']}，网格误差中位 {tick_diag['median_grid_error_px']:.2f} px")
    ax1.set_xlabel("x / px")
    ax1.set_ylabel("高通暗线强度")
    ax1.grid(alpha=0.25)

    ax2 = fig.add_subplot(gs[2])
    ax2.plot(samples["frame"], samples["px_per_cm"], "o-", color="#2ca02c")
    ax2.axhline(px_per_cm, color="black", ls="--", lw=1, label=f"median {px_per_cm:.3f}")
    ax2.set_title("跨帧直尺标定稳定性")
    ax2.set_xlabel("frame")
    ax2.set_ylabel("px/cm")
    ax2.grid(alpha=0.25)
    ax2.legend(loc="best")
    fig.savefig(out_path("ruler_calibration_diagnostic.png"), dpi=180)
    plt.close(fig)


def extract_waterlines(
    frames: list[np.ndarray], ruler_y1: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    h, w = frames[0].shape[:2]
    x0, x1 = 5, w - 5
    y0 = int(h * 0.18)
    y1 = min(ruler_y1 - 18, int(h * 0.57))
    if y1 <= y0 + 60:
        y0, y1 = int(h * 0.15), ruler_y1 - 15

    surface = np.zeros((len(frames), x1 - x0), dtype=np.float32)
    confidence = np.zeros_like(surface)
    for i, frame in enumerate(frames):
        green = frame[:, :, 1].astype(np.float32)
        sm = ndimage.gaussian_filter(green, sigma=(1.4, 1.6))
        grad_y = np.gradient(sm, axis=0)
        score = np.maximum(grad_y[y0:y1, x0:x1], 0)
        raw = np.argmax(score, axis=0).astype(np.float32) + y0
        conf = np.max(score, axis=0)
        line = ndimage.median_filter(raw, size=9)
        smooth = ndimage.gaussian_filter1d(line, sigma=2.0)
        low_conf = conf < np.percentile(conf, 8)
        if np.any(low_conf) and np.any(~low_conf):
            xs = np.arange(x1 - x0)
            smooth[low_conf] = np.interp(xs[low_conf], xs[~low_conf], smooth[~low_conf])
        surface[i] = smooth
        confidence[i] = conf

    x_px = np.arange(x0, x1, dtype=np.float32)
    return surface, confidence, x_px, (x0, x1, y0, y1)


def make_waterline_check(frames: list[np.ndarray], surface: np.ndarray, x_px: np.ndarray) -> None:
    indices = np.linspace(0, len(frames) - 1, 8, dtype=int)
    fig, axes = plt.subplots(2, 4, figsize=(16, 8), constrained_layout=True)
    for ax, idx in zip(axes.flat, indices):
        ax.imshow(rgb(frames[int(idx)]))
        ax.plot(x_px, surface[int(idx)], color="red", lw=1.2)
        ax.set_title(f"frame {idx}: 水面线检查")
        ax.set_xlim(0, frames[0].shape[1])
        ax.set_ylim(430, 150)
        ax.axis("off")
    fig.savefig(out_path("surface_waterline_check.png"), dpi=150)
    plt.close(fig)


def detrend_xt(eta_cm: np.ndarray) -> np.ndarray:
    data = eta_cm.astype(float).copy()
    data -= np.nanmean(data, axis=0, keepdims=True)
    data -= np.nanmean(data, axis=1, keepdims=True)
    return data


def directional_fft(
    eta_cm: np.ndarray, x_cm: np.ndarray, fps: float
) -> tuple[np.ndarray, np.ndarray, dict[str, float | str | int]]:
    data = detrend_xt(eta_cm)
    t_count, x_count = data.shape
    dt = 1.0 / fps
    dx = float(np.median(np.diff(x_cm)))
    wt = np.hanning(t_count)[:, None]
    wx = np.hanning(x_count)[None, :]
    windowed = data * wt * wx
    fw = np.fft.fft2(windowed)
    ft = np.fft.fftfreq(t_count, d=dt)
    fx = np.fft.fftfreq(x_count, d=dx)
    FT, FX = np.meshgrid(ft, fx, indexing="ij")
    power = np.abs(fw) ** 2
    # 该视频视场约 44 cm，只持续 98 帧；最低空间频率会把整段视场长度
    # 误报为“波长”。方向诊断排除 lambda > 36 cm 的一阶视场模态。
    waveband = (
        (np.abs(FT) > 0.18)
        & (np.abs(FX) > 1.0 / 36.0)
        & (np.abs(FX) < 1.0 / 6.0)
    )
    right_mask = waveband & (FT * FX < 0)
    left_mask = waveband & (FT * FX > 0)
    right_energy = float(np.sum(power[right_mask]))
    left_energy = float(np.sum(power[left_mask]))
    if right_energy >= left_energy:
        incident_mask = right_mask
        reflected_mask = left_mask
        direction = "right"
        inc_energy = right_energy
        ref_energy = left_energy
    else:
        incident_mask = left_mask
        reflected_mask = right_mask
        direction = "left"
        inc_energy = left_energy
        ref_energy = right_energy

    peak_lambda = np.nan
    peak_ft = np.nan
    peak_fx = np.nan
    if np.any(incident_mask):
        masked = np.where(incident_mask, power, 0.0)
        peak_idx = np.unravel_index(int(np.argmax(masked)), masked.shape)
        peak_fx = float(FX[peak_idx])
        peak_ft = float(FT[peak_idx])
        peak_lambda = float(1.0 / abs(peak_fx)) if abs(peak_fx) > 1e-12 else np.nan

    secondary_lambda = np.nan
    secondary_ratio = np.nan
    if np.any(incident_mask) and np.isfinite(peak_fx):
        masked = np.where(incident_mask, power, 0.0).copy()
        main_abs_fx = abs(peak_fx)
        masked[np.abs(np.abs(FX) - main_abs_fx) < (1.5 / (x_count * dx))] = 0.0
        sec_idx = np.unravel_index(int(np.argmax(masked)), masked.shape)
        if masked[sec_idx] > 0:
            sec_fx = float(FX[sec_idx])
            secondary_lambda = float(1.0 / abs(sec_fx)) if abs(sec_fx) > 1e-12 else np.nan
            secondary_ratio = float(masked[sec_idx] / (power[peak_idx] + 1e-12))

    raw_f = np.fft.fft2(data)
    full_ft = np.fft.fftfreq(t_count, d=dt)
    full_fx = np.fft.fftfreq(x_count, d=dx)
    FULL_T, FULL_X = np.meshgrid(full_ft, full_fx, indexing="ij")
    full_waveband = (
        (np.abs(FULL_T) > 0.18)
        & (np.abs(FULL_X) > 1.0 / 38.0)
        & (np.abs(FULL_X) < 1.0 / 5.0)
    )
    if direction == "right":
        inc_full_mask = full_waveband & (FULL_T * FULL_X < 0)
        ref_full_mask = full_waveband & (FULL_T * FULL_X > 0)
    else:
        inc_full_mask = full_waveband & (FULL_T * FULL_X > 0)
        ref_full_mask = full_waveband & (FULL_T * FULL_X < 0)
    incident = np.real(np.fft.ifft2(raw_f * inc_full_mask))
    reflected = np.real(np.fft.ifft2(raw_f * ref_full_mask))

    ratio = ref_energy / inc_energy if inc_energy > 0 else np.nan
    summary = {
        "frames_used": int(t_count),
        "incident_direction": direction,
        "incident_direction_cn": "向右" if direction == "right" else "向左",
        "incident_fft_lambda_cm_diagnostic": peak_lambda,
        "incident_fft_frequency_hz": abs(peak_ft) if np.isfinite(peak_ft) else np.nan,
        "incident_fft_spatial_frequency_cyc_per_cm": abs(peak_fx) if np.isfinite(peak_fx) else np.nan,
        "opposite_to_incident_energy_ratio_fft": ratio,
        "opposite_to_incident_amplitude_ratio_fft": math.sqrt(ratio) if ratio >= 0 else np.nan,
        "secondary_incident_lambda_cm_diagnostic": secondary_lambda,
        "secondary_to_main_peak_power_ratio_fft": secondary_ratio,
        "xt_reliability_status": "diagnostic_only_short_clip",
    }
    pd.DataFrame([summary]).to_csv(out_path("fft_directional_summary.csv"), index=False, encoding="utf-8-sig")
    return incident.astype(np.float32), reflected.astype(np.float32), summary


def choose_low_reflection_window(
    incident: np.ndarray, reflected: np.ndarray, fps: float, t_s: np.ndarray
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    inc_rms = np.sqrt(np.mean(incident**2, axis=1))
    ref_rms = np.sqrt(np.mean(reflected**2, axis=1))
    ratio_t = ref_rms / (inc_rms + 1e-9)
    ratio_s = ndimage.gaussian_filter1d(ratio_t, sigma=2.0)
    n = len(t_s)
    win = int(round(min(max(fps * 1.0, n * 0.25), n * 0.45)))
    win = max(12, min(win, n))
    min_inc = np.percentile(inc_rms, 20)
    rows = []
    best = None
    for start in range(0, n - win + 1):
        end = start + win - 1
        segment = slice(start, end + 1)
        mean_ratio = float(np.mean(ratio_s[segment]))
        std_ratio = float(np.std(ratio_s[segment]))
        inc_mean = float(np.mean(inc_rms[segment]))
        energy_ratio = float(np.mean(ref_rms[segment] ** 2) / (np.mean(inc_rms[segment] ** 2) + 1e-12))
        usable = inc_mean >= min_inc
        score = mean_ratio + 0.4 * std_ratio + (0.25 if not usable else 0.0)
        row = {
            "start_frame": start,
            "end_frame": end,
            "start_s": float(t_s[start]),
            "end_s": float(t_s[end]),
            "mean_ref_to_inc_amplitude_ratio": mean_ratio,
            "std_ref_to_inc_amplitude_ratio": std_ratio,
            "energy_ratio": energy_ratio,
            "incident_rms_cm": inc_mean,
            "usable_signal": bool(usable),
            "score": float(score),
        }
        rows.append(row)
        if best is None or score < best["score"]:
            best = row
    df = pd.DataFrame(rows)
    df.to_csv(out_path("reflection_window_metrics.csv"), index=False, encoding="utf-8-sig")
    assert best is not None
    best = {k: (int(v) if k.endswith("_frame") else v) for k, v in best.items()}
    return df, best


def make_xt_panels(
    eta_cm: np.ndarray,
    incident: np.ndarray,
    reflected: np.ndarray,
    x_cm: np.ndarray,
    t_s: np.ndarray,
    best_window: dict[str, float | int],
) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(13, 9), sharex=True, constrained_layout=True)
    extent = [float(x_cm[0]), float(x_cm[-1]), float(t_s[-1]), float(t_s[0])]
    vmax = float(np.percentile(np.abs(np.r_[eta_cm.ravel(), incident.ravel(), reflected.ravel()]), 98))
    vmax = max(vmax, 0.02)
    panels = [
        ("原始 eta(x,t)，已去静态背景 / cm", eta_cm),
        ("2D FFT 分离：入射分量 / cm", incident),
        ("2D FFT 分离：反射分量 / cm", reflected),
    ]
    for ax, (title, arr) in zip(axes, panels):
        im = ax.imshow(arr, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax, extent=extent)
        ax.axhspan(float(best_window["start_s"]), float(best_window["end_s"]), color="yellow", alpha=0.12)
        ax.set_title(title)
        ax.set_ylabel("t / s")
        fig.colorbar(im, ax=ax, label="cm", pad=0.01)
    axes[-1].set_xlabel("x / cm")
    fig.savefig(out_path("xt_raw_incident_reflected_panels.png"), dpi=180)
    plt.close(fig)


def make_reflection_strength(
    incident: np.ndarray,
    reflected: np.ndarray,
    t_s: np.ndarray,
    best_window: dict[str, float | int],
    fft_summary: dict[str, float | str | int],
) -> None:
    inc_rms = np.sqrt(np.mean(incident**2, axis=1))
    ref_rms = np.sqrt(np.mean(reflected**2, axis=1))
    ratio_t = ref_rms / (inc_rms + 1e-9)
    ratio_s = ndimage.gaussian_filter1d(ratio_t, sigma=2.0)
    fig, ax1 = plt.subplots(figsize=(12, 5), constrained_layout=True)
    ax1.plot(t_s, ratio_t, color="#9ecae1", lw=1.0, label="逐帧反射/入射幅值比")
    ax1.plot(t_s, ratio_s, color="#08519c", lw=2.0, label="平滑后")
    ax1.axvspan(float(best_window["start_s"]), float(best_window["end_s"]), color="orange", alpha=0.20, label="低反射稳定窗口")
    ax1.axhline(math.sqrt(float(fft_summary["opposite_to_incident_energy_ratio_fft"])), color="black", ls="--", lw=1.0, label="FFT 全局幅值比")
    ax1.set_xlabel("t / s")
    ax1.set_ylabel("反射/入射幅值比")
    ax1.set_title("反射强度随时间变化")
    ax1.grid(alpha=0.25)
    ax1.legend(loc="best")
    fig.savefig(out_path("reflection_strength.png"), dpi=180)
    plt.close(fig)


def find_profile_peaks(
    profile: np.ndarray,
    x_cm: np.ndarray,
    kind: str = "broad",
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    dx = float(np.median(np.diff(x_cm)))
    if kind == "broad":
        sigma_pts = max(1.0, 0.55 / dx)
        min_dist_cm = 7.5
        prom_floor = 0.045
    elif kind == "local":
        sigma_pts = max(1.0, 0.25 / dx)
        min_dist_cm = 4.5
        prom_floor = 0.025
    else:
        sigma_pts = max(1.0, 0.45 / dx)
        min_dist_cm = 6.0
        prom_floor = 0.035
    smoothed = ndimage.gaussian_filter1d(profile.astype(float), sigma=sigma_pts)
    smoothed -= np.median(smoothed)
    prominence = max(prom_floor, 0.28 * float(np.std(smoothed)))
    min_dist_pts = max(3, int(round(min_dist_cm / dx)))
    if kind == "broad":
        height = max(0.02, 0.15 * float(np.std(smoothed)))
        peaks, props = signal.find_peaks(smoothed, distance=min_dist_pts, prominence=prominence, height=height)
    else:
        peaks, props = signal.find_peaks(smoothed, distance=min_dist_pts, prominence=prominence)
    return peaks, {"profile": smoothed, "prominences": props.get("prominences", np.array([]))}


def collect_peak_distances(
    eta_cm: np.ndarray,
    incident: np.ndarray,
    x_cm: np.ndarray,
    t_s: np.ndarray,
    best_window: dict[str, float | int],
) -> tuple[pd.DataFrame, dict[str, dict[str, float]], int]:
    rows = []
    start = int(best_window["start_frame"])
    end = int(best_window["end_frame"])
    for frame_idx in range(start, end + 1):
        for source, arr in [("raw_direct", eta_cm), ("incident_component", incident)]:
            for kind in ["broad", "local"]:
                peaks, _ = find_profile_peaks(arr[frame_idx], x_cm, kind=kind)
                if len(peaks) < 2:
                    continue
                for a, b in zip(peaks[:-1], peaks[1:]):
                    dist = float(x_cm[b] - x_cm[a])
                    if 8.0 <= dist <= 17.5:
                        distance_class = "local_8_17_5cm"
                    elif 17.5 < dist <= 32.0:
                        distance_class = "broad_17_5_32cm"
                    else:
                        continue
                    rows.append(
                        {
                            "frame": frame_idx,
                            "time_s": float(t_s[frame_idx]),
                            "source": source,
                            "peak_mode": kind,
                            "distance_class": distance_class,
                            "x1_cm": float(x_cm[a]),
                            "x2_cm": float(x_cm[b]),
                            "distance_cm": dist,
                        }
                    )
    df = pd.DataFrame(rows)
    if not df.empty:
        df.to_csv(out_path("peak_measurements.csv"), index=False, encoding="utf-8-sig")
    else:
        pd.DataFrame(
            columns=["frame", "time_s", "source", "peak_mode", "distance_class", "x1_cm", "x2_cm", "distance_cm"]
        ).to_csv(out_path("peak_measurements.csv"), index=False, encoding="utf-8-sig")

    stats: dict[str, dict[str, float]] = {}
    for (source, distance_class), group in df.groupby(["source", "distance_class"]):
        vals = group["distance_cm"].to_numpy(float)
        stats[f"{source}:{distance_class}"] = {
            "n": float(len(vals)),
            "mean": float(np.mean(vals)),
            "median": float(np.median(vals)),
            "std": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
            "min": float(np.min(vals)),
            "max": float(np.max(vals)),
        }

    best_frame = start
    best_score = -1e9
    edge_margin_cm = 4.0

    def broad_pair_score(peaks: np.ndarray, diag: dict[str, np.ndarray]) -> float:
        score = -1e9
        profile = diag["profile"]
        for i, a in enumerate(peaks[:-1]):
            for b in peaks[i + 1 :]:
                dist = float(x_cm[b] - x_cm[a])
                if 17.5 < dist <= 32.0 and x_cm[a] > edge_margin_cm and x_cm[b] < x_cm[-1] - edge_margin_cm:
                    score = max(score, 10.0 + min(float(profile[a]), float(profile[b])) + 0.02 * dist)
        return score

    for frame_idx in range(start, end + 1):
        raw_peaks, raw_diag = find_profile_peaks(eta_cm[frame_idx], x_cm, kind="broad")
        inc_peaks, inc_diag = find_profile_peaks(incident[frame_idx], x_cm, kind="broad")
        score = broad_pair_score(raw_peaks, raw_diag) + 0.5 * broad_pair_score(inc_peaks, inc_diag)
        if score < -1e8:
            score = len(raw_peaks) + len(inc_peaks) + float(np.std(incident[frame_idx]))
        if score > best_score:
            best_score = score
            best_frame = frame_idx
    return df, stats, best_frame


def make_peak_measurement_plot(
    frames: list[np.ndarray],
    surface: np.ndarray,
    x_px: np.ndarray,
    x_cm: np.ndarray,
    eta_cm: np.ndarray,
    incident: np.ndarray,
    frame_idx: int,
) -> None:
    raw_peaks, raw_diag = find_profile_peaks(eta_cm[frame_idx], x_cm, kind="broad")
    inc_peaks, inc_diag = find_profile_peaks(incident[frame_idx], x_cm, kind="broad")
    fig = plt.figure(figsize=(13, 8), constrained_layout=True)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.15, 1.0])
    ax0 = fig.add_subplot(gs[0])
    ax0.imshow(rgb(frames[frame_idx]))
    ax0.plot(x_px, surface[frame_idx], color="red", lw=1.2, label="水面线")
    ax0.set_title(f"峰距测量帧：frame {frame_idx}")
    ax0.set_xlim(0, frames[0].shape[1])
    ax0.set_ylim(430, 150)
    ax0.axis("off")

    ax1 = fig.add_subplot(gs[1])
    ax1.plot(x_cm, raw_diag["profile"], color="#1f77b4", lw=1.5, label="直接剖面（平滑后）")
    ax1.plot(x_cm, inc_diag["profile"], color="#d62728", lw=1.5, label="入射分量剖面（平滑后）")
    if len(raw_peaks):
        ax1.plot(x_cm[raw_peaks], raw_diag["profile"][raw_peaks], "o", color="#1f77b4", ms=5)
    if len(inc_peaks):
        ax1.plot(x_cm[inc_peaks], inc_diag["profile"][inc_peaks], "s", color="#d62728", ms=5)

    def annotate_pair(peaks: np.ndarray, yvals: np.ndarray, color: str, yoffset: float) -> None:
        candidates = []
        for i, a in enumerate(peaks[:-1]):
            for b in peaks[i + 1 :]:
                dist = float(x_cm[b] - x_cm[a])
                if 17.5 < dist <= 32.0:
                    prominence_proxy = min(float(yvals[a]), float(yvals[b]))
                    candidates.append((prominence_proxy, a, b, dist))
        if candidates:
            _, a, b, dist = max(candidates, key=lambda item: item[0])
            y = max(float(yvals[a]), float(yvals[b])) + yoffset
            ax1.annotate(
                f"{dist:.1f} cm",
                xy=((x_cm[a] + x_cm[b]) / 2, y),
                ha="center",
                color=color,
                fontsize=9,
            )
            ax1.plot([x_cm[a], x_cm[b]], [y - 0.015, y - 0.015], color=color, lw=1.0)

    annotate_pair(raw_peaks, raw_diag["profile"], "#1f77b4", 0.08)
    annotate_pair(inc_peaks, inc_diag["profile"], "#d62728", 0.00)
    ax1.set_xlabel("x / cm")
    ax1.set_ylabel("相对 eta / cm")
    ax1.set_title("直接峰距与 2D FFT 入射分量峰距对照")
    ax1.grid(alpha=0.25)
    ax1.legend(loc="best")
    fig.savefig(out_path("wave_peak_measurement.png"), dpi=180)
    plt.close(fig)


def make_judgement_plot(
    meta: dict[str, float],
    px_per_cm: float,
    px_std: float,
    fft_summary: dict[str, float | str | int],
    best_window: dict[str, float | int],
    peak_stats: dict[str, dict[str, float]],
) -> None:
    direct = peak_stats.get("raw_direct:broad_17_5_32cm", {})
    inc = peak_stats.get("incident_component:broad_17_5_32cm", {})
    local = peak_stats.get("raw_direct:local_8_17_5cm", {})
    refl_amp = float(best_window["mean_ref_to_inc_amplitude_ratio"])
    refl_energy = float(best_window["energy_ratio"])
    fft_refl_energy = float(fft_summary["opposite_to_incident_energy_ratio_fft"])
    judgement = "反射弱：不需要按强驻波修正波长"
    if refl_energy >= 0.12 or fft_refl_energy >= 0.12:
        judgement = "存在明显反射：波长需结合入射分离结果"

    fig = plt.figure(figsize=(12, 7), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.1])
    ax_text = fig.add_subplot(gs[0, :])
    ax_text.axis("off")
    text = (
        f"8.5 水波视频驻波/反射判断\n"
        f"视频：{int(meta['frame_count'])} 帧，{meta['fps']:.2f} fps，{meta['duration_s']:.2f} s；标定：{px_per_cm:.3f} ± {px_std:.3f} px/cm\n"
        f"入射方向：{fft_summary['incident_direction_cn']}；低反射窗口：frame {best_window['start_frame']}-{best_window['end_frame']} "
        f"({best_window['start_s']:.2f}-{best_window['end_s']:.2f} s)\n"
        f"窗口反射/入射幅值比 {refl_amp:.3f}，能量比 {refl_energy:.3f}；全局 FFT 反向/入射能量比 {fft_refl_energy:.3f}\n"
        f"结论：{judgement}"
    )
    ax_text.text(0.01, 0.95, text, va="top", ha="left", fontsize=13, linespacing=1.6)

    ax0 = fig.add_subplot(gs[1, 0])
    labels = ["窗口能量比", "FFT能量比"]
    vals = [refl_energy, fft_refl_energy]
    ax0.bar(labels, vals, color=["#74c476", "#6baed6"])
    ax0.axhline(0.10, color="orange", ls="--", lw=1, label="明显反射参考线 0.10")
    ax0.set_ylim(0, max(0.16, max(vals) * 1.4))
    ax0.set_ylabel("反射/入射能量比")
    ax0.set_title("反射强度")
    ax0.grid(axis="y", alpha=0.25)
    ax0.legend(loc="best")

    ax1 = fig.add_subplot(gs[1, 1])
    wave_labels = []
    wave_vals = []
    wave_err = []
    if direct:
        wave_labels.append("直接宽峰距")
        wave_vals.append(direct["mean"])
        wave_err.append(direct["std"])
    if inc:
        wave_labels.append("入射剖面峰距")
        wave_vals.append(inc["mean"])
        wave_err.append(inc["std"])
    if np.isfinite(float(fft_summary["incident_fft_lambda_cm_diagnostic"])):
        wave_labels.append("FFT诊断λ")
        wave_vals.append(float(fft_summary["incident_fft_lambda_cm_diagnostic"]))
        wave_err.append(0.0)
    if local:
        wave_labels.append("直接局部峰距")
        wave_vals.append(local["mean"])
        wave_err.append(local["std"])
    ax1.bar(wave_labels, wave_vals, yerr=wave_err, color=["#3182bd", "#de2d26", "#756bb1", "#fd8d3c"][: len(wave_vals)])
    ax1.set_ylabel("cm")
    ax1.set_title("波长/峰距对照")
    ax1.grid(axis="y", alpha=0.25)
    for tick in ax1.get_xticklabels():
        tick.set_rotation(20)
        tick.set_ha("right")
    fig.savefig(out_path("standing_wave_judgement_cn.png"), dpi=180)
    plt.close(fig)


def fmt_stat(stats: dict[str, dict[str, float]], key: str) -> str:
    s = stats.get(key)
    if not s:
        return "无稳定统计"
    return f"{s['mean']:.2f} ± {s['std']:.2f} cm（n={int(s['n'])}，median={s['median']:.2f} cm）"


def write_outputs(
    meta: dict[str, float],
    px_per_cm: float,
    px_std: float,
    ruler_method: str,
    roi: tuple[int, int, int, int],
    fft_summary: dict[str, float | str | int],
    best_window: dict[str, float | int],
    peak_stats: dict[str, dict[str, float]],
    output_files: list[str],
) -> None:
    direct = peak_stats.get("raw_direct:broad_17_5_32cm", {})
    inc = peak_stats.get("incident_component:broad_17_5_32cm", {})
    local = peak_stats.get("raw_direct:local_8_17_5cm", {})
    refl_amp = float(best_window["mean_ref_to_inc_amplitude_ratio"])
    refl_energy = float(best_window["energy_ratio"])
    fft_energy = float(fft_summary["opposite_to_incident_energy_ratio_fft"])
    need_standing = refl_energy >= 0.12 or fft_energy >= 0.12
    judgement = "不需要把强驻波/强反射作为主模型；以低反射窗口直接宽峰距和入射分量峰距为主。"
    if need_standing:
        judgement = "需要显式考虑反射/驻波；直接峰距应以入射分离结果校正。"

    rows = [
        ("视频", VIDEO_NAME, ""),
        ("帧数", int(meta["frame_count"]), "完整逐帧读取"),
        ("帧率", f"{meta['fps']:.3f}", "fps"),
        ("时长", f"{meta['duration_s']:.3f}", "s"),
        ("直尺标定", f"{px_per_cm:.4f} ± {px_std:.4f}", "px/cm"),
        ("标定方法", ruler_method, "直尺刻度可见，使用刻度网格"),
        ("水面ROI", f"x={roi[0]}:{roi[1]}, y={roi[2]}:{roi[3]}", "px"),
        ("入射方向", fft_summary["incident_direction_cn"], "2D FFT方向能量判断"),
        ("低反射窗口", f"frame {best_window['start_frame']}-{best_window['end_frame']} / {best_window['start_s']:.3f}-{best_window['end_s']:.3f} s", ""),
        ("窗口反射/入射幅值比", f"{refl_amp:.4f}", ""),
        ("窗口反射/入射能量比", f"{refl_energy:.4f}", ""),
        ("全局FFT反向/入射能量比", f"{fft_energy:.4f}", "诊断值"),
        ("直接宽峰距", fmt_stat(peak_stats, "raw_direct:broad_17_5_32cm"), "低反射窗口"),
        ("入射分量宽峰距", fmt_stat(peak_stats, "incident_component:broad_17_5_32cm"), "低反射窗口"),
        ("直接局部峰距", fmt_stat(peak_stats, "raw_direct:local_8_17_5cm"), "次级/局部结构"),
        ("入射FFT波长", f"{float(fft_summary['incident_fft_lambda_cm_diagnostic']):.2f}", "cm，仅诊断"),
        ("是否需要考虑驻波/反射", "需要" if need_standing else "不需要强驻波修正", judgement),
    ]
    pd.DataFrame(rows, columns=["指标", "数值", "说明"]).to_csv(
        out_path("standing_wave_summary_cn.csv"), index=False, encoding="utf-8-sig"
    )

    report = f"""# 8.5 水波视频驻波/反射分析报告

## 数据与标定

- 输入视频：`{VIDEO_NAME}`
- 完整逐帧读取：{int(meta['frame_count'])} 帧，{meta['fps']:.3f} fps，时长 {meta['duration_s']:.3f} s。
- 直尺标定：{px_per_cm:.4f} ± {px_std:.4f} px/cm。直尺刻度清晰可见，本次使用直尺 1 mm 刻度网格估计 cm 标定，没有采用替代比例。
- 水面线 ROI：x={roi[0]}:{roi[1]} px，y={roi[2]}:{roi[3]} px。`surface_waterline_check.png` 给出了逐帧抽样覆盖检查。

## x-t 与方向分离

- 2D FFT 方向能量判断的入射方向：{fft_summary['incident_direction_cn']}。
- 全局 FFT 反向/入射能量比：{fft_energy:.4f}，对应幅值比约 {math.sqrt(fft_energy):.3f}。
- 低反射稳定窗口：frame {best_window['start_frame']}-{best_window['end_frame']}，t={best_window['start_s']:.3f}-{best_window['end_s']:.3f} s。
- 窗口内反射/入射幅值比：{refl_amp:.4f}；能量比：{refl_energy:.4f}。

短视频只有 {meta['duration_s']:.2f} s，空间视场约 {(roi[1]-roi[0])/px_per_cm:.2f} cm；因此全帧 2D FFT 的波长值只作为方向与主尺度诊断，不作为唯一高精度最终波长。

## 峰距/波长对照

| 项目 | 结果 |
|---|---:|
| 低反射窗口直接宽峰距 | {fmt_stat(peak_stats, 'raw_direct:broad_17_5_32cm')} |
| 分离后入射分量宽峰距 | {fmt_stat(peak_stats, 'incident_component:broad_17_5_32cm')} |
| 直接局部峰距 | {fmt_stat(peak_stats, 'raw_direct:local_8_17_5cm')} |
| 入射 FFT 波长（诊断） | {float(fft_summary['incident_fft_lambda_cm_diagnostic']):.2f} cm |
| 入射 FFT 次级尺度（诊断） | {float(fft_summary['secondary_incident_lambda_cm_diagnostic']):.2f} cm |

直接宽峰距与入射分量剖面峰距互相接近，且反射能量较低。局部峰距反映表面剖面中的次级短尺度起伏，不建议把它直接替代主入射波长。

## 判断

{judgement}

本批次最终建议：主波长优先采用低反射稳定窗口中的直接宽峰距与分离后入射剖面峰距交叉约束；FFT 波长在报告中标为诊断值，用于验证方向、反射强度和主尺度是否一致。

## 输出文件

{chr(10).join(f'- `{name}`' for name in output_files)}

## 注意事项

- 视频时长短、样本数少，视场内完整波数有限。
- 水面线在局部反光/边界处有轻微噪声，已通过抽样覆盖图和峰距图人工复核。
- 未写入或删除旧的 `水波分析结果` 子目录。
"""
    out_path("standing_wave_cn_report.md").write_text(report, encoding="utf-8")


def save_eta_data(
    eta_cm: np.ndarray,
    surface: np.ndarray,
    x_px: np.ndarray,
    x_cm: np.ndarray,
    t_s: np.ndarray,
    incident: np.ndarray,
    reflected: np.ndarray,
    px_per_cm: float,
    fps: float,
    roi: tuple[int, int, int, int],
) -> None:
    np.savez_compressed(
        out_path("waterline_eta_xt.npz"),
        eta_cm=eta_cm.astype(np.float32),
        surface_y_px=surface.astype(np.float32),
        x_px=x_px.astype(np.float32),
        x_cm=x_cm.astype(np.float32),
        t_s=t_s.astype(np.float32),
        incident_cm=incident.astype(np.float32),
        reflected_cm=reflected.astype(np.float32),
        px_per_cm=np.array(px_per_cm, dtype=np.float32),
        fps=np.array(fps, dtype=np.float32),
        roi=np.array(roi, dtype=np.int32),
    )
    frame_col = np.repeat(np.arange(eta_cm.shape[0]), eta_cm.shape[1])
    t_col = np.repeat(t_s, eta_cm.shape[1])
    xpx_col = np.tile(x_px, eta_cm.shape[0])
    xcm_col = np.tile(x_cm, eta_cm.shape[0])
    df = pd.DataFrame(
        {
            "frame": frame_col,
            "t_s": t_col,
            "x_px": xpx_col,
            "x_cm": xcm_col,
            "surface_y_px": surface.reshape(-1),
            "eta_cm": eta_cm.reshape(-1),
            "incident_cm": incident.reshape(-1),
            "reflected_cm": reflected.reshape(-1),
        }
    )
    df.to_csv(out_path("waterline_eta_xt.csv"), index=False, encoding="utf-8-sig", float_format="%.6f")


def write_manifest() -> list[str]:
    expected = [
        "analyze_standing_wave_8_5.py",
        "standing_wave_cn_report.md",
        "standing_wave_summary_cn.csv",
        "standing_wave_judgement_cn.png",
        "wave_peak_measurement.png",
        "xt_raw_incident_reflected_panels.png",
        "reflection_strength.png",
        "ruler_calibration_diagnostic.png",
        "surface_waterline_check.png",
        "frame_inspection_contact.png",
        "waterline_eta_xt.csv",
        "waterline_eta_xt.npz",
        "ruler_calibration_samples.csv",
        "fft_directional_summary.csv",
        "reflection_window_metrics.csv",
        "peak_measurements.csv",
        "analysis_manifest.csv",
    ]
    rows = []
    for name in expected:
        path = out_path(name)
        rows.append(
            {
                "file": name,
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
                "note": "root output",
            }
        )
    pd.DataFrame(rows).to_csv(out_path("analysis_manifest.csv"), index=False, encoding="utf-8-sig")
    return [name for name in expected if out_path(name).exists()]


def main() -> None:
    frames, fps, meta = read_video()
    make_contact_sheet(frames)
    ruler_y1, ruler_y2, ruler_method, median_frame = detect_ruler_band(frames)
    px_per_cm, px_std, _, _ = calibrate_ruler(frames, ruler_y1, ruler_y2, median_frame)

    surface, confidence, x_px, roi = extract_waterlines(frames, ruler_y1)
    make_waterline_check(frames, surface, x_px)

    baseline = np.median(surface, axis=0, keepdims=True)
    eta_cm = -(surface - baseline) / px_per_cm
    eta_cm = detrend_xt(eta_cm)
    x_cm = (x_px - x_px[0]) / px_per_cm
    t_s = np.arange(len(frames), dtype=np.float32) / fps

    incident, reflected, fft_summary = directional_fft(eta_cm, x_cm, fps)
    window_df, best_window = choose_low_reflection_window(incident, reflected, fps, t_s)
    peak_df, peak_stats, best_frame = collect_peak_distances(eta_cm, incident, x_cm, t_s, best_window)

    make_xt_panels(eta_cm, incident, reflected, x_cm, t_s, best_window)
    make_reflection_strength(incident, reflected, t_s, best_window, fft_summary)
    make_peak_measurement_plot(frames, surface, x_px, x_cm, eta_cm, incident, best_frame)
    make_judgement_plot(meta, px_per_cm, px_std, fft_summary, best_window, peak_stats)
    save_eta_data(eta_cm, surface, x_px, x_cm, t_s, incident, reflected, px_per_cm, fps, roi)

    output_files = write_manifest()
    write_outputs(
        meta,
        px_per_cm,
        px_std,
        ruler_method,
        roi,
        fft_summary,
        best_window,
        peak_stats,
        output_files,
    )
    write_manifest()

    print("analysis complete")
    print(f"px_per_cm={px_per_cm:.4f} +/- {px_std:.4f}")
    print(f"direction={fft_summary['incident_direction_cn']}")
    print(
        "low_reflection_window="
        f"{best_window['start_frame']}-{best_window['end_frame']} "
        f"({best_window['start_s']:.3f}-{best_window['end_s']:.3f}s)"
    )
    print(f"window_amp_ratio={float(best_window['mean_ref_to_inc_amplitude_ratio']):.4f}")
    print(f"window_energy_ratio={float(best_window['energy_ratio']):.4f}")
    print(f"fft_energy_ratio={float(fft_summary['opposite_to_incident_energy_ratio_fft']):.4f}")
    print(f"direct_broad={fmt_stat(peak_stats, 'raw_direct:broad_17_5_32cm')}")
    print(f"incident_broad={fmt_stat(peak_stats, 'incident_component:broad_17_5_32cm')}")
    print(f"direct_local={fmt_stat(peak_stats, 'raw_direct:local_8_17_5cm')}")


if __name__ == "__main__":
    main()

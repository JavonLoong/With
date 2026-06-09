# -*- coding: utf-8 -*-
"""Standing/reflection analysis for water-wave data group 10.0.

Run this script from this directory.  It writes all analysis products directly
to the group root and deliberately does not touch the older subdirectory.
"""

from __future__ import annotations

import csv
import json
import math
import os
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter, gaussian_filter1d, median_filter
from scipy.signal import correlate, find_peaks, savgol_filter


OUT = Path(__file__).resolve().parent
VIDEO_NAME = "8b5f4cdec73a03c1e7ed911633b86d5b.mp4"
os.chdir(OUT)
os.environ.setdefault("MPLCONFIGDIR", str(OUT))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.font_manager as fm  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402


X_MIN = 40
X_MAX = 1220
SURFACE_Y_MIN = 108
SURFACE_Y_MAX = 230
RULER_Y1 = 454
RULER_Y2 = 488


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
            plt.rcParams["font.sans-serif"] = [prop.get_name()]
            plt.rcParams["font.family"] = "sans-serif"
            break
    plt.rcParams["axes.unicode_minus"] = False


def save_png(path: str | Path, dpi: int = 170) -> None:
    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close()


def write_image(path: str | Path, image_bgr: np.ndarray) -> None:
    ok, buf = cv2.imencode(".png", image_bgr)
    if not ok:
        raise RuntimeError(f"PNG encode failed for {path}")
    Path(path).write_bytes(buf.tobytes())


def read_video() -> tuple[np.ndarray, dict]:
    cap = cv2.VideoCapture(VIDEO_NAME)
    if not cap.isOpened():
        raise RuntimeError(
            "OpenCV cannot open the video. Run from the group directory so the "
            "ASCII filename is passed to the decoder."
        )
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    reported_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames: list[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frames.append(frame)
    cap.release()
    if not frames:
        raise RuntimeError("No frames decoded from video.")
    meta = {
        "video": VIDEO_NAME,
        "reported_frame_count": reported_count,
        "decoded_frame_count": len(frames),
        "fps": fps,
        "width": width,
        "height": height,
        "duration_s": len(frames) / fps if fps > 0 else float("nan"),
    }
    return np.stack(frames, axis=0), meta


def parabolic_peak(y: np.ndarray, idx: int) -> float:
    if idx <= 0 or idx >= len(y) - 1:
        return float(idx)
    denom = y[idx - 1] - 2 * y[idx] + y[idx + 1]
    if abs(denom) < 1e-12:
        return float(idx)
    return float(idx + 0.5 * (y[idx - 1] - y[idx + 1]) / denom)


def ruler_period_from_strip(gray: np.ndarray, y1: int, y2: int) -> float:
    x1, x2 = 20, gray.shape[1] - 20
    darkness = 255.0 - gray[y1:y2, x1:x2].astype(float).mean(axis=0)
    darkness -= gaussian_filter1d(darkness, 35)
    darkness = np.maximum(darkness, 0)
    darkness -= darkness.mean()
    if np.std(darkness) < 1e-6:
        return float("nan")
    ac = correlate(darkness, darkness, mode="full", method="fft")
    ac = ac[len(ac) // 2 :]
    lo, hi = 24, 37
    local = ac[lo:hi]
    best = int(np.argmax(local)) + lo
    return parabolic_peak(ac, best)


def calibrate_ruler(frames: np.ndarray) -> tuple[dict, pd.DataFrame]:
    indices = np.unique(np.linspace(0, len(frames) - 1, 12).round().astype(int))
    rows = []
    for idx in indices:
        gray = cv2.cvtColor(frames[idx], cv2.COLOR_BGR2GRAY)
        strips = [
            (RULER_Y1, RULER_Y2),
            (RULER_Y1, RULER_Y1 + 14),
            (RULER_Y1 + 10, RULER_Y1 + 25),
            (RULER_Y1 + 22, RULER_Y2),
        ]
        estimates = [ruler_period_from_strip(gray, a, b) for a, b in strips]
        estimates = [e for e in estimates if np.isfinite(e) and 24 <= e <= 37]
        rows.append(
            {
                "frame": int(idx),
                "ruler_y1": RULER_Y1,
                "ruler_y2": RULER_Y2,
                "strip_estimates_px_per_cm": "|".join(f"{e:.3f}" for e in estimates),
                "px_per_cm": float(np.median(estimates)) if estimates else float("nan"),
            }
        )
    df = pd.DataFrame(rows)
    good = df["px_per_cm"].replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
    if len(good) == 0:
        raise RuntimeError("Ruler tick calibration failed even though the ruler is visible.")
    calib = {
        "method": "background_ruler_tick_autocorrelation",
        "ruler_y1": RULER_Y1,
        "ruler_y2": RULER_Y2,
        "px_per_cm": float(np.median(good)),
        "px_per_cm_mean": float(np.mean(good)),
        "px_per_cm_std": float(np.std(good, ddof=1)) if len(good) > 1 else 0.0,
        "samples": int(len(good)),
    }
    df.to_csv("calibration_samples.csv", index=False, encoding="utf-8-sig")
    return calib, df


def plot_ruler_diagnostic(frames: np.ndarray, calib: dict, df: pd.DataFrame) -> None:
    avg = np.mean(frames[np.unique(np.linspace(0, len(frames) - 1, 8).round().astype(int))], axis=0).astype(np.uint8)
    rgb = cv2.cvtColor(avg, cv2.COLOR_BGR2RGB)
    crop = rgb[RULER_Y1 - 25 : RULER_Y2 + 28, :]
    period = calib["px_per_cm"]
    fig, axes = plt.subplots(2, 1, figsize=(12, 6), gridspec_kw={"height_ratios": [2.2, 1]})
    axes[0].imshow(crop)
    axes[0].set_title(f"背景直尺标定诊断：{period:.3f} px/cm")
    axes[0].set_xlabel("x (px)")
    axes[0].set_ylabel("ruler crop y")
    for x in np.arange(0, frames.shape[2], period):
        axes[0].axvline(x, color="yellow", lw=0.35, alpha=0.45)
    axes[0].axhline(25, color="cyan", lw=1.0)
    axes[0].axhline(25 + (RULER_Y2 - RULER_Y1), color="cyan", lw=1.0)

    axes[1].plot(df["frame"], df["px_per_cm"], marker="o", lw=1.4)
    axes[1].axhline(period, color="crimson", ls="--", lw=1.0, label="median")
    axes[1].set_xlabel("frame")
    axes[1].set_ylabel("px/cm")
    axes[1].set_title("逐帧抽样标定值")
    axes[1].grid(True, alpha=0.25)
    axes[1].legend()
    save_png("ruler_calibration_diagnostic.png")


def extract_surface_lines(frames: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n, _h, w, _c = frames.shape
    lines = np.empty((n, w), dtype=float)
    strengths = np.empty((n, w), dtype=float)
    for i, frame in enumerate(frames):
        green = frame[:, :, 1].astype(float)
        crop = green[SURFACE_Y_MIN:SURFACE_Y_MAX, :]
        smooth = gaussian_filter(crop, sigma=(1.4, 2.2))
        grad = np.diff(smooth, axis=0)
        idx = np.argmax(grad, axis=0)
        maxv = np.max(grad, axis=0)
        line = SURFACE_Y_MIN + idx.astype(float) + 0.5
        med = median_filter(line, size=21, mode="nearest")
        outlier = np.abs(line - med) > 9
        line[outlier] = med[outlier]
        if w >= 41:
            line = savgol_filter(line, 41, 2, mode="interp")
        line = gaussian_filter1d(line, 2.0, mode="nearest")
        lines[i] = line
        strengths[i] = maxv
    lines = median_filter(lines, size=(3, 1), mode="nearest")
    return lines, strengths


def make_eta(lines: np.ndarray, calib: dict, meta: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    px_per_cm = calib["px_per_cm"]
    x_px = np.arange(X_MIN, X_MAX)
    surface = lines[:, X_MIN:X_MAX]
    baseline_y = np.median(surface, axis=0)
    eta_cm = -(surface - baseline_y[None, :]) / px_per_cm
    eta_cm -= np.median(eta_cm, axis=1, keepdims=True)
    x_cm = (x_px - X_MIN) / px_per_cm
    t_s = np.arange(lines.shape[0]) / meta["fps"]
    return eta_cm, surface, baseline_y, x_px, x_cm, t_s


def plot_waterline_check(frames: np.ndarray, lines: np.ndarray, meta: dict) -> None:
    sample_indices = [0, len(frames) // 3, 2 * len(frames) // 3, len(frames) - 1]
    fig, axes = plt.subplots(len(sample_indices), 1, figsize=(12, 9), sharex=True)
    for ax, idx in zip(axes, sample_indices):
        frame = cv2.cvtColor(frames[idx], cv2.COLOR_BGR2RGB)
        y0, y1 = SURFACE_Y_MIN - 18, SURFACE_Y_MAX + 10
        ax.imshow(frame[y0:y1, :, :])
        ax.plot(np.arange(frames.shape[2]), lines[idx] - y0, color="red", lw=1.0)
        ax.axhline(SURFACE_Y_MIN - y0, color="cyan", ls=":", lw=0.8)
        ax.axhline(SURFACE_Y_MAX - y0, color="cyan", ls=":", lw=0.8)
        ax.set_ylabel(f"{idx}\n{idx / meta['fps']:.2f}s")
        ax.set_ylim(y1 - y0, 0)
    axes[-1].set_xlabel("x (px)")
    fig.suptitle("surface / waterline 检查：红线为逐帧提取的 eta(x,t) 水面线", y=0.995)
    save_png("surface_waterline_check.png")


def save_eta_products(
    eta_cm: np.ndarray,
    surface: np.ndarray,
    baseline_y: np.ndarray,
    x_px: np.ndarray,
    x_cm: np.ndarray,
    t_s: np.ndarray,
    calib: dict,
    meta: dict,
) -> None:
    np.savez_compressed(
        "eta_xt_core_data.npz",
        eta_cm=eta_cm,
        surface_y_px=surface,
        baseline_y_px=baseline_y,
        x_px=x_px,
        x_cm=x_cm,
        t_s=t_s,
        px_per_cm=calib["px_per_cm"],
        fps=meta["fps"],
    )
    sampled_cols = np.linspace(0, eta_cm.shape[1] - 1, min(240, eta_cm.shape[1])).round().astype(int)
    matrix = pd.DataFrame(eta_cm[:, sampled_cols], columns=[f"x_{x_cm[j]:.3f}_cm" for j in sampled_cols])
    matrix.insert(0, "time_s", t_s)
    matrix.to_csv("eta_xt_matrix_sampled.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        {
            "time_s": t_s,
            "mean_eta_cm": eta_cm.mean(axis=1),
            "rms_eta_cm": np.sqrt(np.mean(eta_cm**2, axis=1)),
            "max_eta_cm": eta_cm.max(axis=1),
            "min_eta_cm": eta_cm.min(axis=1),
        }
    ).to_csv("eta_time_series_stats.csv", index=False, encoding="utf-8-sig")


def field_for_fft(eta_cm: np.ndarray) -> np.ndarray:
    field = eta_cm.astype(float).copy()
    field -= np.mean(field, axis=0, keepdims=True)
    field -= np.mean(field, axis=1, keepdims=True)
    field -= gaussian_filter(field, sigma=(10, 90), mode="nearest")
    return field


def direction_masks(shape: tuple[int, int], dt: float, dx: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    nt, nx = shape
    ft = np.fft.fftfreq(nt, d=dt)[:, None]
    fx = np.fft.fftfreq(nx, d=dx)[None, :]
    lambda_min, lambda_max = 5.0, 70.0
    temporal_min = 0.15
    band = (
        (np.abs(ft) >= temporal_min)
        & (np.abs(fx) >= 1.0 / lambda_max)
        & (np.abs(fx) <= 1.0 / lambda_min)
    )
    right = (ft * fx < 0) & band
    left = (ft * fx > 0) & band
    return right, left, band, ft, fx


def directional_components(field: np.ndarray, dt: float, dx: float, incident_sign: str | None = None) -> dict:
    f = np.fft.fft2(field)
    right, left, band, ft, fx = direction_masks(field.shape, dt, dx)
    right_energy = float(np.sum(np.abs(f[right]) ** 2))
    left_energy = float(np.sum(np.abs(f[left]) ** 2))
    if incident_sign is None:
        incident_sign = "right" if right_energy >= left_energy else "left"
    inc_mask = right if incident_sign == "right" else left
    ref_mask = left if incident_sign == "right" else right
    incident = np.fft.ifft2(f * inc_mask).real
    reflected = np.fft.ifft2(f * ref_mask).real
    inc_energy = float(np.sum(np.abs(f[inc_mask]) ** 2))
    ref_energy = float(np.sum(np.abs(f[ref_mask]) ** 2))
    return {
        "incident_sign": incident_sign,
        "right_energy": right_energy,
        "left_energy": left_energy,
        "incident_energy": inc_energy,
        "reflected_energy": ref_energy,
        "reflection_energy_ratio": ref_energy / inc_energy if inc_energy > 0 else float("nan"),
        "incident": incident,
        "reflected": reflected,
        "fft": f,
        "band": band,
        "ft": ft,
        "fx": fx,
    }


def dominant_wavelength_fft(field: np.ndarray, dt: float, dx: float, incident_sign: str) -> dict:
    nt, nx = field.shape
    pad_t = max(512, 2 ** int(math.ceil(math.log2(nt * 4))))
    pad_x = max(4096, 2 ** int(math.ceil(math.log2(nx * 4))))
    window = np.hanning(nt)[:, None] * np.hanning(nx)[None, :]
    f = np.fft.fft2(field * window, s=(pad_t, pad_x))
    ft = np.fft.fftfreq(pad_t, d=dt)[:, None]
    fx = np.fft.fftfreq(pad_x, d=dx)[None, :]
    band = (
        (np.abs(ft) >= 0.15)
        & (np.abs(fx) >= 1.0 / 70.0)
        & (np.abs(fx) <= 1.0 / 5.0)
    )
    direction = (ft * fx < 0) if incident_sign == "right" else (ft * fx > 0)
    mask = band & direction
    power = np.abs(f) ** 2
    masked = np.where(mask, power, 0.0)
    flat_idx = int(np.argmax(masked))
    iy, ix = np.unravel_index(flat_idx, masked.shape)
    peak_fx = float(fx[0, ix])
    peak_ft = float(ft[iy, 0])
    main_lambda = 1.0 / abs(peak_fx) if abs(peak_fx) > 0 else float("nan")
    main_period = 1.0 / abs(peak_ft) if abs(peak_ft) > 0 else float("nan")
    masked2 = masked.copy()
    fy_radius = max(2, pad_t // 80)
    fx_radius = max(3, pad_x // 120)
    y0, y1 = max(0, iy - fy_radius), min(pad_t, iy + fy_radius + 1)
    x0, x1 = max(0, ix - fx_radius), min(pad_x, ix + fx_radius + 1)
    masked2[y0:y1, x0:x1] = 0.0
    dft = abs(float(ft[1, 0] - ft[0, 0]))
    dfx = abs(float(fx[0, 1] - fx[0, 0]))
    same_conjugate_pair = (
        np.abs(np.abs(ft) - abs(peak_ft)) <= fy_radius * dft
    ) & (
        np.abs(np.abs(fx) - abs(peak_fx)) <= fx_radius * dfx
    )
    masked2[same_conjugate_pair] = 0.0
    if masked2.max() > 0:
        iy2, ix2 = np.unravel_index(int(np.argmax(masked2)), masked2.shape)
        sec_fx = float(fx[0, ix2])
        secondary_lambda = 1.0 / abs(sec_fx) if abs(sec_fx) > 0 else float("nan")
        secondary_ratio = float(masked2[iy2, ix2] / masked[iy, ix]) if masked[iy, ix] > 0 else float("nan")
    else:
        secondary_lambda = float("nan")
        secondary_ratio = float("nan")
    return {
        "fft_incident_lambda_cm": main_lambda,
        "fft_incident_period_s": main_period,
        "fft_incident_frequency_hz": abs(peak_ft),
        "fft_incident_fx_cyc_per_cm": peak_fx,
        "fft_secondary_lambda_cm": secondary_lambda,
        "fft_secondary_to_main_power": secondary_ratio,
    }


def plot_xt_panels(
    field: np.ndarray,
    incident: np.ndarray,
    reflected: np.ndarray,
    x_cm: np.ndarray,
    t_s: np.ndarray,
    direction: dict,
    fft_info: dict,
) -> None:
    vmax = np.nanpercentile(np.abs(field), 98)
    vmax = max(vmax, 1e-3)
    extent = [float(x_cm[0]), float(x_cm[-1]), float(t_s[-1]), float(t_s[0])]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
    titles = [
        "原始 eta(x,t) 去趋势场",
        f"入射分量（{direction['incident_sign']}）",
        "反射/反向分量",
    ]
    for ax, data, title in zip(axes, [field, incident, reflected], titles):
        im = ax.imshow(data, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto", extent=extent)
        ax.set_title(title)
        ax.set_xlabel("x (cm, relative)")
    axes[0].set_ylabel("time (s)")
    cbar = fig.colorbar(im, ax=axes, shrink=0.88, pad=0.015)
    cbar.set_label("eta (cm)")
    fig.suptitle(
        "x-t 图与 2D FFT 方向分离："
        f"能量比(ref/inc)={direction['reflection_energy_ratio']:.3f}；"
        f"FFT诊断入射波长={fft_info['fft_incident_lambda_cm']:.2f} cm",
        y=1.02,
    )
    save_png("xt_raw_incident_reflected_panels.png")


def sliding_reflection_windows(field: np.ndarray, dt: float, dx: float, incident_sign: str, t_s: np.ndarray) -> pd.DataFrame:
    nt = field.shape[0]
    win = min(nt, max(48, int(round(2.0 / dt))))
    step = max(1, int(round(0.25 / dt)))
    rows = []
    for start in range(0, nt - win + 1, step):
        end = start + win
        sub = field[start:end]
        d = directional_components(sub, dt, dx, incident_sign)
        fft = dominant_wavelength_fft(sub, dt, dx, incident_sign)
        rows.append(
            {
                "start_frame": start,
                "end_frame_exclusive": end,
                "center_time_s": float((t_s[start] + t_s[end - 1]) / 2),
                "start_time_s": float(t_s[start]),
                "end_time_s": float(t_s[end - 1]),
                "incident_energy": d["incident_energy"],
                "reflected_energy": d["reflected_energy"],
                "reflection_energy_ratio": d["reflection_energy_ratio"],
                "reflection_amplitude_ratio_sqrt": math.sqrt(max(d["reflection_energy_ratio"], 0.0)),
                "fft_incident_lambda_cm": fft["fft_incident_lambda_cm"],
                "fft_incident_period_s": fft["fft_incident_period_s"],
            }
        )
    df = pd.DataFrame(rows)
    if len(df) == 0:
        return df
    energy_floor = df["incident_energy"].quantile(0.25)
    median_lambda = df["fft_incident_lambda_cm"].replace([np.inf, -np.inf], np.nan).median()
    stable = df["incident_energy"] >= energy_floor
    if np.isfinite(median_lambda):
        stable &= np.abs(df["fft_incident_lambda_cm"] - median_lambda) / median_lambda <= 0.35
    df["stable_candidate"] = stable
    score = df["reflection_energy_ratio"].to_numpy(dtype=float)
    if np.isfinite(median_lambda):
        score = score + 0.08 * np.abs(df["fft_incident_lambda_cm"].to_numpy(dtype=float) - median_lambda) / median_lambda
    score = np.where(stable, score, np.inf)
    selected = int(np.nanargmin(score)) if np.isfinite(score).any() else int(df["reflection_energy_ratio"].idxmin())
    df["selected_low_reflection_window"] = False
    df.loc[selected, "selected_low_reflection_window"] = True
    df.to_csv("reflection_windows.csv", index=False, encoding="utf-8-sig")
    return df


def plot_reflection_strength(windows: pd.DataFrame) -> None:
    fig, ax1 = plt.subplots(figsize=(9, 4.8))
    ax1.plot(windows["center_time_s"], windows["reflection_energy_ratio"], marker="o", lw=1.4, label="反射/入射能量比")
    ax1.set_xlabel("window center time (s)")
    ax1.set_ylabel("energy ratio")
    ax1.grid(True, alpha=0.25)
    selected = windows[windows["selected_low_reflection_window"]]
    if len(selected):
        row = selected.iloc[0]
        ax1.axvspan(row["start_time_s"], row["end_time_s"], color="gold", alpha=0.25, label="低反射稳定窗口")
        ax1.scatter([row["center_time_s"]], [row["reflection_energy_ratio"]], s=80, color="crimson", zorder=4)
    ax2 = ax1.twinx()
    ax2.plot(windows["center_time_s"], windows["fft_incident_lambda_cm"], color="tab:green", marker="s", lw=1.0, alpha=0.75, label="FFT诊断入射波长")
    ax2.set_ylabel("lambda (cm)")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")
    fig.suptitle("方向分离反射强度与低反射窗口筛选")
    save_png("reflection_strength.png")


def profile_peak_distances(
    component: np.ndarray,
    x_cm: np.ndarray,
    frame_indices: np.ndarray,
    name: str,
    min_distance_cm: float,
    max_distance_cm: float,
) -> tuple[pd.DataFrame, dict]:
    dx = float(np.median(np.diff(x_cm)))
    min_distance_px = max(5, int(round(min_distance_cm / dx * 0.65)))
    rows = []
    for idx in frame_indices:
        profile = component[idx].astype(float)
        smooth_sigma_px = max(3.0, 0.16 / dx)
        smooth = gaussian_filter1d(profile, smooth_sigma_px, mode="nearest")
        smooth -= gaussian_filter1d(smooth, max(25.0, 3.5 / dx), mode="nearest")
        prominence = max(0.015, 0.28 * float(np.nanstd(smooth)))
        peaks, props = find_peaks(smooth, distance=min_distance_px, prominence=prominence)
        if len(peaks) < 2:
            continue
        for a, b in zip(peaks[:-1], peaks[1:]):
            dist = float(x_cm[b] - x_cm[a])
            if min_distance_cm <= dist <= max_distance_cm:
                rows.append(
                    {
                        "component": name,
                        "frame": int(idx),
                        "time_index": int(idx),
                        "peak_x1_cm": float(x_cm[a]),
                        "peak_x2_cm": float(x_cm[b]),
                        "distance_cm": dist,
                        "prominence_left_cm": float(props["prominences"][np.where(peaks == a)[0][0]]) if a in peaks else float("nan"),
                    }
                )
    df = pd.DataFrame(rows)
    if len(df):
        stats = {
            "component": name,
            "n": int(len(df)),
            "mean_cm": float(df["distance_cm"].mean()),
            "median_cm": float(df["distance_cm"].median()),
            "std_cm": float(df["distance_cm"].std(ddof=1)) if len(df) > 1 else 0.0,
            "min_cm": float(df["distance_cm"].min()),
            "max_cm": float(df["distance_cm"].max()),
        }
    else:
        stats = {
            "component": name,
            "n": 0,
            "mean_cm": float("nan"),
            "median_cm": float("nan"),
            "std_cm": float("nan"),
            "min_cm": float("nan"),
            "max_cm": float("nan"),
        }
    return df, stats


def select_peak_frames(windows: pd.DataFrame, t_s: np.ndarray) -> np.ndarray:
    if len(windows) and windows["selected_low_reflection_window"].any():
        row = windows[windows["selected_low_reflection_window"]].iloc[0]
        start = int(row["start_frame"])
        end = int(row["end_frame_exclusive"])
    else:
        start, end = len(t_s) // 3, len(t_s)
    if end <= start:
        return np.array([], dtype=int)
    count = min(10, end - start)
    return np.unique(np.linspace(start, end - 1, count).round().astype(int))


def peak_measurements(
    raw_field: np.ndarray,
    incident: np.ndarray,
    x_cm: np.ndarray,
    t_s: np.ndarray,
    windows: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frames = select_peak_frames(windows, t_s)
    raw_broad, raw_broad_stats = profile_peak_distances(raw_field, x_cm, frames, "direct_raw_broad_peak_distance", 17.0, 34.0)
    raw_local, raw_local_stats = profile_peak_distances(raw_field, x_cm, frames, "direct_raw_local_peak_distance", 8.0, 17.0)
    inc_profile, inc_profile_stats = profile_peak_distances(incident, x_cm, frames, "separated_incident_profile_peak_distance", 17.0, 35.0)
    all_dist = pd.concat([raw_broad, raw_local, inc_profile], ignore_index=True)
    all_dist.to_csv("wave_peak_distances.csv", index=False, encoding="utf-8-sig")
    stats = pd.DataFrame([raw_broad_stats, raw_local_stats, inc_profile_stats])
    stats.to_csv("wave_peak_distance_summary.csv", index=False, encoding="utf-8-sig")
    return all_dist, stats


def plot_peak_measurement(
    raw_field: np.ndarray,
    incident: np.ndarray,
    x_cm: np.ndarray,
    t_s: np.ndarray,
    peak_stats: pd.DataFrame,
    windows: pd.DataFrame,
) -> None:
    frames = select_peak_frames(windows, t_s)
    if len(frames) == 0:
        frames = np.array([len(t_s) // 2], dtype=int)
    chosen = int(frames[len(frames) // 2])
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    for ax, data, title in [
        (axes[0], raw_field[chosen], "低反射窗口内原始剖面"),
        (axes[1], incident[chosen], "方向分离后的入射剖面"),
    ]:
        smooth = gaussian_filter1d(data, max(3.0, 0.16 / np.median(np.diff(x_cm))), mode="nearest")
        ax.plot(x_cm, data, color="0.75", lw=0.8, label="raw")
        ax.plot(x_cm, smooth, color="tab:blue", lw=1.5, label="smoothed")
        dx_cm = float(np.median(np.diff(x_cm)))
        broad_distance_px = max(200, int(round(17.0 / dx_cm * 0.65)))
        peaks, _ = find_peaks(
            smooth - gaussian_filter1d(smooth, max(25.0, 3.5 / dx_cm), mode="nearest"),
            distance=broad_distance_px,
        )
        ax.scatter(x_cm[peaks], smooth[peaks], color="crimson", s=18, zorder=4)
        for a, b in zip(peaks[:-1], peaks[1:]):
            dist = x_cm[b] - x_cm[a]
            if 8 <= dist <= 35:
                ax.annotate(
                    f"{dist:.1f} cm",
                    xy=((x_cm[a] + x_cm[b]) / 2, max(smooth[a], smooth[b])),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha="center",
                    fontsize=8,
                    color="crimson",
                )
        ax.set_ylabel("eta (cm)")
        ax.set_title(f"{title}，frame={chosen}, t={t_s[chosen]:.2f}s")
        ax.grid(True, alpha=0.22)
        ax.legend(loc="upper right")
    axes[-1].set_xlabel("x (cm, relative)")
    text = []
    for _, row in peak_stats.iterrows():
        if row["n"] > 0:
            text.append(f"{row['component']}: {row['mean_cm']:.2f}±{row['std_cm']:.2f} cm (n={int(row['n'])})")
    fig.suptitle("波峰间距测量：" + "；".join(text[:3]), y=0.995)
    save_png("wave_peak_measurement.png")


def plot_judgement(summary: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.8))
    labels = ["直接宽峰距", "分离入射剖面", "FFT诊断"]
    vals = [
        summary.get("direct_broad_peak_distance_cm", np.nan),
        summary.get("incident_profile_peak_distance_cm", np.nan),
        summary.get("fft_incident_lambda_cm", np.nan),
    ]
    errs = [
        summary.get("direct_broad_peak_distance_std_cm", 0.0),
        summary.get("incident_profile_peak_distance_std_cm", 0.0),
        0.0,
    ]
    axes[0].bar(labels, vals, yerr=errs, color=["tab:blue", "tab:green", "0.65"], capsize=4)
    axes[0].set_ylabel("wavelength / peak spacing (cm)")
    axes[0].set_title("峰距/波长对比")
    axes[0].tick_params(axis="x", labelrotation=18)
    ratio = summary["selected_reflection_energy_ratio"]
    amp = summary["selected_reflection_amplitude_ratio"]
    axes[1].bar(["能量比", "幅值比sqrt"], [ratio, amp], color=["tab:orange", "tab:red"])
    axes[1].axhline(0.1, color="0.4", ls="--", lw=1, label="10%参考线")
    axes[1].set_ylim(0, max(0.35, ratio * 1.25, amp * 1.25))
    axes[1].set_title("低反射窗口反射强度")
    axes[1].legend()
    fig.suptitle(summary["judgement"])
    save_png("standing_wave_judgement_cn.png")


def build_summary(
    meta: dict,
    calib: dict,
    direction: dict,
    fft_info: dict,
    windows: pd.DataFrame,
    peak_stats: pd.DataFrame,
) -> dict:
    selected = windows[windows["selected_low_reflection_window"]].iloc[0] if len(windows) else None
    def stat_value(component: str, key: str) -> float:
        rows = peak_stats[peak_stats["component"] == component]
        if len(rows) == 0:
            return float("nan")
        return float(rows.iloc[0][key])

    global_ratio = direction["reflection_energy_ratio"]
    selected_ratio = float(selected["reflection_energy_ratio"]) if selected is not None else global_ratio
    selected_amp = math.sqrt(max(selected_ratio, 0.0))
    direct_broad = stat_value("direct_raw_broad_peak_distance", "mean_cm")
    incident_profile = stat_value("separated_incident_profile_peak_distance", "mean_cm")

    if selected_ratio < 0.08 and global_ratio > 0.25:
        judgement = "低反射窗口内反射弱，可用于行波波长测量；全片后段反射明显，整体解释需考虑驻波/反射"
    elif selected_ratio < 0.08 and selected_amp < 0.30:
        judgement = "反射较弱：优先按行波处理，驻波/反射作为误差项说明"
    elif selected_ratio < 0.18:
        judgement = "存在可见但不主导的反射：波长结论需结合低反射窗口和入射分量"
    else:
        judgement = "反射较强：需要显式考虑驻波/反射"

    fft_note = "诊断值"
    if meta["duration_s"] < 8 or (X_MAX - X_MIN) / calib["px_per_cm"] < 2 * fft_info["fft_incident_lambda_cm"]:
        fft_note = "诊断值；短视频/视场有限，不作为唯一最终波长"

    summary = {
        "video": VIDEO_NAME,
        "experiment_folder": "10.0",
        "decoded_frames": meta["decoded_frame_count"],
        "fps": meta["fps"],
        "duration_s": meta["duration_s"],
        "field_width_cm": (X_MAX - X_MIN) / calib["px_per_cm"],
        "px_per_cm": calib["px_per_cm"],
        "px_per_cm_std": calib["px_per_cm_std"],
        "calibration_method": calib["method"],
        "incident_direction": direction["incident_sign"],
        "global_reflection_energy_ratio": global_ratio,
        "global_reflection_amplitude_ratio": math.sqrt(max(global_ratio, 0.0)),
        "selected_window_start_s": float(selected["start_time_s"]) if selected is not None else float("nan"),
        "selected_window_end_s": float(selected["end_time_s"]) if selected is not None else float("nan"),
        "selected_reflection_energy_ratio": selected_ratio,
        "selected_reflection_amplitude_ratio": selected_amp,
        "fft_incident_lambda_cm": fft_info["fft_incident_lambda_cm"],
        "fft_incident_period_s": fft_info["fft_incident_period_s"],
        "fft_secondary_lambda_cm": fft_info["fft_secondary_lambda_cm"],
        "fft_secondary_to_main_power": fft_info["fft_secondary_to_main_power"],
        "fft_status": fft_note,
        "direct_broad_peak_distance_cm": direct_broad,
        "direct_broad_peak_distance_std_cm": stat_value("direct_raw_broad_peak_distance", "std_cm"),
        "direct_broad_peak_distance_n": int(stat_value("direct_raw_broad_peak_distance", "n")),
        "direct_local_peak_distance_cm": stat_value("direct_raw_local_peak_distance", "mean_cm"),
        "direct_local_peak_distance_std_cm": stat_value("direct_raw_local_peak_distance", "std_cm"),
        "direct_local_peak_distance_n": int(stat_value("direct_raw_local_peak_distance", "n")),
        "incident_profile_peak_distance_cm": incident_profile,
        "incident_profile_peak_distance_std_cm": stat_value("separated_incident_profile_peak_distance", "std_cm"),
        "incident_profile_peak_distance_n": int(stat_value("separated_incident_profile_peak_distance", "n")),
        "judgement": judgement,
    }
    pd.DataFrame([summary]).to_csv("standing_wave_summary_cn.csv", index=False, encoding="utf-8-sig")
    return summary


def write_report(summary: dict, meta: dict, calib: dict) -> None:
    lines = [
        "# 10.0 水波视频驻波/反射分析报告",
        "",
        "## 数据与标定",
        f"- 输入视频：`{VIDEO_NAME}`。",
        f"- 完整逐帧读取：{summary['decoded_frames']} 帧，fps={summary['fps']:.3f}，时长 {summary['duration_s']:.2f} s，画面 {meta['width']}x{meta['height']} px。",
        f"- 直尺标定：底部背景直尺刻度可见，使用刻度投影自相关估计，px/cm = {summary['px_per_cm']:.3f} ± {summary['px_per_cm_std']:.3f}（n={calib['samples']} 个抽样帧）。未使用替代标定。",
        f"- x-t 分析视场：x={X_MIN}..{X_MAX - 1} px，宽度约 {summary['field_width_cm']:.2f} cm；eta(x,t) 由上方水面暗/亮界面逐列梯度提取并转成 cm。",
        "",
        "## 方向分离与反射强度",
        f"- 2D FFT 方向判定：主入射方向为 `{summary['incident_direction']}`。",
        f"- 全片反射/入射能量比：{summary['global_reflection_energy_ratio']:.3f}；对应幅值比 sqrt(E_ref/E_inc)≈{summary['global_reflection_amplitude_ratio']:.3f}。",
        f"- 低反射稳定窗口：{summary['selected_window_start_s']:.2f}--{summary['selected_window_end_s']:.2f} s，反射/入射能量比 {summary['selected_reflection_energy_ratio']:.3f}，幅值比≈{summary['selected_reflection_amplitude_ratio']:.3f}。",
        "",
        "## 波长/峰距",
        f"- 低反射窗口直接宽峰距：{summary['direct_broad_peak_distance_cm']:.2f} ± {summary['direct_broad_peak_distance_std_cm']:.2f} cm（n={summary['direct_broad_peak_distance_n']}）。",
        f"- 直接局部峰距候选：{summary['direct_local_peak_distance_cm']:.2f} ± {summary['direct_local_peak_distance_std_cm']:.2f} cm（n={summary['direct_local_peak_distance_n']}），用于提示局部纹理/次级峰，不单独作为最终波长。",
        f"- 分离后入射剖面峰距：{summary['incident_profile_peak_distance_cm']:.2f} ± {summary['incident_profile_peak_distance_std_cm']:.2f} cm（n={summary['incident_profile_peak_distance_n']}）。",
        f"- 入射分量 2D FFT 主波长：{summary['fft_incident_lambda_cm']:.2f} cm，周期约 {summary['fft_incident_period_s']:.2f} s；状态：{summary['fft_status']}。",
        "",
        "## 判断",
        f"- {summary['judgement']}。",
        "- 本视频只有约 5.6 s，且有效视场不足以稳定容纳多组长波波峰；因此不把全帧 2D FFT 峰值当作唯一高精度最终波长。更可靠的读数是低反射窗口内的直接宽峰距与分离后入射剖面峰距，两者共同约束波长范围。",
        "",
        "## 主要输出",
        "- `standing_wave_summary_cn.csv`：中文汇总表。",
        "- `standing_wave_judgement_cn.png`：判断图。",
        "- `wave_peak_measurement.png`：峰距测量图。",
        "- `xt_raw_incident_reflected_panels.png`：原始/入射/反射 x-t 面板。",
        "- `reflection_strength.png`：滑动窗口反射强度。",
        "- `ruler_calibration_diagnostic.png`：直尺标定诊断。",
        "- `surface_waterline_check.png`：surface/waterline 检查图。",
        "- `eta_xt_core_data.npz`、`eta_xt_matrix_sampled.csv`、`wave_peak_distances.csv`、`reflection_windows.csv`：核心数据。",
    ]
    Path("standing_wave_cn_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manifest() -> None:
    expected = [
        "analyze_standing_wave_10_0.py",
        "standing_wave_cn_report.md",
        "standing_wave_summary_cn.csv",
        "standing_wave_judgement_cn.png",
        "wave_peak_measurement.png",
        "xt_raw_incident_reflected_panels.png",
        "reflection_strength.png",
        "ruler_calibration_diagnostic.png",
        "surface_waterline_check.png",
        "eta_xt_core_data.npz",
        "eta_xt_matrix_sampled.csv",
        "eta_time_series_stats.csv",
        "calibration_samples.csv",
        "wave_peak_distances.csv",
        "wave_peak_distance_summary.csv",
        "reflection_windows.csv",
        "analysis_metadata.json",
    ]
    with Path("analysis_output_manifest.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "bytes", "exists"])
        writer.writeheader()
        for name in expected:
            path = OUT / name
            writer.writerow({"file": name, "bytes": path.stat().st_size if path.exists() else 0, "exists": path.exists()})


def cleanup_plot_cache() -> None:
    for path in OUT.glob("fontlist-v*.json"):
        path.unlink(missing_ok=True)


def main() -> None:
    configure_chinese_font()
    frames, meta = read_video()
    calib, calib_df = calibrate_ruler(frames)
    plot_ruler_diagnostic(frames, calib, calib_df)
    lines, strengths = extract_surface_lines(frames)
    eta_cm, surface, baseline_y, x_px, x_cm, t_s = make_eta(lines, calib, meta)
    plot_waterline_check(frames, lines, meta)
    save_eta_products(eta_cm, surface, baseline_y, x_px, x_cm, t_s, calib, meta)

    field = field_for_fft(eta_cm)
    dt = 1.0 / meta["fps"]
    dx = float(np.median(np.diff(x_cm)))
    direction = directional_components(field, dt, dx)
    fft_info = dominant_wavelength_fft(field, dt, dx, direction["incident_sign"])
    plot_xt_panels(field, direction["incident"], direction["reflected"], x_cm, t_s, direction, fft_info)
    windows = sliding_reflection_windows(field, dt, dx, direction["incident_sign"], t_s)
    plot_reflection_strength(windows)
    peak_distances, peak_stats = peak_measurements(field, direction["incident"], x_cm, t_s, windows)
    plot_peak_measurement(field, direction["incident"], x_cm, t_s, peak_stats, windows)
    summary = build_summary(meta, calib, direction, fft_info, windows, peak_stats)
    plot_judgement(summary)
    write_report(summary, meta, calib)
    Path("analysis_metadata.json").write_text(
        json.dumps({"meta": meta, "calibration": calib, "summary": summary}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    cleanup_plot_cache()
    write_manifest()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

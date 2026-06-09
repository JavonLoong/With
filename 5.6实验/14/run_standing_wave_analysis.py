# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import warnings
from pathlib import Path

import cv2
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage, signal
from scipy.signal import find_peaks
from skimage import color, exposure, measure, morphology


VIDEO_NAME = "82ca0fe44590dc1c480dfe881d8b319b.mp4"
DATA_GROUP = "14"


def setup_matplotlib() -> None:
    matplotlib.use("Agg")
    matplotlib.rcParams["font.sans-serif"] = [
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Arial Unicode MS",
        "DejaVu Sans",
    ]
    matplotlib.rcParams["axes.unicode_minus"] = False
    matplotlib.rcParams["figure.dpi"] = 160


def read_video(video_path: Path) -> tuple[np.ndarray, float]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频: {video_path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    frames: list[np.ndarray] = []
    while True:
        ok, frame_bgr = cap.read()
        if not ok:
            break
        frames.append(frame_bgr[:, :, ::-1].copy())
    cap.release()
    if not frames:
        raise RuntimeError(f"未能从视频读取任何帧: {video_path}")
    return np.stack(frames, axis=0), fps


def detect_ruler_label_components(frame: np.ndarray, y1: int = 440, y2: int = 492) -> list[dict[str, float]]:
    crop = frame[y1:y2, :, :].astype(np.float32) / 255.0
    gray = color.rgb2gray(crop)
    clahe = exposure.equalize_adapthist(gray, kernel_size=(15, 55), clip_limit=0.03)
    mask = clahe < 0.25
    mask[:5, :] = False
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mask = morphology.remove_small_objects(mask, min_size=8)

    labels = measure.label(mask)
    components: list[dict[str, float]] = []
    for region in measure.regionprops(labels):
        minr, minc, maxr, maxc = region.bbox
        width = maxc - minc
        height = maxr - minr
        if region.area > 220 and 25 <= width <= 45 and 15 <= height <= 34:
            components.append(
                {
                    "x_px": (minc + maxc) / 2.0,
                    "x1_px": float(minc),
                    "x2_px": float(maxc),
                    "y1_px": float(y1 + minr),
                    "y2_px": float(y1 + maxr),
                    "area_px": float(region.area),
                    "width_px": float(width),
                    "height_px": float(height),
                }
            )
    components.sort(key=lambda row: row["x_px"])
    return components


def calibrate_from_ruler(frames: np.ndarray) -> tuple[pd.DataFrame, dict[str, float]]:
    label_values = np.array([210.0, 200.0, 190.0, 180.0, 170.0])
    candidate_frames = [0, 1, 2, len(frames) // 4, len(frames) // 2, 3 * len(frames) // 4]
    best: tuple[int, list[dict[str, float]], float] | None = None

    for frame_idx in candidate_frames:
        components = detect_ruler_label_components(frames[frame_idx])
        if len(components) < 5:
            continue
        candidate = components[:5]
        x = np.array([row["x_px"] for row in candidate], dtype=np.float64)
        pair_scales = np.diff(x) / 10.0
        if np.any(pair_scales < 18.0) or np.any(pair_scales > 34.0):
            continue
        uniformity_pct = float(np.std(pair_scales, ddof=1) / np.mean(pair_scales) * 100.0)
        if best is None or uniformity_pct < best[2]:
            best = (frame_idx, candidate, uniformity_pct)

    if best is None:
        raise RuntimeError("直尺刻度可见但未能稳定识别 210/200/190/180/170 cm 盒标，需要人工检查标定。")

    frame_idx, selected, pair_scale_std_pct = best
    calib_points = pd.DataFrame(selected)
    calib_points.insert(0, "ruler_reading_cm", label_values)
    calib_points.insert(
        1,
        "basis",
        [f"第 {frame_idx} 帧可见盒标 {int(v)} cm" for v in label_values],
    )

    x = calib_points["x_px"].to_numpy(dtype=np.float64)
    reading = calib_points["ruler_reading_cm"].to_numpy(dtype=np.float64)
    slope, intercept = np.polyfit(x, reading, 1)
    fitted = slope * x + intercept
    residual = reading - fitted
    calib_points["fit_reading_cm"] = fitted
    calib_points["residual_cm"] = residual

    pair_scales = np.abs(np.diff(x) / np.diff(reading))
    cm_per_px = float(abs(slope))
    px_per_cm = float(1.0 / cm_per_px)
    rmse_cm = float(np.sqrt(np.mean(residual**2)))
    max_abs_residual_cm = float(np.max(np.abs(residual)))
    estimated_uncertainty_pct = float(max(1.0, min(2.5, pair_scale_std_pct + 0.25)))

    calibration = {
        "calibration_frame": float(frame_idx),
        "ruler_crop_y1": 440.0,
        "ruler_crop_y2": 492.0,
        "slope_cm_per_px_signed": float(slope),
        "intercept_cm": float(intercept),
        "cm_per_px": cm_per_px,
        "px_per_cm": px_per_cm,
        "fit_rmse_cm": rmse_cm,
        "fit_max_abs_residual_cm": max_abs_residual_cm,
        "pair_scale_mean_px_per_cm": float(np.mean(pair_scales)),
        "pair_scale_std_pct": pair_scale_std_pct,
        "estimated_scale_uncertainty_pct": estimated_uncertainty_pct,
    }
    return calib_points, calibration


def extract_surface_y(frame: np.ndarray) -> tuple[np.ndarray, int]:
    green = frame[:, :, 1].astype(np.float32)
    smooth = ndimage.gaussian_filter(green, sigma=(1.2, 2.5))
    y0, y1 = 45, 155
    roi = smooth[y0:y1, :]
    grad_y = np.gradient(roi, axis=0)

    row_score = ndimage.gaussian_filter1d(grad_y[:, 60:1220].mean(axis=1), sigma=2.0)
    global_y = y0 + int(np.argmax(row_score))
    lo = max(0, global_y - y0 - 45)
    hi = min(roi.shape[0], global_y - y0 + 45)

    ys = np.empty(frame.shape[1], dtype=np.float32)
    for x in range(frame.shape[1]):
        ys[x] = y0 + lo + int(np.argmax(grad_y[lo:hi, x]))

    median = ndimage.median_filter(ys, size=13, mode="nearest")
    outliers = np.abs(ys - median) > 10.0
    ys[outliers] = median[outliers]
    ys = ndimage.median_filter(ys, size=9, mode="nearest")
    ys = signal.savgol_filter(ys, 61, 3, mode="interp")
    return ys.astype(np.float32), global_y


def extract_all_surfaces(frames: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    surfaces = []
    global_rows = []
    for frame in frames:
        surface, global_y = extract_surface_y(frame)
        surfaces.append(surface)
        global_rows.append(global_y)
    return np.stack(surfaces, axis=0), np.asarray(global_rows, dtype=np.float32)


def make_eta(surface_y_px: np.ndarray) -> np.ndarray:
    eta = -surface_y_px.astype(np.float32)
    eta = eta - np.median(eta, axis=0, keepdims=True)
    eta = eta - np.median(eta, axis=1, keepdims=True)
    eta = signal.detrend(eta, axis=1, type="linear")
    return eta.astype(np.float32)


def directional_fft(eta_px: np.ndarray, fps: float, dx_cm: float) -> dict[str, object]:
    dt = 1.0 / fps
    eta_work = signal.detrend(eta_px, axis=0, type="linear")
    eta_work = signal.detrend(eta_work, axis=1, type="linear")
    frame_count, x_count = eta_work.shape

    f_t = np.fft.fftfreq(frame_count, d=dt)
    f_x = np.fft.fftfreq(x_count, d=dx_cm)
    ft_grid, fx_grid = np.meshgrid(f_t, f_x, indexing="ij")
    raw_fft = np.fft.fft2(eta_work)
    energy = np.abs(raw_fft) ** 2

    wave_mask = (np.abs(ft_grid) > 0.25) & (np.abs(fx_grid) > 0.012) & (np.abs(fx_grid) < 0.18)
    pos_energy = float(energy[(ft_grid * fx_grid > 0) & wave_mask].sum())
    neg_energy = float(energy[(ft_grid * fx_grid < 0) & wave_mask].sum())
    incident_sign = 1 if pos_energy >= neg_energy else -1
    incident_direction = "leftward(-x)" if incident_sign > 0 else "rightward(+x)"

    inc_mask = (ft_grid * fx_grid * incident_sign > 0) & wave_mask
    ref_mask = (ft_grid * fx_grid * incident_sign < 0) & wave_mask
    eta_incident = np.fft.ifft2(raw_fft * inc_mask).real.astype(np.float32)
    eta_reflected = np.fft.ifft2(raw_fft * ref_mask).real.astype(np.float32)

    n_t = 2 ** int(math.ceil(math.log2(frame_count * 4)))
    n_x = 2 ** int(math.ceil(math.log2(x_count * 4)))
    window = np.hanning(frame_count)[:, None] * np.hanning(x_count)[None, :]
    padded_fft = np.fft.fft2(eta_work * window, s=(n_t, n_x))
    p_f_t = np.fft.fftfreq(n_t, d=dt)
    p_f_x = np.fft.fftfreq(n_x, d=dx_cm)
    pft_grid, pfx_grid = np.meshgrid(p_f_t, p_f_x, indexing="ij")
    padded_power = np.abs(padded_fft) ** 2

    diagnostic_mask = (
        (p_f_t[:, None] > 0.25)
        & (p_f_t[:, None] < 8.0)
        & (np.abs(p_f_x[None, :]) > 0.012)
        & (np.abs(p_f_x[None, :]) < 0.12)
        & (pft_grid * pfx_grid * incident_sign > 0)
    )
    diagnostic_power = np.where(diagnostic_mask, padded_power, 0.0)
    dom_idx = np.unravel_index(int(np.argmax(diagnostic_power)), diagnostic_power.shape)
    dominant_frequency_hz = float(abs(p_f_t[dom_idx[0]]))
    dominant_spatial_frequency = float(abs(p_f_x[dom_idx[1]]))
    fft_lambda_cm = float(1.0 / dominant_spatial_frequency)

    return {
        "eta_incident_px": eta_incident,
        "eta_reflected_px": eta_reflected,
        "incident_sign": incident_sign,
        "incident_direction": incident_direction,
        "pos_direction_energy": pos_energy,
        "neg_direction_energy": neg_energy,
        "dominant_frequency_hz": dominant_frequency_hz,
        "dominant_spatial_frequency_cyc_per_cm": dominant_spatial_frequency,
        "fft_incident_lambda_cm": fft_lambda_cm,
        "f_t": f_t,
        "f_x": f_x,
        "fft_energy": energy,
    }


def reflection_timeseries(
    eta_incident_px: np.ndarray, eta_reflected_px: np.ndarray, fps: float
) -> tuple[pd.DataFrame, dict[str, float]]:
    incident_inst = np.mean(eta_incident_px**2, axis=1)
    reflected_inst = np.mean(eta_reflected_px**2, axis=1)
    rolling = max(5, int(round(0.45 * fps)))
    incident_energy = ndimage.uniform_filter1d(incident_inst, size=rolling, mode="nearest")
    reflected_energy = ndimage.uniform_filter1d(reflected_inst, size=rolling, mode="nearest")
    ratio = reflected_energy / (incident_energy + 1e-9)

    frame_count = len(ratio)
    window_len = max(12, int(round(0.65 * fps)))
    window_len = min(window_len, frame_count)
    best_score = float("inf")
    best_start = 0
    best_mean = float("nan")
    best_std = float("nan")
    for start in range(0, frame_count - window_len + 1):
        values = ratio[start : start + window_len]
        score = float(values.mean() + 0.5 * values.std())
        if score < best_score:
            best_score = score
            best_start = start
            best_mean = float(values.mean())
            best_std = float(values.std())
    best_end = best_start + window_len - 1

    time_s = np.arange(frame_count, dtype=np.float64) / fps
    df = pd.DataFrame(
        {
            "frame": np.arange(frame_count),
            "time_s": time_s,
            "incident_energy_px2": incident_energy,
            "reflected_energy_px2": reflected_energy,
            "reflected_incident_energy_ratio": ratio,
            "in_low_reflection_window": (np.arange(frame_count) >= best_start)
            & (np.arange(frame_count) <= best_end),
        }
    )

    stats = {
        "stable_start_frame": float(best_start),
        "stable_end_frame": float(best_end),
        "stable_start_s": float(best_start / fps),
        "stable_end_s": float(best_end / fps),
        "stable_mean_reflection_ratio": best_mean,
        "stable_std_reflection_ratio": best_std,
        "stable_window_frames": float(window_len),
        "median_reflection_ratio": float(np.median(ratio)),
        "mean_reflection_ratio": float(np.mean(ratio)),
        "max_reflection_ratio": float(np.max(ratio)),
        "min_reflection_ratio": float(np.min(ratio)),
    }
    return df, stats


def peak_spacing_measurements(
    eta_component_px: np.ndarray,
    x_cm: np.ndarray,
    frame_indices: np.ndarray,
    fps: float,
    component_name: str,
    expected_lambda_cm: float | None,
) -> tuple[pd.DataFrame, dict[str, float]]:
    dx_cm = float(np.median(np.diff(x_cm)))
    rows: list[dict[str, float | str | int]] = []
    valid = (x_cm >= 1.5) & (x_cm <= x_cm[-1] - 1.5)
    x_valid = x_cm[valid]

    for frame_idx in frame_indices:
        profile = eta_component_px[frame_idx, valid].astype(np.float64)
        if len(profile) >= 81:
            profile_smooth = signal.savgol_filter(profile, 81, 3, mode="interp")
        else:
            profile_smooth = ndimage.gaussian_filter1d(profile, sigma=3.0)
        prominence = max(0.7, 0.20 * float(np.std(profile_smooth)))
        if expected_lambda_cm is None or not np.isfinite(expected_lambda_cm):
            min_distance_cm = 8.0
        else:
            min_distance_cm = max(7.0, 0.35 * expected_lambda_cm)
        min_distance_px = max(3, int(round(min_distance_cm / dx_cm)))
        peaks, props = find_peaks(profile_smooth, prominence=prominence, distance=min_distance_px)

        for local_idx, (left_peak, right_peak) in enumerate(zip(peaks[:-1], peaks[1:])):
            spacing_cm = float(x_valid[right_peak] - x_valid[left_peak])
            if 10.0 <= spacing_cm <= 45.0:
                rows.append(
                    {
                        "component": component_name,
                        "frame": int(frame_idx),
                        "time_s": float(frame_idx / fps),
                        "left_peak_x_cm": float(x_valid[left_peak]),
                        "right_peak_x_cm": float(x_valid[right_peak]),
                        "spacing_cm": spacing_cm,
                        "left_peak_eta_px": float(profile_smooth[left_peak]),
                        "right_peak_eta_px": float(profile_smooth[right_peak]),
                        "left_peak_prominence_px": float(props["prominences"][local_idx]),
                        "peaks_in_frame": int(len(peaks)),
                    }
                )

    df = pd.DataFrame(rows)
    if df.empty:
        stats = {
            "count": 0.0,
            "median_spacing_cm": float("nan"),
            "mean_spacing_cm": float("nan"),
            "mad_spacing_cm": float("nan"),
            "min_spacing_cm": float("nan"),
            "max_spacing_cm": float("nan"),
        }
        return df, stats

    spacing = df["spacing_cm"].to_numpy(dtype=np.float64)
    median = float(np.median(spacing))
    stats = {
        "count": float(len(spacing)),
        "median_spacing_cm": median,
        "mean_spacing_cm": float(np.mean(spacing)),
        "mad_spacing_cm": float(np.median(np.abs(spacing - median))),
        "min_spacing_cm": float(np.min(spacing)),
        "max_spacing_cm": float(np.max(spacing)),
    }
    return df, stats


def plot_calibration(frame: np.ndarray, calib_points: pd.DataFrame, calibration: dict[str, float], out_path: Path) -> None:
    y1 = int(calibration["ruler_crop_y1"])
    y2 = int(calibration["ruler_crop_y2"])
    crop = frame[y1:y2, :, :]

    fig, axes = plt.subplots(2, 1, figsize=(10.5, 4.8), gridspec_kw={"height_ratios": [1.1, 1.0]})
    axes[0].imshow(crop)
    for _, row in calib_points.iterrows():
        x = float(row["x_px"])
        axes[0].axvline(x, color="#ff2d2d", lw=1.3)
        axes[0].text(x + 5, 8, f'{int(row["ruler_reading_cm"])} cm', color="white", fontsize=9)
    axes[0].set_title("直尺标定诊断：使用可见盒标")
    axes[0].set_axis_off()

    x_pts = calib_points["x_px"].to_numpy()
    y_pts = calib_points["ruler_reading_cm"].to_numpy()
    fit_x = np.linspace(0, frame.shape[1] - 1, 200)
    fit_y = calibration["slope_cm_per_px_signed"] * fit_x + calibration["intercept_cm"]
    axes[1].scatter(x_pts, y_pts, color="#d62728", label="直尺读数点")
    axes[1].plot(fit_x, fit_y, color="#1f77b4", label="线性拟合")
    axes[1].invert_yaxis()
    axes[1].set_xlabel("图像 x (px)")
    axes[1].set_ylabel("直尺读数 (cm)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="best")
    axes[1].text(
        0.02,
        0.06,
        f'px_per_cm = {calibration["px_per_cm"]:.3f}\n'
        f'RMSE = {calibration["fit_rmse_cm"]:.3f} cm\n'
        f'估计标定不确定度 = {calibration["estimated_scale_uncertainty_pct"]:.1f}%',
        transform=axes[1].transAxes,
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "#bbbbbb"},
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_surface_check(frames: np.ndarray, surface_y_px: np.ndarray, out_path: Path) -> None:
    indices = np.unique(np.linspace(0, len(frames) - 1, 5).round().astype(int))
    fig, axes = plt.subplots(len(indices), 1, figsize=(12, 2.0 * len(indices)))
    if len(indices) == 1:
        axes = [axes]
    for ax, idx in zip(axes, indices):
        ax.imshow(frames[idx])
        ax.plot(np.arange(frames.shape[2]), surface_y_px[idx], color="red", lw=1.2)
        ax.set_xlim(0, frames.shape[2] - 1)
        ax.set_ylim(155, 45)
        ax.set_title(f"水线检查：第 {idx} 帧")
        ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_xt_panels(
    eta_px: np.ndarray,
    eta_incident_px: np.ndarray,
    eta_reflected_px: np.ndarray,
    x_cm: np.ndarray,
    time_s: np.ndarray,
    out_path: Path,
) -> None:
    vmax = float(np.nanpercentile(np.abs(eta_px), 98))
    fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True, sharey=True)
    panels = [
        ("原始 eta(x,t)", eta_px),
        ("方向分离：入射分量", eta_incident_px),
        ("方向分离：反射分量", eta_reflected_px),
    ]
    for ax, (title, data) in zip(axes, panels):
        im = ax.imshow(
            data,
            extent=[x_cm[0], x_cm[-1], time_s[-1], time_s[0]],
            aspect="auto",
            cmap="RdBu_r",
            vmin=-vmax,
            vmax=vmax,
        )
        ax.set_ylabel("时间 (s)")
        ax.set_title(title)
        fig.colorbar(im, ax=ax, label="eta (px)")
    axes[-1].set_xlabel("x (cm，按直尺标定的距离)")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_reflection(reflection_df: pd.DataFrame, reflection_stats: dict[str, float], out_path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 5.8), sharex=True)
    t = reflection_df["time_s"]
    axes[0].plot(t, reflection_df["incident_energy_px2"], label="入射能量", color="#1f77b4")
    axes[0].plot(t, reflection_df["reflected_energy_px2"], label="反射能量", color="#d62728")
    axes[0].set_ylabel("能量 (px²)")
    axes[0].legend(loc="best")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(t, reflection_df["reflected_incident_energy_ratio"], color="#2ca02c")
    axes[1].axvspan(
        reflection_stats["stable_start_s"],
        reflection_stats["stable_end_s"],
        color="#7fc97f",
        alpha=0.22,
        label="低反射稳定窗口",
    )
    axes[1].axhline(0.10, color="#555555", ls="--", lw=1.0, label="0.10 参考线")
    axes[1].set_xlabel("时间 (s)")
    axes[1].set_ylabel("反射/入射能量比")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(loc="best")
    axes[1].set_title(
        f'低反射窗口 {reflection_stats["stable_start_s"]:.3f}-{reflection_stats["stable_end_s"]:.3f} s，'
        f'平均比值 {reflection_stats["stable_mean_reflection_ratio"]:.3f}'
    )
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def choose_peak_example(direct_df: pd.DataFrame, direct_lambda_cm: float) -> int:
    if direct_df.empty:
        return 0
    idx = (direct_df["spacing_cm"] - direct_lambda_cm).abs().idxmin()
    return int(direct_df.loc[idx, "frame"])


def plot_peak_measurement(
    frames: np.ndarray,
    surface_y_px: np.ndarray,
    eta_px: np.ndarray,
    eta_incident_px: np.ndarray,
    x_cm: np.ndarray,
    direct_df: pd.DataFrame,
    incident_df: pd.DataFrame,
    direct_lambda_cm: float,
    incident_lambda_cm: float,
    out_path: Path,
) -> None:
    frame_idx = choose_peak_example(direct_df, direct_lambda_cm)
    fig, axes = plt.subplots(3, 1, figsize=(11.5, 8.0), gridspec_kw={"height_ratios": [1.15, 1.0, 1.0]})

    axes[0].imshow(frames[frame_idx])
    axes[0].plot(np.arange(frames.shape[2]), surface_y_px[frame_idx], color="red", lw=1.2, label="提取水线")
    axes[0].set_xlim(0, frames.shape[2] - 1)
    axes[0].set_ylim(155, 45)
    axes[0].set_axis_off()
    axes[0].set_title(f"峰距测量示例：第 {frame_idx} 帧 ({frame_idx / 30.0:.3f} s)")

    for ax, data, df, title, color in [
        (axes[1], eta_px, direct_df, f"直接水线剖面：中位相邻峰距 {direct_lambda_cm:.2f} cm", "#1f77b4"),
        (axes[2], eta_incident_px, incident_df, f"分离后入射剖面：中位相邻峰距 {incident_lambda_cm:.2f} cm", "#d62728"),
    ]:
        profile = data[frame_idx].astype(np.float64)
        smooth = signal.savgol_filter(profile, 81, 3, mode="interp")
        ax.plot(x_cm, smooth, color=color, lw=1.4)
        frame_rows = df[df["frame"] == frame_idx] if not df.empty else pd.DataFrame()
        for _, row in frame_rows.iterrows():
            ax.axvline(row["left_peak_x_cm"], color="#333333", ls=":", lw=1)
            ax.axvline(row["right_peak_x_cm"], color="#333333", ls=":", lw=1)
            y_text = float(np.nanmax(smooth) * 0.88)
            ax.annotate(
                f'{row["spacing_cm"]:.2f} cm',
                xy=((row["left_peak_x_cm"] + row["right_peak_x_cm"]) / 2.0, y_text),
                ha="center",
                fontsize=9,
                bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "#bbbbbb"},
            )
        ax.set_ylabel("eta (px)")
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
    axes[2].set_xlabel("x (cm)")
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def plot_judgement(
    direct_lambda_cm: float,
    direct_unc_cm: float,
    incident_lambda_cm: float,
    incident_unc_cm: float,
    fft_lambda_cm: float,
    diff_cm: float,
    rel_diff_pct: float,
    reflection_stats: dict[str, float],
    final_need_standing: bool,
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.5), gridspec_kw={"width_ratios": [1.0, 1.1]})

    labels = ["直接峰距", "入射剖面峰距", "2D FFT诊断"]
    values = [direct_lambda_cm, incident_lambda_cm, fft_lambda_cm]
    errors = [direct_unc_cm, incident_unc_cm, np.nan]
    colors = ["#4c78a8", "#e45756", "#72b7b2"]
    x = np.arange(len(labels))
    axes[0].bar(x, values, color=colors, alpha=0.9)
    axes[0].errorbar(x[:2], values[:2], yerr=errors[:2], fmt="none", ecolor="#333333", capsize=4)
    axes[0].set_xticks(x, labels, rotation=18)
    axes[0].set_ylabel("波长 / 峰距 (cm)")
    axes[0].set_title("波长来源比较")
    axes[0].grid(True, axis="y", alpha=0.3)

    judgement = "低反射窗口内不需主要驻波修正" if not final_need_standing else "低反射窗口仍建议考虑驻波/反射"
    text = (
        f"判断：{judgement}\n\n"
        f"直接峰距 - 入射剖面 = {diff_cm:+.2f} cm\n"
        f"相对差异 = {rel_diff_pct:.2f}%\n"
        f"低反射窗口平均反射/入射 = {reflection_stats['stable_mean_reflection_ratio']:.3f}\n"
        f"全片中位反射/入射 = {reflection_stats['median_reflection_ratio']:.3f}\n\n"
        "说明：视频短且视场约 49 cm，2D FFT 波长\n"
        "只作为方向/反射诊断；最终波长优先采用\n"
        "低反射窗口的直接峰距与入射剖面峰距。"
    )
    axes[1].axis("off")
    axes[1].text(
        0.02,
        0.92,
        text,
        va="top",
        ha="left",
        fontsize=11,
        linespacing=1.45,
        bbox={"facecolor": "#f7f7f7", "edgecolor": "#cccccc", "boxstyle": "round,pad=0.5"},
    )
    fig.tight_layout()
    fig.savefig(out_path)
    plt.close(fig)


def write_report(
    out_path: Path,
    video_info: dict[str, float],
    calibration: dict[str, float],
    reflection_stats: dict[str, float],
    fft_result: dict[str, object],
    direct_stats: dict[str, float],
    incident_stats: dict[str, float],
    incident_lambda_cm: float,
    final_lambda_cm: float,
    diff_cm: float,
    rel_diff_pct: float,
    final_need_standing: bool,
    full_video_reflection_notice: bool,
) -> None:
    final_judgement = (
        "低反射稳定窗口内不需要把驻波/反射作为主要修正项；"
        "直接峰距与分离后入射剖面峰距一致。"
        if not final_need_standing
        else "低反射窗口内直接峰距与入射剖面仍有明显差异，建议考虑驻波/反射修正。"
    )
    full_notice = (
        "但全片反射能量并不低，尤其非稳定段会影响全帧 FFT 和未分窗读数，因此全片解释仍需考虑反射。"
        if full_video_reflection_notice
        else "全片反射能量整体较低，低反射窗口判断与全片趋势一致。"
    )

    text = f"""# 数据组 {DATA_GROUP} 水波视频驻波/反射分析报告

## 输入与标定

- 输入视频：`{VIDEO_NAME}`
- 视频帧数：{video_info['frames']:.0f} 帧，帧率：{video_info['fps']:.2f} fps，时长：{video_info['duration_s']:.3f} s，分辨率：{video_info['width']:.0f} x {video_info['height']:.0f} px。
- 直尺刻度清楚可见，使用画面中的 210/200/190/180/170 cm 盒标做线性标定；未使用替代比例。
- 标定结果：{calibration['px_per_cm']:.3f} px/cm，{calibration['cm_per_px']:.5f} cm/px；拟合 RMSE {calibration['fit_rmse_cm']:.3f} cm，估计比例不确定度约 {calibration['estimated_scale_uncertainty_pct']:.1f}%。
- 有效视场宽度约 {video_info['field_width_cm']:.2f} cm。

## 方向分离与反射

- 2D FFT 方向能量判定入射方向：{fft_result['incident_direction']}。
- 正/负方向能量：{fft_result['pos_direction_energy']:.3e} / {fft_result['neg_direction_energy']:.3e}。
- 低反射稳定窗口：第 {reflection_stats['stable_start_frame']:.0f}-{reflection_stats['stable_end_frame']:.0f} 帧，即 {reflection_stats['stable_start_s']:.3f}-{reflection_stats['stable_end_s']:.3f} s。
- 低反射窗口平均反射/入射能量比：{reflection_stats['stable_mean_reflection_ratio']:.3f}；全片中位反射/入射能量比：{reflection_stats['median_reflection_ratio']:.3f}，最大值：{reflection_stats['max_reflection_ratio']:.3f}。

## 波长比较

- 低反射窗口直接相邻峰距：{direct_stats['median_spacing_cm']:.2f} cm，MAD {direct_stats['mad_spacing_cm']:.2f} cm，样本数 {direct_stats['count']:.0f}。
- 方向分离后入射剖面相邻峰距：{incident_stats['median_spacing_cm']:.2f} cm，MAD {incident_stats['mad_spacing_cm']:.2f} cm，样本数 {incident_stats['count']:.0f}。
- 最终建议入射波长：约 {final_lambda_cm:.2f} cm。
- 直接峰距与入射剖面差值：{diff_cm:+.2f} cm，相对差异 {rel_diff_pct:.2f}%。
- 全帧 2D FFT 入射波长诊断值：{fft_result['fft_incident_lambda_cm']:.2f} cm，主频约 {fft_result['dominant_frequency_hz']:.2f} Hz。由于视频仅 {video_info['duration_s']:.2f} s、视场只覆盖约 {video_info['field_width_cm'] / final_lambda_cm:.1f} 个最终波长，该 FFT 波长不作为高精度最终值。

## 判断

{final_judgement}{full_notice}

结论：最终读数建议采用约 **{final_lambda_cm:.1f} cm**。在选出的低反射稳定窗口内，驻波/反射不会显著改变峰距读数；若使用全片、晚段或全帧 2D FFT 结果，则必须把反射影响作为诊断限制说明。
"""
    out_path.write_text(text, encoding="utf-8")


def main() -> None:
    setup_matplotlib()
    out_dir = Path(__file__).resolve().parent
    video_path = out_dir / VIDEO_NAME

    frames, fps = read_video(video_path)
    frame_count, height, width, _ = frames.shape
    dt = 1.0 / fps
    time_s = np.arange(frame_count, dtype=np.float64) * dt

    calib_points, calibration = calibrate_from_ruler(frames)
    cm_per_px = float(calibration["cm_per_px"])
    x_px = np.arange(width, dtype=np.float64)
    x_cm = x_px * cm_per_px

    surface_y_px, global_rows = extract_all_surfaces(frames)
    eta_px = make_eta(surface_y_px)
    fft_result = directional_fft(eta_px, fps=fps, dx_cm=cm_per_px)
    eta_incident_px = fft_result["eta_incident_px"]
    eta_reflected_px = fft_result["eta_reflected_px"]

    reflection_df, reflection_stats = reflection_timeseries(eta_incident_px, eta_reflected_px, fps=fps)
    stable_frames = np.arange(
        int(reflection_stats["stable_start_frame"]),
        int(reflection_stats["stable_end_frame"]) + 1,
        dtype=int,
    )

    fft_lambda_cm = float(fft_result["fft_incident_lambda_cm"])
    direct_df, direct_stats = peak_spacing_measurements(
        eta_px,
        x_cm,
        stable_frames,
        fps,
        "direct_raw_low_reflection_window",
        expected_lambda_cm=fft_lambda_cm,
    )
    incident_df, incident_stats = peak_spacing_measurements(
        eta_incident_px,
        x_cm,
        stable_frames,
        fps,
        "direction_filtered_incident_low_reflection_window",
        expected_lambda_cm=fft_lambda_cm,
    )
    if direct_stats["count"] < 3 or incident_stats["count"] < 3:
        raise RuntimeError("低反射窗口内可用峰距样本不足，需人工复核水线或峰值阈值。")

    direct_lambda_cm = float(direct_stats["median_spacing_cm"])
    incident_lambda_cm = float(incident_stats["median_spacing_cm"])
    final_lambda_cm = float(np.median([direct_lambda_cm, incident_lambda_cm]))
    diff_cm = float(direct_lambda_cm - incident_lambda_cm)
    rel_diff_pct = float(abs(diff_cm) / incident_lambda_cm * 100.0)

    calibration_unc_cm = calibration["estimated_scale_uncertainty_pct"] / 100.0 * final_lambda_cm
    direct_unc_cm = float(max(direct_stats["mad_spacing_cm"], calibration_unc_cm))
    incident_unc_cm = float(max(incident_stats["mad_spacing_cm"], calibration_unc_cm))
    final_need_standing = bool(
        rel_diff_pct > 5.0 or float(reflection_stats["stable_mean_reflection_ratio"]) > 0.10
    )
    full_video_reflection_notice = bool(float(reflection_stats["median_reflection_ratio"]) > 0.10)

    plot_calibration(
        frames[int(calibration["calibration_frame"])],
        calib_points,
        calibration,
        out_dir / "ruler_calibration_diagnostic.png",
    )
    plot_surface_check(frames, surface_y_px, out_dir / "surface_extraction_check.png")
    plot_xt_panels(
        eta_px,
        eta_incident_px,
        eta_reflected_px,
        x_cm,
        time_s,
        out_dir / "xt_raw_incident_reflected_panels.png",
    )
    plot_reflection(reflection_df, reflection_stats, out_dir / "reflection_intensity.png")
    plot_peak_measurement(
        frames,
        surface_y_px,
        eta_px,
        eta_incident_px,
        x_cm,
        direct_df,
        incident_df,
        direct_lambda_cm,
        incident_lambda_cm,
        out_dir / "wave_peak_measurement.png",
    )
    plot_judgement(
        direct_lambda_cm,
        direct_unc_cm,
        incident_lambda_cm,
        incident_unc_cm,
        fft_lambda_cm,
        diff_cm,
        rel_diff_pct,
        reflection_stats,
        final_need_standing,
        out_dir / "standing_wave_judgement_cn.png",
    )

    calib_points.to_csv(out_dir / "ruler_calibration_points.csv", index=False, encoding="utf-8-sig")
    reflection_df.to_csv(out_dir / "reflection_ratio_timeseries.csv", index=False, encoding="utf-8-sig")
    direct_df.to_csv(out_dir / "peak_measurements.csv", index=False, encoding="utf-8-sig")
    incident_df.to_csv(out_dir / "incident_peak_measurements.csv", index=False, encoding="utf-8-sig")

    fft_summary = pd.DataFrame(
        [
            {
                "入射方向": fft_result["incident_direction"],
                "正方向能量": fft_result["pos_direction_energy"],
                "负方向能量": fft_result["neg_direction_energy"],
                "主频_Hz": fft_result["dominant_frequency_hz"],
                "FFT诊断空间频率_cyc_per_cm": fft_result["dominant_spatial_frequency_cyc_per_cm"],
                "FFT诊断入射波长_cm": fft_lambda_cm,
                "说明": "短视频/有限视场下仅作方向和诊断，不作为最终高精度波长",
            }
        ]
    )
    fft_summary.to_csv(out_dir / "fft_direction_summary.csv", index=False, encoding="utf-8-sig")

    eta_df = pd.DataFrame(
        {
            "frame": np.repeat(np.arange(frame_count), width),
            "time_s": np.repeat(time_s, width),
            "x_px": np.tile(x_px, frame_count),
            "x_cm": np.tile(x_cm, frame_count),
            "surface_y_px": surface_y_px.reshape(-1),
            "eta_px_up_positive": eta_px.reshape(-1),
            "eta_cm_approx": (eta_px * cm_per_px).reshape(-1),
            "eta_incident_px": eta_incident_px.reshape(-1),
            "eta_reflected_px": eta_reflected_px.reshape(-1),
        }
    )
    eta_df.to_csv(out_dir / "eta_contour_timeseries.csv", index=False, encoding="utf-8-sig")

    np.savez_compressed(
        out_dir / "standing_wave_analysis_data.npz",
        fps=fps,
        time_s=time_s,
        x_px=x_px,
        x_cm=x_cm,
        surface_y_px=surface_y_px,
        global_surface_rows_px=global_rows,
        eta_px=eta_px,
        eta_cm_approx=eta_px * cm_per_px,
        eta_incident_px=eta_incident_px,
        eta_reflected_px=eta_reflected_px,
        reflection_ratio=reflection_df["reflected_incident_energy_ratio"].to_numpy(),
        incident_energy_px2=reflection_df["incident_energy_px2"].to_numpy(),
        reflected_energy_px2=reflection_df["reflected_energy_px2"].to_numpy(),
        calibration_values=np.array(
            [
                calibration["slope_cm_per_px_signed"],
                calibration["intercept_cm"],
                calibration["cm_per_px"],
                calibration["px_per_cm"],
                calibration["fit_rmse_cm"],
                calibration["estimated_scale_uncertainty_pct"],
            ],
            dtype=np.float64,
        ),
    )

    summary = pd.DataFrame(
        [
            {
                "数据组": DATA_GROUP,
                "视频帧数": frame_count,
                "帧率_fps": fps,
                "时长_s": frame_count / fps,
                "宽_px": width,
                "高_px": height,
                "视场宽度_cm": x_cm[-1],
                "px_per_cm": calibration["px_per_cm"],
                "cm_per_px": calibration["cm_per_px"],
                "标定_RMSE_cm": calibration["fit_rmse_cm"],
                "标定估计误差_pct": calibration["estimated_scale_uncertainty_pct"],
                "入射方向": fft_result["incident_direction"],
                "主频_Hz": fft_result["dominant_frequency_hz"],
                "FFT诊断入射波长_cm": fft_lambda_cm,
                "FFT是否作为最终波长": "否，短视频/视场不足，仅作方向和诊断",
                "稳定窗口开始_s": reflection_stats["stable_start_s"],
                "稳定窗口结束_s": reflection_stats["stable_end_s"],
                "稳定窗口平均反射入射能量比": reflection_stats["stable_mean_reflection_ratio"],
                "全片中位反射入射能量比": reflection_stats["median_reflection_ratio"],
                "直接相邻峰距_cm": direct_lambda_cm,
                "直接峰距_MAD_cm": direct_stats["mad_spacing_cm"],
                "直接峰距样本数": direct_stats["count"],
                "分离入射波长_cm": incident_lambda_cm,
                "分离入射波长来源": "低反射窗口方向分离后入射剖面相邻峰距中位数",
                "低反射窗口入射剖面峰距_cm": incident_lambda_cm,
                "入射峰距样本数": incident_stats["count"],
                "最终建议波长_cm": final_lambda_cm,
                "差值_直接减入射_cm": diff_cm,
                "相对差异_pct": rel_diff_pct,
                "是否建议考虑驻波": "低反射窗口内否；全片/FFT诊断需考虑反射"
                if full_video_reflection_notice and not final_need_standing
                else ("是" if final_need_standing else "否"),
                "最终口径说明": f"直接峰距与分离后入射峰距一致，最终取约{final_lambda_cm:.1f} cm；2D FFT值受短视频和视场不足影响，只作诊断。",
            }
        ]
    )
    summary.to_csv(out_dir / "standing_wave_summary_cn.csv", index=False, encoding="utf-8-sig")

    video_info = {
        "frames": float(frame_count),
        "fps": fps,
        "duration_s": frame_count / fps,
        "width": float(width),
        "height": float(height),
        "field_width_cm": float(x_cm[-1]),
    }
    write_report(
        out_dir / "standing_wave_cn_report.md",
        video_info,
        calibration,
        reflection_stats,
        fft_result,
        direct_stats,
        incident_stats,
        incident_lambda_cm,
        final_lambda_cm,
        diff_cm,
        rel_diff_pct,
        final_need_standing,
        full_video_reflection_notice,
    )

    manifest = pd.DataFrame(
        [
            {"file": path.name, "bytes": path.stat().st_size}
            for path in sorted(out_dir.iterdir())
            if path.is_file() and path.name not in {VIDEO_NAME, "analysis_manifest.csv"}
        ]
    )
    manifest.to_csv(out_dir / "analysis_manifest.csv", index=False, encoding="utf-8-sig")

    print("analysis complete")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

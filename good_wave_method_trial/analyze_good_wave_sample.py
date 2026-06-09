# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import ndimage, signal


@dataclass(frozen=True)
class WindowResult:
    start_i: int
    end_i: int
    start_s: float
    end_s: float
    ratio_median: float
    ratio_mean: float
    ratio_std: float


def setup_font() -> None:
    for font_path in [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]:
        if font_path.exists():
            font_manager.fontManager.addfont(str(font_path))
            prop = font_manager.FontProperties(fname=str(font_path))
            plt.rcParams["font.sans-serif"] = [prop.get_name()]
            break
    plt.rcParams["axes.unicode_minus"] = False


def read_video(video_path: Path) -> tuple[np.ndarray, float]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    frames: list[np.ndarray] = []
    while True:
        ok, bgr = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    cap.release()
    if not frames:
        raise RuntimeError(f"No frames read from: {video_path}")
    return np.stack(frames, axis=0), fps


def odd_window(n: int, preferred: int) -> int:
    value = min(preferred, n if n % 2 else n - 1)
    value = max(5, value)
    if value % 2 == 0:
        value -= 1
    return value


def estimate_px_per_cm(frames: np.ndarray) -> tuple[float, dict[str, object]]:
    h, w = frames.shape[1:3]
    sample = np.median(frames[: min(len(frames), 25)], axis=0).astype(np.uint8)
    gray = cv2.cvtColor(sample, cv2.COLOR_RGB2GRAY).astype(float)

    # Search below the water surface and above the lower reflection area.
    y0 = int(0.34 * h)
    y1 = int(0.62 * h)
    band = gray[y0:y1]
    darkness = 255.0 - band
    row_score = ndimage.gaussian_filter1d(darkness.mean(axis=1), 3.0)
    center = int(np.argmax(row_score) + y0)

    estimates: list[float] = []
    rows: list[dict[str, object]] = []
    for half_height in (5, 8, 12, 16):
        a = max(0, center - half_height)
        b = min(h, center + half_height + 1)
        profile = 255.0 - gray[a:b].mean(axis=0)
        profile = profile - ndimage.gaussian_filter1d(profile, 55)
        profile = profile * np.hanning(w)
        spec = np.abs(np.fft.rfft(profile)) ** 2
        freqs = np.fft.rfftfreq(w, d=1.0)
        mask = (freqs >= 1.0 / 38.0) & (freqs <= 1.0 / 20.0)
        period = float("nan")
        strength = 0.0
        if np.any(mask):
            idxs = np.where(mask)[0]
            j = int(idxs[np.argmax(spec[idxs])])
            if freqs[j] > 0:
                period = float(1.0 / freqs[j])
                strength = float(spec[j])
        used = bool(np.isfinite(period) and 24.0 <= period <= 36.0)
        if used:
            estimates.append(period)
        rows.append(
            {
                "ruler_center_y_px": center,
                "strip_y0_px": a,
                "strip_y1_px": b,
                "period_px_per_cm": period,
                "strength": strength,
                "used": used,
            }
        )

    if estimates:
        value = float(np.median(estimates))
        source = "ruler_fft"
    else:
        value = 31.75
        source = "fallback_31.75"
    meta = {
        "px_per_cm": value,
        "source": source,
        "ruler_center_y_px": center,
        "diagnostic_rows": rows,
    }
    return value, meta


def surface_from_red_overlay(frame: np.ndarray, y_bounds: tuple[int, int]) -> tuple[np.ndarray | None, np.ndarray | None]:
    y0, y1 = y_bounds
    roi = frame[y0:y1].astype(np.int16)
    r = roi[:, :, 0]
    g = roi[:, :, 1]
    b = roi[:, :, 2]
    red = (r > 135) & (r > g + 45) & (r > b + 45)
    red = ndimage.binary_opening(red, structure=np.ones((2, 3)))
    xs = np.arange(frame.shape[1])
    ys = np.full(frame.shape[1], np.nan, dtype=np.float32)
    reliability = np.zeros(frame.shape[1], dtype=np.float32)
    for x in range(frame.shape[1]):
        col = np.where(red[:, x])[0]
        if len(col):
            ys[x] = float(np.median(col) + y0)
            reliability[x] = min(1.0, len(col) / 3.0)
    good = np.isfinite(ys)
    if good.sum() < max(80, int(0.35 * frame.shape[1])):
        return None, None
    ys = np.interp(xs, xs[good], ys[good]).astype(np.float32)
    ys = ndimage.median_filter(ys, size=9, mode="nearest")
    win = odd_window(len(ys), 91)
    ys = signal.savgol_filter(ys, win, 3, mode="interp").astype(np.float32)
    reliability = ndimage.gaussian_filter1d(reliability, 7)
    return ys, reliability


def surface_from_green_gradient(frame: np.ndarray, y_bounds: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    y0, y1 = y_bounds
    green = frame[:, :, 1].astype(np.float32)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32)
    score = 0.76 * green + 0.24 * gray
    score = ndimage.gaussian_filter(score, sigma=(1.1, 2.0))
    roi = score[y0:y1]
    grad = np.gradient(roi, axis=0)
    positive = np.maximum(grad, 0)
    k = np.argmax(positive, axis=0)
    strengths = positive[k, np.arange(frame.shape[1])]
    y = (y0 + k).astype(np.float32)

    low = float(np.percentile(strengths, 12))
    high = float(np.percentile(strengths, 90))
    reliability = np.clip((strengths - low) / max(high - low, 1e-6), 0, 1).astype(np.float32)
    weak = strengths < low
    y[weak] = np.nan
    xs = np.arange(frame.shape[1])
    valid = np.isfinite(y)
    if valid.sum() > max(60, int(0.2 * frame.shape[1])):
        y = np.interp(xs, xs[valid], y[valid]).astype(np.float32)
    else:
        y = np.nan_to_num(y, nan=float(np.nanmedian(y))).astype(np.float32)
    y = ndimage.median_filter(y, size=11, mode="nearest")
    y = signal.savgol_filter(y, odd_window(len(y), 101), 3, mode="interp").astype(np.float32)
    return y, reliability


def extract_surfaces(frames: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    h = frames.shape[1]
    y_bounds = (max(55, int(0.08 * h)), min(int(0.29 * h), 210))
    lines: list[np.ndarray] = []
    reliability_rows: list[np.ndarray] = []
    red_used = 0
    for frame in frames:
        line, rel = surface_from_red_overlay(frame, y_bounds)
        if line is not None and rel is not None:
            red_used += 1
        else:
            line, rel = surface_from_green_gradient(frame, y_bounds)
        lines.append(line)
        reliability_rows.append(rel)
    ylines = np.vstack(lines)
    reliability = np.vstack(reliability_rows)

    temporal = ndimage.median_filter(ylines, size=(5, 1), mode="nearest")
    residual = ylines - temporal
    repaired = np.zeros(ylines.shape, dtype=bool)
    for i in range(ylines.shape[0]):
        med = float(np.median(residual[i]))
        mad = float(np.median(np.abs(residual[i] - med)))
        bad = np.abs(residual[i] - med) > max(5.0, 4.5 * mad)
        if np.any(bad):
            ylines[i, bad] = temporal[i, bad]
            repaired[i, bad] = True
    for i in range(ylines.shape[0]):
        ylines[i] = signal.savgol_filter(ylines[i], odd_window(ylines.shape[1], 91), 3, mode="interp")

    meta = {
        "surface_y_bounds_px": list(y_bounds),
        "frames_using_red_overlay": int(red_used),
        "frames_total": int(len(frames)),
        "repaired_fraction": float(repaired.mean()),
        "mean_reliability": float(np.mean(reliability)),
    }
    return ylines.astype(np.float32), reliability.astype(np.float32), meta


def build_eta(
    ylines: np.ndarray,
    px_per_cm: float,
    crop_margin_px: int = 70,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n, w = ylines.shape
    x0 = min(max(crop_margin_px, 0), w // 3)
    x1 = max(w - crop_margin_px, x0 + 10)
    cropped = ylines[:, x0:x1].astype(float)
    xs_px = np.arange(x0, x1, dtype=float)
    reference = np.nanmedian(cropped, axis=0)
    eta_cm = (reference[None, :] - cropped) / px_per_cm
    eta_cm -= np.nanmedian(eta_cm, axis=1, keepdims=True)
    slow = ndimage.gaussian_filter1d(np.nanmedian(eta_cm, axis=0), sigma=90)
    eta_cm -= slow[None, :]
    eta_cm = signal.detrend(eta_cm, axis=1, type="linear")
    x_cm = (xs_px - xs_px[0]) / px_per_cm
    return eta_cm.astype(np.float32), x_cm.astype(np.float32), xs_px.astype(np.float32)


def prep_fft_data(eta: np.ndarray) -> np.ndarray:
    data = np.nan_to_num(eta, nan=0.0).astype(float)
    data = signal.detrend(data, axis=0, type="linear")
    data = signal.detrend(data, axis=1, type="linear")
    data -= data.mean(axis=0, keepdims=True)
    data -= data.mean(axis=1, keepdims=True)
    return data


def directional_separation(
    eta: np.ndarray,
    fps: float,
    dx_cm: float,
    wavelength_band_cm: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    data = prep_fft_data(eta)
    ft = np.fft.fftfreq(data.shape[0], d=1.0 / fps)
    fx = np.fft.fftfreq(data.shape[1], d=dx_cm)
    f_grid, k_grid = np.meshgrid(ft, fx, indexing="ij")
    spectrum = np.fft.fft2(data)
    lo, hi = wavelength_band_cm
    wave_mask = (
        (np.abs(f_grid) >= 0.15)
        & (np.abs(k_grid) >= 1.0 / hi)
        & (np.abs(k_grid) <= 1.0 / lo)
    )
    pos_mask = wave_mask & (f_grid * k_grid < 0)
    neg_mask = wave_mask & (f_grid * k_grid > 0)
    pos_energy = float(np.sum(np.abs(spectrum[pos_mask]) ** 2))
    neg_energy = float(np.sum(np.abs(spectrum[neg_mask]) ** 2))
    incident_positive_x = pos_energy >= neg_energy
    inc_mask = pos_mask if incident_positive_x else neg_mask
    ref_mask = neg_mask if incident_positive_x else pos_mask
    incident = np.real(np.fft.ifft2(spectrum * inc_mask)).astype(np.float32)
    reflected = np.real(np.fft.ifft2(spectrum * ref_mask)).astype(np.float32)

    power = np.where(inc_mask, np.abs(spectrum) ** 2, 0.0)
    if np.max(power) > 0:
        score = power.sum(axis=0)
        valid = np.abs(fx) > 0
        k_abs = np.abs(fx[valid])
        s = score[valid]
        by_k: dict[float, float] = {}
        for k, value in zip(k_abs, s):
            if value <= 0:
                continue
            key = float(np.round(k, 8))
            by_k[key] = by_k.get(key, 0.0) + float(value)
        if by_k:
            ks = np.array(sorted(by_k), dtype=float)
            ss = ndimage.gaussian_filter1d(np.array([by_k[float(k)] for k in ks]), 1.0)
            j = int(np.argmax(ss))
            k = float(ks[j])
            fft_wavelength = float(1.0 / k) if k > 0 else float("nan")
        else:
            fft_wavelength = float("nan")
    else:
        fft_wavelength = float("nan")

    meta = {
        "positive_x_energy": pos_energy,
        "negative_x_energy": neg_energy,
        "incident_direction": "+x/right" if incident_positive_x else "-x/left",
        "reflection_to_incident_energy_ratio_full": min(pos_energy, neg_energy) / max(max(pos_energy, neg_energy), 1e-12),
        "fft_incident_wavelength_cm": fft_wavelength,
        "wavelength_band_cm": list(wavelength_band_cm),
    }
    return incident, reflected, meta


def reflection_timeseries(incident: np.ndarray, reflected: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    inc_e = ndimage.gaussian_filter1d(np.mean(incident**2, axis=1), 1.2)
    ref_e = ndimage.gaussian_filter1d(np.mean(reflected**2, axis=1), 1.2)
    floor = max(float(np.percentile(inc_e, 10)) * 0.15, 1e-12)
    ratio = ref_e / np.maximum(inc_e, floor)
    ratio = ndimage.gaussian_filter1d(ratio, 1.0)
    return inc_e, ref_e, ratio


def choose_low_reflection_window(times: np.ndarray, ratio: np.ndarray, inc_e: np.ndarray, fps: float) -> WindowResult:
    n = len(times)
    win = max(12, int(round(0.75 * fps)))
    if win >= n:
        win = max(8, n // 2)
    ref_amp = max(float(np.percentile(inc_e, 55)), 1e-12)
    best: tuple[float, int, int] | None = None
    for start in range(0, n - win + 1):
        stop = start + win
        r = ratio[start:stop]
        amp = inc_e[start:stop]
        amp_penalty = max(0.0, ref_amp - float(np.median(amp))) / ref_amp
        score = float(np.median(r) + 0.35 * np.std(r) + 0.12 * amp_penalty)
        if best is None or score < best[0]:
            best = (score, start, stop)
    if best is None:
        raise RuntimeError("Could not choose a low-reflection window")
    _, start, stop = best
    r = ratio[start:stop]
    return WindowResult(
        start_i=start,
        end_i=stop,
        start_s=float(times[start]),
        end_s=float(times[stop - 1]),
        ratio_median=float(np.median(r)),
        ratio_mean=float(np.mean(r)),
        ratio_std=float(np.std(r)),
    )


def frame_autocorr_period(row: np.ndarray, dx_cm: float, band_cm: tuple[float, float]) -> tuple[float, float]:
    y = signal.detrend(row.astype(float), type="linear")
    y -= float(np.mean(y))
    den = float(np.dot(y, y))
    if den <= 1e-12:
        return float("nan"), float("nan")
    corr = np.correlate(y, y, mode="full")[len(y) - 1 :] / den
    lags = np.arange(len(corr)) * dx_cm
    mask = (lags >= band_cm[0]) & (lags <= band_cm[1])
    idxs = np.where(mask)[0]
    if idxs.size < 5:
        return float("nan"), float("nan")
    sm = signal.savgol_filter(corr[idxs], odd_window(idxs.size, 51), 3, mode="interp")
    peaks, props = signal.find_peaks(sm, prominence=0.012)
    if len(peaks):
        local = int(peaks[np.argmax(sm[peaks])])
    else:
        local = int(np.argmax(sm))
    idx = int(idxs[local])
    return float(lags[idx]), float(corr[idx])


def estimate_autocorr_periods(
    field: np.ndarray,
    frame_indices: np.ndarray,
    times: np.ndarray,
    dx_cm: float,
    band_cm: tuple[float, float],
    series: str,
) -> tuple[pd.DataFrame, float, float]:
    rows: list[dict[str, object]] = []
    for idx in frame_indices:
        period, strength = frame_autocorr_period(field[int(idx)], dx_cm, band_cm)
        if np.isfinite(period):
            rows.append(
                {
                    "series": series,
                    "frame_local": int(idx),
                    "time_s": float(times[int(idx)]),
                    "period_cm": period,
                    "autocorr_value": strength,
                }
            )
    df = pd.DataFrame(rows)
    if not len(df):
        return df, float("nan"), float("nan")
    med = float(df["period_cm"].median())
    mad = float(np.median(np.abs(df["period_cm"] - med)))
    return df, med, mad


def estimate_peak_spacings(
    field: np.ndarray,
    x_cm: np.ndarray,
    frame_indices: np.ndarray,
    times: np.ndarray,
    band_cm: tuple[float, float],
    period_hint_cm: float,
    series: str,
) -> tuple[pd.DataFrame, float, float]:
    rows: list[dict[str, object]] = []
    dx = float(np.median(np.diff(x_cm)))
    min_dist_cm = band_cm[0] * 0.65
    if np.isfinite(period_hint_cm):
        min_dist_cm = max(min_dist_cm, 0.40 * period_hint_cm)
    min_dist_px = max(5, int(round(min_dist_cm / dx)))
    for idx in frame_indices:
        y = field[int(idx)].astype(float)
        y = y - ndimage.gaussian_filter1d(y, sigma=85)
        y = ndimage.gaussian_filter1d(y, sigma=3)
        prom = max(0.18 * float(np.std(y)), 0.0015)
        for kind, yy in (("crest", y), ("trough", -y)):
            peaks, props = signal.find_peaks(yy, distance=min_dist_px, prominence=prom)
            for a, b in zip(peaks[:-1], peaks[1:]):
                dist = float(x_cm[b] - x_cm[a])
                if band_cm[0] <= dist <= band_cm[1]:
                    rows.append(
                        {
                            "series": series,
                            "kind": kind,
                            "frame_local": int(idx),
                            "time_s": float(times[int(idx)]),
                            "x1_cm": float(x_cm[a]),
                            "x2_cm": float(x_cm[b]),
                            "spacing_cm": dist,
                            "prominence_threshold": prom,
                        }
                    )
    df = pd.DataFrame(rows)
    if not len(df):
        return df, float("nan"), float("nan")
    med = float(df["spacing_cm"].median())
    mad = float(np.median(np.abs(df["spacing_cm"] - med)))
    return df, med, mad


def draw_xt_panels(
    out_path: Path,
    times: np.ndarray,
    x_cm: np.ndarray,
    eta: np.ndarray,
    incident: np.ndarray,
    reflected: np.ndarray,
    win: WindowResult,
    sample_name: str,
) -> None:
    vmax = max(0.01, float(np.nanpercentile(np.abs(eta), 98)))
    fig, axes = plt.subplots(3, 1, figsize=(12.0, 9.0), dpi=170, sharex=True, sharey=True)
    fig.subplots_adjust(left=0.08, right=0.86, top=0.93, bottom=0.08, hspace=0.25)
    panels = [
        ("原始 eta(x,t)", eta),
        ("方向分离：入射分量", incident),
        ("方向分离：反射分量", reflected),
    ]
    im = None
    extent = [float(x_cm[0]), float(x_cm[-1]), float(times[0]), float(times[-1])]
    for ax, (title, data) in zip(axes, panels):
        im = ax.imshow(
            data,
            aspect="auto",
            origin="lower",
            extent=extent,
            cmap="RdBu_r",
            vmin=-vmax,
            vmax=vmax,
            interpolation="bilinear",
        )
        ax.set_ylabel("时间 (s)")
        ax.set_title(title, fontsize=14)
    axes[-1].set_xlabel("水平位置 (cm)")
    cax = fig.add_axes([0.895, 0.16, 0.025, 0.68])
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("相对水面位移 eta (cm)")
    fig.suptitle(f"{sample_name}：水面位移与入射/反射方向分离", fontsize=16)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def draw_reflection_plot(out_path: Path, times: np.ndarray, inc_e: np.ndarray, ref_e: np.ndarray, ratio: np.ndarray, win: WindowResult) -> None:
    fig, ax = plt.subplots(figsize=(10.5, 4.6), dpi=170)
    ax.plot(times, ratio, color="#0057b8", lw=1.8, label="反射/入射能量比")
    ax.axvspan(win.start_s, win.end_s, color="gold", alpha=0.25, label="低反射窗口")
    ax.axhline(win.ratio_median, color="#0057b8", ls="--", lw=1)
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("能量比")
    ax.set_ylim(bottom=0)
    ax2 = ax.twinx()
    ax2.plot(times, inc_e / max(float(np.max(inc_e)), 1e-12), color="#2ca02c", alpha=0.55, label="入射能量(归一化)")
    ax2.plot(times, ref_e / max(float(np.max(ref_e)), 1e-12), color="#d62728", alpha=0.55, label="反射能量(归一化)")
    ax2.set_ylabel("归一化能量")
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc="upper right", fontsize=9)
    ax.set_title(f"反射强度诊断：窗口中位数 {win.ratio_median:.3f}")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def draw_example_overlay(
    out_path: Path,
    frame: np.ndarray,
    surface_y: np.ndarray,
    x_px: np.ndarray,
    x_cm: np.ndarray,
    field_row: np.ndarray,
    spacing_df: pd.DataFrame,
    frame_local: int,
    fps: float,
) -> None:
    fig = plt.figure(figsize=(12, 7.2), dpi=170)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.25, 1.0], hspace=0.25)
    ax0 = fig.add_subplot(gs[0])
    ax0.imshow(frame)
    ax0.plot(x_px, surface_y, color="#ff2d55", lw=1.4)
    rows = spacing_df[spacing_df["frame_local"] == frame_local] if len(spacing_df) else pd.DataFrame()
    rows = rows[rows["kind"] == "crest"] if len(rows) else rows
    for _, r in rows.head(5).iterrows():
        x1p = float(r["x1_cm"]) * (x_px[-1] - x_px[0]) / max(float(x_cm[-1] - x_cm[0]), 1e-9) + x_px[0]
        x2p = float(r["x2_cm"]) * (x_px[-1] - x_px[0]) / max(float(x_cm[-1] - x_cm[0]), 1e-9) + x_px[0]
        y_mid = float(np.interp((x1p + x2p) / 2.0, x_px, surface_y))
        ax0.plot([x1p, x2p], [y_mid - 18, y_mid - 18], color="yellow", lw=2.0)
        ax0.text((x1p + x2p) / 2, y_mid - 24, f"{float(r['spacing_cm']):.2f} cm", color="yellow", ha="center", fontsize=9, weight="bold")
    ax0.set_xlim(40, frame.shape[1] - 40)
    ax0.set_ylim(185, 50)
    ax0.axis("off")
    ax0.set_title(f"示例帧：frame {frame_local}, t={frame_local / fps:.2f}s")

    ax1 = fig.add_subplot(gs[1])
    y = field_row - ndimage.gaussian_filter1d(field_row, sigma=85)
    y = ndimage.gaussian_filter1d(y, sigma=3)
    ax1.plot(x_cm, y, color="#111111", lw=1.25)
    for _, r in rows.head(5).iterrows():
        ax1.axvline(float(r["x1_cm"]), color="gold", lw=0.9, alpha=0.85)
        ax1.axvline(float(r["x2_cm"]), color="gold", lw=0.9, alpha=0.85)
    ax1.axhline(0, color="0.7", lw=0.8)
    ax1.set_xlabel("水平位置 (cm)")
    ax1.set_ylabel("eta (cm)")
    ax1.set_title("同一帧空间剖面与波峰间距")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--name", default="sample")
    parser.add_argument("--band-low", type=float, default=5.0)
    parser.add_argument("--band-high", type=float, default=15.0)
    parser.add_argument("--px-per-cm", type=float, default=None)
    args = parser.parse_args()

    setup_font()
    args.out.mkdir(parents=True, exist_ok=True)
    frames, fps = read_video(args.video)
    if args.px_per_cm is None:
        px_per_cm, cal_meta = estimate_px_per_cm(frames)
    else:
        px_per_cm = float(args.px_per_cm)
        _, estimated_meta = estimate_px_per_cm(frames)
        cal_meta = {
            "px_per_cm": px_per_cm,
            "source": "cli_override",
            "auto_estimate_for_reference": estimated_meta,
        }
    surfaces_full, reliability, surface_meta = extract_surfaces(frames)
    eta, x_cm, x_px = build_eta(surfaces_full, px_per_cm)
    crop_x0 = int(round(float(x_px[0])))
    crop_x1 = int(round(float(x_px[-1]))) + 1
    surfaces = surfaces_full[:, crop_x0:crop_x1]

    times = np.arange(len(frames), dtype=float) / fps
    dx_cm = float(np.median(np.diff(x_cm)))
    band = (float(args.band_low), float(args.band_high))
    incident, reflected, fft_meta = directional_separation(eta, fps, dx_cm, band)
    inc_e, ref_e, ratio = reflection_timeseries(incident, reflected)
    win = choose_low_reflection_window(times, ratio, inc_e, fps)
    frame_indices = np.arange(win.start_i, win.end_i)

    direct_ac, direct_period, direct_period_mad = estimate_autocorr_periods(eta, frame_indices, times, dx_cm, band, "direct_raw")
    inc_ac, inc_period, inc_period_mad = estimate_autocorr_periods(incident, frame_indices, times, dx_cm, band, "incident_separated")
    period_hint = float(np.nanmedian([v for v in [direct_period, inc_period, fft_meta["fft_incident_wavelength_cm"]] if np.isfinite(v)]))
    direct_spacing, direct_med, direct_mad = estimate_peak_spacings(eta, x_cm, frame_indices, times, band, period_hint, "direct_raw")
    inc_spacing, inc_med, inc_mad = estimate_peak_spacings(incident, x_cm, frame_indices, times, band, period_hint, "incident_separated")

    ac_df = pd.concat([direct_ac, inc_ac], ignore_index=True)
    spacing_df = pd.concat([direct_spacing, inc_spacing], ignore_index=True)
    ac_df.to_csv(args.out / "autocorr_periods.csv", index=False, encoding="utf-8-sig")
    spacing_df.to_csv(args.out / "peak_spacing_measurements.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(eta, columns=[f"x_{v:.3f}_cm" for v in x_cm]).assign(time_s=times).to_csv(
        args.out / "eta_xt_surface_cm.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(
        {
            "frame": np.arange(len(times)),
            "time_s": times,
            "incident_energy": inc_e,
            "reflected_energy": ref_e,
            "reflection_to_incident_ratio": ratio,
            "in_low_reflection_window": (np.arange(len(times)) >= win.start_i) & (np.arange(len(times)) < win.end_i),
        }
    ).to_csv(args.out / "reflection_time_series.csv", index=False, encoding="utf-8-sig")

    draw_xt_panels(args.out / "xt_raw_incident_reflected_panels.png", times, x_cm, eta, incident, reflected, win, args.name)
    draw_reflection_plot(args.out / "reflection_strength.png", times, inc_e, ref_e, ratio, win)
    if len(inc_spacing):
        chosen_frame = int(inc_spacing.groupby("frame_local").size().sort_values(ascending=False).index[0])
        chosen_df = inc_spacing
        chosen_field = incident
    elif len(direct_spacing):
        chosen_frame = int(direct_spacing.groupby("frame_local").size().sort_values(ascending=False).index[0])
        chosen_df = direct_spacing
        chosen_field = eta
    else:
        chosen_frame = int((win.start_i + win.end_i) // 2)
        chosen_df = spacing_df
        chosen_field = eta
    draw_example_overlay(
        args.out / "wave_peak_measurement.png",
        frames[chosen_frame],
        surfaces_full[chosen_frame, crop_x0:crop_x1],
        x_px,
        x_cm,
        chosen_field[chosen_frame],
        chosen_df,
        chosen_frame,
        fps,
    )

    summary = {
        "sample": args.name,
        "input_video": str(args.video),
        "output_dir": str(args.out),
        "frames": int(len(frames)),
        "fps": float(fps),
        "duration_s": float(len(frames) / fps),
        "width_px": int(frames.shape[2]),
        "height_px": int(frames.shape[1]),
        "px_per_cm": float(px_per_cm),
        "px_per_cm_source": cal_meta["source"],
        "analysis_width_cm": float(x_cm[-1] - x_cm[0]),
        "wavelength_band_cm": list(band),
        "low_reflection_window_s": [win.start_s, win.end_s],
        "low_reflection_ratio_median": win.ratio_median,
        "low_reflection_ratio_mean": win.ratio_mean,
        "fft_incident_wavelength_cm": fft_meta["fft_incident_wavelength_cm"],
        "incident_direction": fft_meta["incident_direction"],
        "full_reflection_to_incident_energy_ratio": fft_meta["reflection_to_incident_energy_ratio_full"],
        "direct_autocorr_wavelength_cm": direct_period,
        "direct_autocorr_mad_cm": direct_period_mad,
        "incident_autocorr_wavelength_cm": inc_period,
        "incident_autocorr_mad_cm": inc_period_mad,
        "direct_peak_spacing_median_cm": direct_med,
        "direct_peak_spacing_mad_cm": direct_mad,
        "direct_peak_spacing_n": int(len(direct_spacing)),
        "incident_peak_spacing_median_cm": inc_med,
        "incident_peak_spacing_mad_cm": inc_mad,
        "incident_peak_spacing_n": int(len(inc_spacing)),
        "surface_extraction": surface_meta,
        "calibration": cal_meta,
        "method_notes": [
            "Waterline extracted per frame from the visible red surface overlay, falling back to green-edge detection.",
            "eta(x,t) is relative vertical waterline displacement after per-frame and slow spatial detrending.",
            "Incident/reflected components are separated by 2D FFT sign of temporal frequency times spatial wavenumber.",
            "Wavelength estimates use low-reflection-window autocorrelation and adjacent peak/trough spacings.",
        ],
    }
    write_json(args.out / "trial_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

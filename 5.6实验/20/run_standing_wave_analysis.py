# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from scipy import ndimage, signal


ROOT = Path(__file__).resolve().parent
VIDEO_NAME = "ff6a1e97ef837bbe07835f23e14b277f.mp4"
DATA_GROUP = "20"
X0_PX = 70
X1_MARGIN_PX = 70


@dataclass
class Calibration:
    px_per_cm: float
    px_per_cm_std: float
    ruler_y0: int
    ruler_y1: int
    label_px_per_cm: float
    tick_period_fft_px: float
    tick_period_ac_px: float
    tick_kind: str
    label_positions_px: np.ndarray
    label_values_cm: np.ndarray
    fit_residual_px: np.ndarray
    fit_rmse_px: float


@dataclass
class WindowResult:
    start_i: int
    end_i: int
    start_s: float
    end_s: float
    ratio_median: float
    ratio_mean: float
    ratio_std: float


def setup_font() -> None:
    candidates = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if Path(path).exists():
            font_manager.fontManager.addfont(path)
            prop = font_manager.FontProperties(fname=path)
            plt.rcParams["font.sans-serif"] = [prop.get_name()]
            break
    plt.rcParams["axes.unicode_minus"] = False


def load_video() -> tuple[np.ndarray, float]:
    os.chdir(ROOT)
    cap = cv2.VideoCapture(VIDEO_NAME)
    if not cap.isOpened():
        raise RuntimeError(f"无法打开视频：{VIDEO_NAME}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    frames: list[np.ndarray] = []
    while True:
        ok, frame_bgr = cap.read()
        if not ok:
            break
        frames.append(frame_bgr[:, :, ::-1].copy())
    cap.release()
    if not frames:
        raise RuntimeError("视频没有成功读取任何帧")
    return np.stack(frames, axis=0), fps


def valid_frame_mask(frames: np.ndarray) -> np.ndarray:
    means = frames.mean(axis=(1, 2, 3))
    stds = frames.std(axis=(1, 2, 3))
    return (means > 10.0) & (stds > 5.0)


def find_ruler_band(gray: np.ndarray) -> tuple[int, int]:
    h = gray.shape[0]
    search0 = int(h * 0.68)
    search1 = int(h * 0.92)
    search = gray[search0:search1]
    gy = np.abs(np.gradient(search.astype(float), axis=0))
    score = ndimage.gaussian_filter1d(gy.mean(axis=1), 2.0)
    y_mid = int(np.argmax(score) + search0)
    y0 = max(y_mid - 45, 0)
    y1 = min(y_mid + 22, h)
    return y0, y1


def _best_decade_sequence(peaks: np.ndarray) -> np.ndarray:
    peaks = np.asarray(sorted(float(v) for v in peaks), dtype=float)
    if len(peaks) < 5:
        return peaks
    candidates: list[tuple[float, int, np.ndarray]] = []
    for length in (6, 5):
        if len(peaks) < length:
            continue
        for start in range(0, len(peaks) - length + 1):
            seq = peaks[start : start + length]
            diffs = np.diff(seq)
            if np.all((diffs > 175) & (diffs < 275)):
                score = float(np.std(diffs) / max(np.mean(diffs), 1e-9))
                candidates.append((score, -length, seq))
    if not candidates:
        return peaks[: min(len(peaks), 6)]
    candidates.sort(key=lambda row: (row[0], row[1]))
    return candidates[0][2]


def calibrate_from_ruler(frames: np.ndarray) -> Calibration:
    med = np.median(frames[: min(len(frames), 30)], axis=0).astype(np.uint8)
    gray = cv2.cvtColor(med, cv2.COLOR_RGB2GRAY).astype(float)
    y0, y1 = find_ruler_band(gray)

    strip = gray[y0:y1, :]
    darkness = 255.0 - strip
    profile = darkness.mean(axis=0)

    # Broad dark peaks are the boxed 10 cm labels. In this video the visible
    # sequence is 210, 200, 190, 180, 170, 160 cm from left to right.
    broad = ndimage.gaussian_filter1d(profile, 14) - ndimage.gaussian_filter1d(profile, 55)
    peaks, props = signal.find_peaks(
        broad,
        distance=120,
        prominence=max(float(np.std(broad)) * 0.45, 1.5),
        width=(18, 90),
    )
    widths = props.get("widths", np.zeros_like(peaks, dtype=float))
    label_centers = peaks[(peaks > 30) & (peaks < gray.shape[1] - 25) & (widths >= 18)].astype(float)
    label_centers = _best_decade_sequence(label_centers)
    if len(label_centers) < 5:
        raise RuntimeError("直尺刻度可见，但未能稳定识别足够的十厘米标号。")
    label_values = np.array([210.0, 200.0, 190.0, 180.0, 170.0, 160.0], dtype=float)[: len(label_centers)]

    coef = np.polyfit(label_values, label_centers, 1)
    label_px_per_cm = abs(float(coef[0]))
    fit = np.polyval(coef, label_values)
    residual = label_centers - fit
    fit_rmse = float(np.sqrt(np.mean(residual**2)))

    hp = profile - ndimage.gaussian_filter1d(profile, 8)
    x = hp - np.mean(hp)
    freq = np.fft.rfftfreq(len(x), d=1.0)
    power = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    fft_mask = (freq > 1 / 32.0) & (freq < 1 / 18.0)
    tick_period_fft = float("nan")
    if np.any(fft_mask):
        tick_period_fft = float(1.0 / freq[fft_mask][int(np.argmax(power[fft_mask]))])

    ac = np.correlate(x, x, mode="full")[len(x) - 1 :]
    ac = ac / max(float(ac[0]), 1e-9)
    lags = np.arange(18, 32)
    tick_period_ac = float(lags[int(np.argmax(ac[lags]))])

    candidates = [label_px_per_cm]
    weights = [2.5]
    if np.isfinite(tick_period_fft) and 18.0 <= tick_period_fft <= 32.0:
        candidates.append(tick_period_fft)
        weights.append(1.5)
    if np.isfinite(tick_period_ac) and 18.0 <= tick_period_ac <= 32.0:
        candidates.append(tick_period_ac)
        weights.append(1.0)
    px_per_cm = float(np.average(candidates, weights=weights))
    px_per_cm_std = float(max(np.std(candidates), fit_rmse / 10.0, 0.05))

    return Calibration(
        px_per_cm=px_per_cm,
        px_per_cm_std=px_per_cm_std,
        ruler_y0=y0,
        ruler_y1=y1,
        label_px_per_cm=label_px_per_cm,
        tick_period_fft_px=tick_period_fft,
        tick_period_ac_px=tick_period_ac,
        tick_kind="直尺 1 cm 周期刻度，210--160 cm 标号校验",
        label_positions_px=label_centers,
        label_values_cm=label_values,
        fit_residual_px=residual,
        fit_rmse_px=fit_rmse,
    )


def extract_surface_y(frame: np.ndarray) -> tuple[np.ndarray, int]:
    green = frame[:, :, 1].astype(np.float32)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY).astype(np.float32)
    score_img = 0.72 * green + 0.28 * gray
    smooth = ndimage.gaussian_filter(score_img, sigma=(1.2, 2.2))
    y0, y1 = 55, 160
    roi = smooth[y0:y1, :]
    grad_y = np.gradient(roi, axis=0)

    row_score = ndimage.gaussian_filter1d(grad_y[:, 60:1220].mean(axis=1), sigma=2.0)
    global_y = y0 + int(np.argmax(row_score))
    lo = max(0, global_y - y0 - 35)
    hi = min(roi.shape[0], global_y - y0 + 38)

    ys = np.empty(frame.shape[1], dtype=np.float32)
    local = grad_y[lo:hi]
    for x in range(frame.shape[1]):
        ys[x] = y0 + lo + int(np.argmax(local[:, x]))

    med = ndimage.median_filter(ys, size=17, mode="nearest")
    bad = np.abs(ys - med) > 10.0
    ys[bad] = med[bad]
    ys = ndimage.median_filter(ys, size=9, mode="nearest")
    window = min(81, len(ys) // 2 * 2 - 1)
    if window >= 21:
        ys = signal.savgol_filter(ys, window, 3, mode="interp")
    else:
        ys = ndimage.gaussian_filter1d(ys, sigma=3)
    return ys.astype(np.float32), global_y


def extract_surface(frames: np.ndarray, px_per_cm: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    surfaces = []
    global_rows = []
    for frame in frames:
        surface, global_y = extract_surface_y(frame)
        surfaces.append(surface)
        global_rows.append(global_y)
    surface_all = np.stack(surfaces, axis=0)
    global_rows_arr = np.asarray(global_rows, dtype=float)

    x0 = X0_PX
    x1 = frames.shape[2] - X1_MARGIN_PX
    surface = surface_all[:, x0:x1].astype(float)
    xs_px = np.arange(x0, x1, dtype=float)

    mean_y = np.nanmedian(surface, axis=0)
    eta_cm = (mean_y[None, :] - surface) / px_per_cm
    eta_cm -= np.nanmedian(eta_cm, axis=1, keepdims=True)
    eta_cm -= ndimage.gaussian_filter1d(np.nanmedian(eta_cm, axis=0), sigma=90)[None, :]
    eta_cm = signal.detrend(eta_cm, axis=1, type="linear")
    x_cm = (xs_px - xs_px[0]) / px_per_cm
    return surface, eta_cm, x_cm, global_rows_arr


def _prep_fft_data(eta_cm: np.ndarray) -> np.ndarray:
    data = np.nan_to_num(eta_cm, nan=0.0)
    data = signal.detrend(data, axis=0, type="linear")
    data = signal.detrend(data, axis=1, type="linear")
    data -= data.mean(axis=0, keepdims=True)
    data -= data.mean(axis=1, keepdims=True)
    return data


def dominant_fft_peak(data: np.ndarray, fps: float, dx_cm: float, incident_positive_x: bool) -> dict[str, float]:
    n_t, n_x = data.shape
    pad_t = 2 ** int(math.ceil(math.log2(max(n_t * 4, 16))))
    pad_x = 2 ** int(math.ceil(math.log2(max(n_x * 4, 16))))
    window = np.hanning(n_t)[:, None] * np.hanning(n_x)[None, :]
    F = np.fft.fft2(data * window, s=(pad_t, pad_x))
    ft = np.fft.fftfreq(pad_t, d=1.0 / fps)
    fx = np.fft.fftfreq(pad_x, d=dx_cm)
    FT, FX = np.meshgrid(ft, fx, indexing="ij")
    direction_mask = (FT * FX < 0) if incident_positive_x else (FT * FX > 0)
    mask = direction_mask & (np.abs(FT) >= 0.45) & (np.abs(FX) >= 1 / 90.0) & (np.abs(FX) <= 1 / 8.0)
    power = np.where(mask, np.abs(F) ** 2, 0.0)
    if np.max(power) <= 0:
        return {
            "fft_frequency_hz": float("nan"),
            "fft_wavenumber_cyc_per_cm": float("nan"),
            "fft_wavelength_cm": float("nan"),
        }
    idx = np.unravel_index(int(np.argmax(power)), power.shape)
    f_hz = abs(float(FT[idx]))
    k = abs(float(FX[idx]))
    return {
        "fft_frequency_hz": f_hz,
        "fft_wavenumber_cyc_per_cm": k,
        "fft_wavelength_cm": float(1.0 / k) if k > 0 else float("nan"),
    }


def directional_separation(eta_cm: np.ndarray, fps: float, dx_cm: float) -> tuple[np.ndarray, np.ndarray, dict[str, float | bool]]:
    data = _prep_fft_data(eta_cm)
    ft = np.fft.fftfreq(data.shape[0], d=1.0 / fps)
    fx = np.fft.fftfreq(data.shape[1], d=dx_cm)
    F = np.fft.fft2(data)
    FT, FX = np.meshgrid(ft, fx, indexing="ij")
    wave_mask = (np.abs(FT) >= 0.45) & (np.abs(FX) >= 1 / 90.0) & (np.abs(FX) <= 1 / 8.0)

    pos_mask = wave_mask & ((FT * FX) < 0)  # +x/right
    neg_mask = wave_mask & ((FT * FX) > 0)  # -x/left
    pos_energy = float(np.sum(np.abs(F[pos_mask]) ** 2))
    neg_energy = float(np.sum(np.abs(F[neg_mask]) ** 2))
    incident_positive_x = pos_energy >= neg_energy
    inc_mask = pos_mask if incident_positive_x else neg_mask
    ref_mask = neg_mask if incident_positive_x else pos_mask

    inc = np.real(np.fft.ifft2(F * inc_mask))
    ref = np.real(np.fft.ifft2(F * ref_mask))
    dom = dominant_fft_peak(data, fps, dx_cm, incident_positive_x)
    meta: dict[str, float | bool] = {
        "positive_x_energy": pos_energy,
        "negative_x_energy": neg_energy,
        "incident_positive_x": incident_positive_x,
        **dom,
    }
    return inc, ref, meta


def reflection_timeseries(inc: np.ndarray, ref: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    inc_e = np.mean(inc**2, axis=1)
    ref_e = np.mean(ref**2, axis=1)
    inc_e = ndimage.gaussian_filter1d(inc_e, sigma=1.5)
    ref_e = ndimage.gaussian_filter1d(ref_e, sigma=1.5)
    floor = max(float(np.percentile(inc_e, 10)) * 0.15, 1e-10)
    ratio = ref_e / np.maximum(inc_e, floor)
    ratio = ndimage.gaussian_filter1d(ratio, sigma=1.2)
    return inc_e, ref_e, ratio


def choose_low_reflection_window(times: np.ndarray, ratio: np.ndarray, inc_e: np.ndarray, fps: float) -> WindowResult:
    n = len(times)
    win = max(int(round(0.75 * fps)), 12)
    if win >= n:
        win = max(8, n // 2)
    best: tuple[float, int, int] | None = None
    ref_amp = max(float(np.percentile(inc_e, 55)), 1e-12)
    for s in range(0, n - win + 1):
        e = s + win
        r = ratio[s:e]
        amp = inc_e[s:e]
        amp_penalty = max(0.0, ref_amp - float(np.median(amp))) / ref_amp
        score = float(np.median(r) + 0.35 * np.std(r) + 0.12 * amp_penalty)
        if best is None or score < best[0]:
            best = (score, s, e)
    if best is None:
        raise RuntimeError("无法选择低反射窗口")
    _, s, e = best
    r = ratio[s:e]
    return WindowResult(
        start_i=s,
        end_i=e,
        start_s=float(times[s]),
        end_s=float(times[e - 1]),
        ratio_median=float(np.median(r)),
        ratio_mean=float(np.mean(r)),
        ratio_std=float(np.std(r)),
    )


def estimate_peak_distances(
    field: np.ndarray,
    x_cm: np.ndarray,
    frame_indices: np.ndarray,
    fps: float,
    label: str,
    min_dist_cm: float,
    max_dist_cm: float = 58.0,
    prominence_fraction: float = 0.28,
) -> tuple[pd.DataFrame, float, float, int, int]:
    rows: list[dict[str, float | int | str]] = []
    dx = float(np.median(np.diff(x_cm)))
    min_dist_px = max(5, int(round(min_dist_cm / dx)))
    for ti in frame_indices:
        y0 = field[int(ti)].copy()
        y = y0 - ndimage.gaussian_filter1d(y0, sigma=90)
        y = ndimage.gaussian_filter1d(y, sigma=4)
        prom = max(prominence_fraction * float(np.nanstd(y)), 0.0025)
        for polarity, yy in (("crest", y), ("trough", -y)):
            peaks, _ = signal.find_peaks(yy, distance=min_dist_px, prominence=prom)
            if len(peaks) < 2:
                continue
            for a, b in zip(peaks[:-1], peaks[1:]):
                dist = float(x_cm[b] - x_cm[a])
                if min_dist_cm <= dist <= max_dist_cm:
                    rows.append(
                        {
                            "series": label,
                            "polarity": polarity,
                            "frame": int(ti),
                            "time_s": float(int(ti) / fps),
                            "x1_cm": float(x_cm[a]),
                            "x2_cm": float(x_cm[b]),
                            "distance_cm": dist,
                            "peak1_eta_cm": float(y[a]),
                            "peak2_eta_cm": float(y[b]),
                        }
                    )
    df = pd.DataFrame(rows)
    if len(df):
        med = float(df["distance_cm"].median())
        mad = float(np.median(np.abs(df["distance_cm"] - med)))
        frame_count = int(df["frame"].nunique())
    else:
        med = float("nan")
        mad = float("nan")
        frame_count = 0
    return df, med, mad, int(len(df)), frame_count


def estimate_spatial_periods(
    field: np.ndarray,
    x_cm: np.ndarray,
    frame_indices: np.ndarray,
    fps: float,
    label: str,
    min_period_cm: float = 14.0,
    max_period_cm: float = 45.0,
) -> tuple[pd.DataFrame, float, float, int]:
    rows: list[dict[str, float | int | str]] = []
    dx = float(np.median(np.diff(x_cm)))
    lag_min = max(3, int(round(min_period_cm / dx)))
    lag_max = min(len(x_cm) - 2, int(round(max_period_cm / dx)))
    if lag_max <= lag_min:
        return pd.DataFrame(), float("nan"), float("nan"), 0

    for ti in frame_indices:
        y0 = field[int(ti)].copy()
        y = y0 - ndimage.gaussian_filter1d(y0, sigma=90)
        y = ndimage.gaussian_filter1d(y, sigma=4)
        y = y - float(np.mean(y))
        ac = np.correlate(y, y, mode="full")[len(y) - 1 :]
        if ac[0] <= 1e-12:
            continue
        ac = ac / ac[0]
        lags = np.arange(lag_min, lag_max)
        search = ac[lags]
        peaks, _ = signal.find_peaks(search, distance=max(3, int(round(5.0 / dx))), prominence=0.018)
        if len(peaks) == 0:
            continue
        best = int(peaks[np.argmax(search[peaks])])
        lag = int(lags[best])
        rows.append(
            {
                "series": label,
                "frame": int(ti),
                "time_s": float(int(ti) / fps),
                "period_cm": float(lag * dx),
                "autocorr_value": float(ac[lag]),
            }
        )

    df = pd.DataFrame(rows)
    if len(df):
        med = float(df["period_cm"].median())
        mad = float(np.median(np.abs(df["period_cm"] - med)))
    else:
        med = float("nan")
        mad = float("nan")
    return df, med, mad, int(len(df))


def summarize_distance_df(df: pd.DataFrame) -> tuple[float, float, int, int]:
    if len(df):
        med = float(df["distance_cm"].median())
        mad = float(np.median(np.abs(df["distance_cm"] - med)))
        return med, mad, int(len(df)), int(df["frame"].nunique())
    return float("nan"), float("nan"), 0, 0


def draw_ruler_diagnostic(frames: np.ndarray, cal: Calibration) -> None:
    img = frames[0]
    crop_y0 = max(cal.ruler_y0 - 24, 0)
    crop_y1 = min(cal.ruler_y1 + 45, img.shape[0])
    fig, ax = plt.subplots(figsize=(12, 3.5), dpi=170)
    ax.imshow(img[crop_y0:crop_y1])
    for x, cm, res in zip(cal.label_positions_px, cal.label_values_cm, cal.fit_residual_px):
        ax.axvline(x, color="#ff3b30", lw=1.15)
        ax.text(x + 4, 14, f"{cm:.0f} cm\n残差 {res:+.1f}px", color="#ff3b30", fontsize=8, weight="bold")
    ax.set_xlim(0, img.shape[1])
    ax.set_yticks([])
    ax.set_xlabel("x 像素")
    ax.set_title(
        f"直尺标定诊断：{cal.px_per_cm:.3f} px/cm；"
        f"标号拟合 {cal.label_px_per_cm:.3f}，周期FFT {cal.tick_period_fft_px:.3f}，自相关 {cal.tick_period_ac_px:.3f}"
    )
    fig.tight_layout()
    fig.savefig(ROOT / "ruler_calibration_diagnostic.png")
    plt.close(fig)


def draw_surface_check(frames: np.ndarray, surface: np.ndarray, x_cm: np.ndarray, px_per_cm: float, fps: float) -> None:
    n = len(frames)
    idxs = np.linspace(0, n - 1, 8, dtype=int)
    fig, axes = plt.subplots(4, 2, figsize=(10.5, 10), dpi=150)
    x_px = x_cm * px_per_cm + X0_PX
    for ax, idx in zip(axes.ravel(), idxs):
        ax.imshow(frames[idx])
        ax.plot(x_px, surface[idx], color="#ff2d55", lw=1.2)
        ax.set_xlim(35, frames.shape[2] - 35)
        ax.set_ylim(165, 55)
        ax.set_title(f"帧 {idx} / {idx / fps:.2f} s")
        ax.axis("off")
    fig.suptitle("水线提取检查：粉色线为逐帧提取的水面轮廓", y=0.995)
    fig.tight_layout()
    fig.savefig(ROOT / "waterline_extraction_check.png")
    plt.close(fig)


def draw_xt_panels(times: np.ndarray, x_cm: np.ndarray, eta: np.ndarray, inc: np.ndarray, ref: np.ndarray, win: WindowResult) -> None:
    vmax = float(np.nanpercentile(np.abs(eta), 98))
    vmax = max(vmax, 0.01)
    fig, axes = plt.subplots(3, 1, figsize=(11.5, 8.5), dpi=160, sharex=True, sharey=True)
    fig.subplots_adjust(left=0.075, right=0.86, top=0.91, bottom=0.08, hspace=0.34)
    panels = [("原始 eta(x,t)", eta), ("2D FFT 方向分离：入射分量", inc), ("2D FFT 方向分离：反射分量", ref)]
    im = None
    for ax, (title, data) in zip(axes, panels):
        im = ax.imshow(
            data,
            aspect="auto",
            origin="lower",
            extent=[x_cm[0], x_cm[-1], times[0], times[-1]],
            cmap="RdBu_r",
            vmin=-vmax,
            vmax=vmax,
        )
        ax.axhspan(win.start_s, win.end_s, color="gold", alpha=0.18, lw=0)
        ax.set_ylabel("t (s)")
        ax.set_title(title)
    axes[-1].set_xlabel("x (cm)")
    cax = fig.add_axes([0.885, 0.15, 0.022, 0.70])
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("eta (cm)")
    fig.suptitle("x-t 图与入射/反射方向分离（黄色为低反射稳定窗口）", y=0.985)
    fig.savefig(ROOT / "xt_raw_incident_reflected_panels.png")
    plt.close(fig)


def draw_reflection(times: np.ndarray, inc_e: np.ndarray, ref_e: np.ndarray, ratio: np.ndarray, win: WindowResult) -> None:
    fig, ax1 = plt.subplots(figsize=(10.2, 4.7), dpi=160)
    ax1.plot(times, ratio, color="#0057b8", lw=1.8, label="反射/入射能量比")
    ax1.axvspan(win.start_s, win.end_s, color="gold", alpha=0.25, label="低反射稳定窗口")
    ax1.axhline(win.ratio_median, color="#0057b8", ls="--", lw=1)
    ax1.set_xlabel("t (s)")
    ax1.set_ylabel("反射/入射能量比")
    ax1.set_ylim(bottom=0)
    ax2 = ax1.twinx()
    ax2.plot(times, inc_e / max(float(np.max(inc_e)), 1e-12), color="#2ca02c", alpha=0.58, label="入射能量(归一化)")
    ax2.plot(times, ref_e / max(float(np.max(ref_e)), 1e-12), color="#d62728", alpha=0.58, label="反射能量(归一化)")
    ax2.set_ylabel("归一化能量")
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper right", fontsize=9)
    ax1.set_title(f"反射强度诊断：窗口中位数 {win.ratio_median:.3f}")
    fig.tight_layout()
    fig.savefig(ROOT / "reflection_strength.png")
    plt.close(fig)


def draw_peak_measurement(
    frames: np.ndarray,
    surface: np.ndarray,
    eta: np.ndarray,
    inc: np.ndarray,
    x_cm: np.ndarray,
    peak_df: pd.DataFrame,
    px_per_cm: float,
    fps: float,
    win: WindowResult,
) -> None:
    direct = peak_df[peak_df["series"] == "direct_raw"] if len(peak_df) else pd.DataFrame()
    if len(direct) and "accepted_for_summary" in direct.columns:
        direct = direct[direct["accepted_for_summary"] == True]
    if len(direct):
        frame_i = int(direct.groupby("frame").size().sort_values(ascending=False).index[0])
    else:
        frame_i = int((win.start_i + win.end_i) // 2)

    rgb = frames[frame_i]
    x_px = x_cm * px_per_cm + X0_PX
    y = eta[frame_i] - ndimage.gaussian_filter1d(eta[frame_i], sigma=90)
    y = ndimage.gaussian_filter1d(y, sigma=4)

    fig = plt.figure(figsize=(12, 8), dpi=160)
    gs = fig.add_gridspec(2, 1, height_ratios=[1.42, 1.0], hspace=0.23)
    ax0 = fig.add_subplot(gs[0])
    ax0.imshow(rgb)
    ax0.plot(x_px, surface[frame_i], color="#ff2d55", lw=1.3, label="提取水线")
    rows = direct[direct["frame"] == frame_i] if len(direct) else pd.DataFrame()
    for _, r in rows.iterrows():
        x1p = r["x1_cm"] * px_per_cm + X0_PX
        x2p = r["x2_cm"] * px_per_cm + X0_PX
        yp = float(np.interp((r["x1_cm"] + r["x2_cm"]) / 2, x_cm, surface[frame_i]))
        ax0.plot([x1p, x2p], [yp - 19, yp - 19], color="yellow", lw=2)
        ax0.text((x1p + x2p) / 2, yp - 25, f"{r['distance_cm']:.1f} cm", color="yellow", ha="center", fontsize=9, weight="bold")
        ax0.scatter(
            [x1p, x2p],
            [np.interp(r["x1_cm"], x_cm, surface[frame_i]), np.interp(r["x2_cm"], x_cm, surface[frame_i])],
            color="yellow",
            s=22,
        )
    ax0.set_xlim(45, rgb.shape[1] - 45)
    ax0.set_ylim(165, 55)
    ax0.set_title(f"直接主峰距测量示例：帧 {frame_i}，t={frame_i / fps:.2f} s")
    ax0.axis("off")

    ax1 = fig.add_subplot(gs[1])
    ax1.plot(x_cm, y, color="#111111", lw=1.2, label="原始 eta 空间剖面")
    ax1.plot(x_cm, inc[frame_i], color="#0057b8", lw=1.25, label="入射分量剖面")
    ax1.axhline(0, color="0.72", lw=0.8)
    for _, r in rows.iterrows():
        ax1.axvline(r["x1_cm"], color="gold", lw=0.9, alpha=0.9)
        ax1.axvline(r["x2_cm"], color="gold", lw=0.9, alpha=0.9)
    ax1.set_xlabel("x (cm)")
    ax1.set_ylabel("eta (cm)")
    ax1.legend(loc="upper right", fontsize=9)
    ax1.set_title("同一帧的原始/入射剖面对照")
    fig.tight_layout()
    fig.savefig(ROOT / "wave_peak_measurement.png")
    plt.close(fig)


def draw_judgement(summary: dict[str, object]) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), dpi=160)
    ax = axes[0]
    vals = [
        float(summary["直接峰距_cm"]),
        float(summary["入射峰距_cm"]),
        float(summary["FFT诊断波长_cm"]),
    ]
    labels = ["直接峰距", "分离后入射峰距", "2D FFT诊断"]
    colors = ["#555555", "#0057b8", "#b85c00"]
    ax.bar(labels, vals, color=colors)
    ax.set_ylabel("波长 / 峰距 (cm)")
    ax.set_title("主波长比较")
    ymax = max([v for v in vals if np.isfinite(v)] + [1.0])
    ax.set_ylim(0, ymax * 1.25)
    for i, v in enumerate(vals):
        if np.isfinite(v):
            ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=10)
    ax.tick_params(axis="x", labelrotation=16)

    ax2 = axes[1]
    ax2.axis("off")
    lines = [
        f"低反射窗口：{summary['窗口开始_s']:.2f}-{summary['窗口结束_s']:.2f} s",
        f"窗口反射/入射能量比：{summary['窗口反射入射能量比']:.3f}",
        f"直接 vs 入射差值：{summary['差值_直接减入射_cm']:.2f} cm",
        f"相对差异：{summary['相对差异_pct']:.1f}%",
        f"判断：{summary['判断简述']}",
        "",
        "说明：短视频、有限视场下，",
        "全帧 2D FFT 只作为方向与主峰诊断。",
    ]
    ax2.text(0.02, 0.94, "\n".join(lines), va="top", ha="left", fontsize=12, linespacing=1.55)
    fig.suptitle("驻波/反射影响判断", y=0.98)
    fig.tight_layout()
    fig.savefig(ROOT / "standing_wave_judgement_cn.png")
    plt.close(fig)


def write_csv_outputs(
    times: np.ndarray,
    x_cm: np.ndarray,
    eta: np.ndarray,
    surface: np.ndarray,
    inc: np.ndarray,
    ref: np.ndarray,
    inc_e: np.ndarray,
    ref_e: np.ndarray,
    ratio: np.ndarray,
    win: WindowResult,
    cal: Calibration,
    peak_df: pd.DataFrame,
    autocorr_df: pd.DataFrame,
    summary: dict[str, object],
) -> None:
    xt_df = pd.DataFrame(eta, columns=[f"x_{v:.3f}_cm" for v in x_cm])
    xt_df.insert(0, "time_s", times)
    xt_df.to_csv(ROOT / "eta_xt_surface_cm.csv", index=False, encoding="utf-8-sig")

    refl_df = pd.DataFrame(
        {
            "frame": np.arange(len(times)),
            "time_s": times,
            "incident_energy": inc_e,
            "reflected_energy": ref_e,
            "reflection_to_incident_ratio": ratio,
            "in_low_reflection_window": (np.arange(len(times)) >= win.start_i) & (np.arange(len(times)) < win.end_i),
        }
    )
    refl_df.to_csv(ROOT / "reflection_time_series.csv", index=False, encoding="utf-8-sig")
    peak_df.to_csv(ROOT / "peak_measurements.csv", index=False, encoding="utf-8-sig")
    autocorr_df.to_csv(ROOT / "spatial_autocorr_periods.csv", index=False, encoding="utf-8-sig")

    with (ROOT / "ruler_calibration.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["项目", "数值", "单位/说明"])
        writer.writerow(["px_per_cm", f"{cal.px_per_cm:.6f}", "px/cm"])
        writer.writerow(["px_per_cm_std_diagnostic", f"{cal.px_per_cm_std:.6f}", "诊断散布，非严格统计误差"])
        writer.writerow(["label_px_per_cm", f"{cal.label_px_per_cm:.6f}", "210--160 cm 标号线性拟合"])
        writer.writerow(["tick_period_fft_px", f"{cal.tick_period_fft_px:.6f}", "直尺周期 FFT 诊断"])
        writer.writerow(["tick_period_ac_px", f"{cal.tick_period_ac_px:.6f}", "直尺周期自相关诊断"])
        writer.writerow(["fit_rmse_px", f"{cal.fit_rmse_px:.6f}", "标号拟合残差 RMS"])
        writer.writerow(["ruler_band_y0", cal.ruler_y0, "px"])
        writer.writerow(["ruler_band_y1", cal.ruler_y1, "px"])
        writer.writerow(["tick_kind", cal.tick_kind, "使用背景直尺"])
        writer.writerow([])
        writer.writerow(["label_cm", "x_px", "residual_px"])
        for cm, x, res in zip(cal.label_values_cm, cal.label_positions_px, cal.fit_residual_px):
            writer.writerow([f"{cm:.1f}", f"{x:.2f}", f"{res:.3f}"])

    pd.DataFrame([summary]).to_csv(ROOT / "standing_wave_summary_cn.csv", index=False, encoding="utf-8-sig")

    np.savez_compressed(
        ROOT / "standing_wave_analysis_data.npz",
        times_s=times,
        x_cm=x_cm,
        surface_y_px=surface,
        eta_cm=eta,
        incident_eta_cm=inc,
        reflected_eta_cm=ref,
        incident_energy=inc_e,
        reflected_energy=ref_e,
        reflection_ratio=ratio,
        low_reflection_window=np.array([win.start_i, win.end_i, win.start_s, win.end_s], dtype=float),
        px_per_cm=np.array(cal.px_per_cm),
        ruler_label_positions_px=cal.label_positions_px,
        ruler_label_values_cm=cal.label_values_cm,
        summary_keys=np.array(list(summary.keys())),
        summary_values=np.array([str(v) for v in summary.values()]),
        autocorr_periods=autocorr_df.to_records(index=False) if len(autocorr_df) else np.array([]),
    )


def write_report(summary: dict[str, object]) -> None:
    report = f"""# 数据组 20 水波驻波/反射分析报告

## 处理概况

- 输入视频：`{VIDEO_NAME}`
- 逐帧读取：完整读取 {summary['读取帧数']} 帧，帧率 {summary['帧率_fps']:.3f} fps，视频时长 {summary['时长_s']:.3f} s，分辨率 {summary['宽_px']}×{summary['高_px']} px；其中有效水面分析帧为 {summary['分析帧数']} 帧，剔除无效黑屏帧：{summary['剔除无效帧']}。
- 直尺标定：背景直尺刻度清楚可见，采用 210--160 cm 十厘米标号线性校验，并用 1 cm 刻度周期 FFT/自相关作独立诊断；标定结果为 **{summary['px_per_cm']:.3f} px/cm**。未使用替代标定。
- 水线提取：对 {summary['分析帧数']} 个有效水面帧逐帧提取水面轮廓，生成 `eta(x,t)`；黑屏帧无可用水线，未纳入 FFT/峰距统计；`eta` 为相对时均水线的竖向位移，单位 cm。
- 方向分析：对 `eta(x,t)` 做 2D FFT，按频率-波数符号分离入射波与反射波；全帧 FFT 主峰只作为诊断值。

## 主要结果

| 项目 | 数值 |
|---|---:|
| 低反射稳定窗口 | {summary['窗口开始_s']:.2f}--{summary['窗口结束_s']:.2f} s |
| 稳定窗口反射/入射能量比中位数 | {summary['窗口反射入射能量比']:.3f} |
| 直接峰距中位数 | {summary['直接峰距_cm']:.2f} cm |
| 直接峰距样本数 | {summary['直接峰距样本数']} |
| 分离后入射剖面峰距中位数 | {summary['入射峰距_cm']:.2f} cm |
| 入射峰距样本数 | {summary['入射峰距样本数']} |
| 直接剖面自相关主周期 | {summary['直接自相关主周期_cm']:.2f} cm |
| 入射剖面自相关主周期 | {summary['入射自相关主周期_cm']:.2f} cm |
| 全帧 2D FFT 入射主峰诊断波长 | {summary['FFT诊断波长_cm']:.2f} cm |
| 直接-入射差值 | {summary['差值_直接减入射_cm']:.2f} cm |
| 相对差异 | {summary['相对差异_pct']:.1f}% |

## 判断

**{summary['判断完整']}**

本组视频约 {summary['时长_s']:.2f} s，横向有效视场约 {summary['视场宽度_cm']:.1f} cm；可用于峰距统计的完整波数有限。因此最终判断优先参考低反射窗口内的直接峰距与方向分离后的入射剖面峰距；全帧 2D FFT 的 {summary['FFT诊断波长_cm']:.2f} cm 保留为方向分离/主频主波数诊断，不把它单独作为高精度最终波长。

## 质量与问题

- 直尺刻度可见，标定诊断图见 `ruler_calibration_diagnostic.png`；没有启用替代标定。
- 水线整体连续，但上方固定结构、局部反光和容器边缘会影响局部边缘响应；脚本用跨 x 中值滤波、异常点替换和 Savitzky-Golay 平滑处理。
- 原始剖面存在局部短峰；最终峰距统计先用低反射窗口自相关主尺度（约 {summary['峰距筛选主周期_cm']:.2f} cm）筛选宽峰，局部短峰保留在 `peak_measurements.csv` 中但不作为最终波长。
- 直接峰距样本数为 {summary['直接峰距样本数']}，入射分量峰距样本数为 {summary['入射峰距样本数']}；短视频和有限视场是主要不确定性来源。
- 反射分量并非全程可忽略；若使用全时段原始峰距，应考虑驻波/反射或继续采用方向分离。

## 输出文件

- `standing_wave_cn_report.md`
- `standing_wave_summary_cn.csv`
- `standing_wave_judgement_cn.png`
- `wave_peak_measurement.png`
- `xt_raw_incident_reflected_panels.png`
- `reflection_strength.png`
- `ruler_calibration_diagnostic.png`
- `waterline_extraction_check.png`
- `eta_xt_surface_cm.csv`
- `reflection_time_series.csv`
- `peak_measurements.csv`
- `spatial_autocorr_periods.csv`
- `ruler_calibration.csv`
- `standing_wave_analysis_data.npz`
- `run_standing_wave_analysis.py`
"""
    (ROOT / "standing_wave_cn_report.md").write_text(report, encoding="utf-8-sig")


def judgement_from_values(ratio_win: float, diff: float, rel: float) -> tuple[str, str]:
    if not np.isfinite(rel):
        short = "样本不足，需谨慎判断"
        long = "峰距样本不足以稳定比较直接峰距和入射峰距；需要结合图像检查和反射强度曲线谨慎判断。"
    elif ratio_win >= 0.20 or rel >= 8.0:
        short = "需要考虑驻波/反射"
        long = (
            f"建议考虑驻波/反射影响。低反射窗口内反射/入射能量比中位数为 {ratio_win:.3f}，"
            f"直接峰距与分离后入射峰距相差 {abs(diff):.2f} cm（{rel:.1f}%）。"
            "直接使用全帧原始峰距会带入反射偏差。"
        )
    elif ratio_win >= 0.10 or rel >= 3.0:
        short = "反射影响中等，纳入不确定度"
        long = (
            f"反射影响中等，建议把方向分离结果纳入不确定度。窗口反射/入射能量比中位数为 {ratio_win:.3f}，"
            f"直接峰距与入射峰距相差 {abs(diff):.2f} cm（{rel:.1f}%）。"
        )
    else:
        short = "低反射窗口内可不做强驻波修正"
        long = (
            f"低反射稳定窗口内暂不需要做强驻波修正。窗口反射/入射能量比中位数为 {ratio_win:.3f}，"
            f"直接峰距与分离后入射峰距差异约 {rel:.1f}%，处于短视频峰识别和标定不确定度的同量级。"
        )
    return short, long


def main() -> None:
    setup_font()
    frames_all, fps = load_video()
    read_n = int(len(frames_all))
    mask = valid_frame_mask(frames_all)
    valid_indices = np.flatnonzero(mask)
    invalid_indices = np.flatnonzero(~mask)
    if len(valid_indices) == 0:
        raise RuntimeError("没有检测到有效水面帧")
    frames = frames_all[valid_indices]
    n, h, w, _ = frames.shape
    times = valid_indices.astype(float) / fps

    cal = calibrate_from_ruler(frames)
    surface, eta, x_cm, global_rows = extract_surface(frames, cal.px_per_cm)
    dx_cm = float(np.median(np.diff(x_cm)))
    inc, ref, fft_meta = directional_separation(eta, fps, dx_cm)
    inc_e, ref_e, ratio = reflection_timeseries(inc, ref)
    win = choose_low_reflection_window(times, ratio, inc_e, fps)

    frame_indices = np.arange(win.start_i, win.end_i)
    direct_ac_df, direct_ac_med, direct_ac_mad, direct_ac_count = estimate_spatial_periods(
        eta, x_cm, frame_indices, fps, "direct_raw"
    )
    inc_ac_df, inc_ac_med, inc_ac_mad, inc_ac_count = estimate_spatial_periods(
        inc, x_cm, frame_indices, fps, "incident_separated"
    )
    autocorr_df = pd.concat([direct_ac_df, inc_ac_df], ignore_index=True)

    period_candidates = [v for v in (direct_ac_med, inc_ac_med) if np.isfinite(v)]
    main_period_for_filter = float(np.median(period_candidates)) if period_candidates else float("nan")
    fft_lambda = float(fft_meta["fft_wavelength_cm"])
    peak_min_distance_cm = 14.0
    if np.isfinite(main_period_for_filter):
        peak_min_distance_cm = float(np.clip(0.45 * main_period_for_filter, 12.0, 18.0))
    elif np.isfinite(fft_lambda):
        peak_min_distance_cm = float(np.clip(0.35 * fft_lambda, 12.0, 18.0))

    direct_df, _, _, _, _ = estimate_peak_distances(
        eta, x_cm, frame_indices, fps, "direct_raw", min_dist_cm=peak_min_distance_cm, prominence_fraction=0.26
    )
    inc_df, _, _, _, _ = estimate_peak_distances(
        inc, x_cm, frame_indices, fps, "incident_separated", min_dist_cm=peak_min_distance_cm, prominence_fraction=0.24
    )
    peak_df = pd.concat([direct_df, inc_df], ignore_index=True)
    if len(peak_df):
        peak_df["accepted_for_summary"] = False
        peak_df["summary_filter_low_cm"] = np.nan
        peak_df["summary_filter_high_cm"] = np.nan
        ranges = {
            "direct_raw": direct_ac_med,
            "incident_separated": inc_ac_med,
        }
        for series_name, period in ranges.items():
            if not np.isfinite(period):
                period = main_period_for_filter
            if not np.isfinite(period):
                continue
            low = 0.75 * float(period)
            high = 1.35 * float(period)
            m = (peak_df["series"] == series_name) & (peak_df["distance_cm"] >= low) & (peak_df["distance_cm"] <= high)
            peak_df.loc[peak_df["series"] == series_name, "summary_filter_low_cm"] = low
            peak_df.loc[peak_df["series"] == series_name, "summary_filter_high_cm"] = high
            peak_df.loc[m, "accepted_for_summary"] = True

    direct_summary_df = peak_df[(peak_df["series"] == "direct_raw") & (peak_df["accepted_for_summary"] == True)] if len(peak_df) else pd.DataFrame()
    inc_summary_df = peak_df[(peak_df["series"] == "incident_separated") & (peak_df["accepted_for_summary"] == True)] if len(peak_df) else pd.DataFrame()
    direct_med, direct_mad, direct_count, direct_frame_count = summarize_distance_df(direct_summary_df)
    inc_med, inc_mad, inc_count, inc_frame_count = summarize_distance_df(inc_summary_df)

    diff = direct_med - inc_med if np.isfinite(direct_med) and np.isfinite(inc_med) else float("nan")
    rel = abs(diff) / inc_med * 100.0 if np.isfinite(diff) and np.isfinite(inc_med) and inc_med else float("nan")
    judgement_short, judgement_long = judgement_from_values(win.ratio_median, diff, rel)

    summary: dict[str, object] = {
        "数据组": DATA_GROUP,
        "视频": VIDEO_NAME,
        "读取帧数": int(read_n),
        "分析帧数": int(n),
        "剔除无效帧": ",".join(str(int(v)) for v in invalid_indices) if len(invalid_indices) else "无",
        "帧数": int(n),
        "帧率_fps": float(fps),
        "时长_s": float(read_n / fps),
        "分析时长_s": float(n / fps),
        "宽_px": int(w),
        "高_px": int(h),
        "px_per_cm": float(cal.px_per_cm),
        "标定诊断散布_px_per_cm": float(cal.px_per_cm_std),
        "标号拟合_px_per_cm": float(cal.label_px_per_cm),
        "刻度周期FFT_px": float(cal.tick_period_fft_px),
        "刻度周期自相关_px": float(cal.tick_period_ac_px),
        "视场宽度_cm": float(x_cm[-1] - x_cm[0]),
        "水线全局行中位_px": float(np.median(global_rows)),
        "直接自相关主周期_cm": float(direct_ac_med),
        "直接自相关MAD_cm": float(direct_ac_mad),
        "直接自相关样本数": int(direct_ac_count),
        "入射自相关主周期_cm": float(inc_ac_med),
        "入射自相关MAD_cm": float(inc_ac_mad),
        "入射自相关样本数": int(inc_ac_count),
        "峰距筛选主周期_cm": float(main_period_for_filter),
        "窗口开始_s": float(win.start_s),
        "窗口结束_s": float(win.end_s),
        "窗口反射入射能量比": float(win.ratio_median),
        "窗口反射入射能量比均值": float(win.ratio_mean),
        "直接峰距_cm": float(direct_med),
        "直接峰距MAD_cm": float(direct_mad),
        "直接峰距样本数": int(direct_count),
        "直接峰距帧数": int(direct_frame_count),
        "入射峰距_cm": float(inc_med),
        "入射峰距MAD_cm": float(inc_mad),
        "入射峰距样本数": int(inc_count),
        "入射峰距帧数": int(inc_frame_count),
        "FFT主频_Hz": float(fft_meta["fft_frequency_hz"]),
        "FFT诊断波长_cm": float(fft_meta["fft_wavelength_cm"]),
        "FFT波数_cyc_per_cm": float(fft_meta["fft_wavenumber_cyc_per_cm"]),
        "峰距最小阈值_cm": float(peak_min_distance_cm),
        "入射方向": "+x/right" if bool(fft_meta["incident_positive_x"]) else "-x/left",
        "正向能量": float(fft_meta["positive_x_energy"]),
        "反向能量": float(fft_meta["negative_x_energy"]),
        "差值_直接减入射_cm": float(diff),
        "相对差异_pct": float(rel),
        "判断简述": judgement_short,
        "判断完整": judgement_long,
        "FFT说明": "全帧 2D FFT 仅作诊断；短视频/有限视场下不单独作为最终高精度波长。",
    }

    draw_ruler_diagnostic(frames, cal)
    draw_surface_check(frames, surface, x_cm, cal.px_per_cm, fps)
    draw_xt_panels(times, x_cm, eta, inc, ref, win)
    draw_reflection(times, inc_e, ref_e, ratio, win)
    draw_peak_measurement(frames, surface, eta, inc, x_cm, peak_df, cal.px_per_cm, fps, win)
    draw_judgement(summary)
    write_csv_outputs(times, x_cm, eta, surface, inc, ref, inc_e, ref_e, ratio, win, cal, peak_df, autocorr_df, summary)
    write_report(summary)

    print("分析完成")
    print(f"px_per_cm={summary['px_per_cm']:.3f}")
    print(f"window={summary['窗口开始_s']:.2f}-{summary['窗口结束_s']:.2f}s ratio={summary['窗口反射入射能量比']:.3f}")
    print(
        f"direct={summary['直接峰距_cm']:.2f} cm, "
        f"incident={summary['入射峰距_cm']:.2f} cm, fft_diag={summary['FFT诊断波长_cm']:.2f} cm"
    )
    print(summary["判断简述"])


if __name__ == "__main__":
    main()

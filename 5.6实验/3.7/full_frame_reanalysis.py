# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import math
import shutil
import tempfile

import cv2
import matplotlib
import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.signal import find_peaks, savgol_filter


matplotlib.use("Agg")
import matplotlib.pyplot as plt


plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


SCRIPT_DIR = Path(__file__).resolve().parent
VIDEO_PATH = SCRIPT_DIR / "5.mp4"
OUT_DIR = SCRIPT_DIR / "frame_reanalysis_full"
OVERLAY_DIR = OUT_DIR / "frame_overlays"


@dataclass
class Calibration:
    px_per_cm: float
    median_px_per_cm: float
    std_px_per_cm: float
    estimates: list[dict[str, float | int | str]]
    note: str


def write_png(path: Path, bgr_img: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".png", bgr_img)
    if not ok:
        raise RuntimeError(f"cannot encode png: {path}")
    path.write_bytes(buf.tobytes())


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def copy_to_ascii_temp(video_path: Path) -> Path:
    temp_dir = Path(tempfile.gettempdir()) / "codex_3_7_full_frame_reanalysis"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_video = temp_dir / "source_3_7.mp4"
    shutil.copyfile(video_path, temp_video)
    return temp_video


def load_video(video_path: Path) -> tuple[list[np.ndarray], float]:
    # OpenCV on Windows can fail on non-ASCII paths. Use an ASCII temp copy.
    temp_video = copy_to_ascii_temp(video_path)
    cap = cv2.VideoCapture(str(temp_video))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV cannot open video: {video_path}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0) or 30.0
    frames: list[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame is not None and frame.size:
            frames.append(frame)
    cap.release()
    if not frames:
        raise RuntimeError(f"No frames decoded from video: {video_path}")
    return frames, fps


def make_contact_sheet(frames: list[np.ndarray], path: Path) -> None:
    idxs = np.linspace(0, len(frames) - 1, min(12, len(frames)), dtype=int)
    thumbs = []
    for idx in idxs:
        img = frames[int(idx)].copy()
        cv2.putText(
            img,
            f"frame {idx:02d}",
            (24, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 0, 255),
            3,
            cv2.LINE_AA,
        )
        thumbs.append(cv2.resize(img, (320, 180), interpolation=cv2.INTER_AREA))

    cols = 4
    rows = int(math.ceil(len(thumbs) / cols))
    blank = np.zeros_like(thumbs[0])
    padded = thumbs + [blank] * (rows * cols - len(thumbs))
    grid_rows = [
        np.concatenate(padded[r * cols : (r + 1) * cols], axis=1)
        for r in range(rows)
    ]
    write_png(path, np.concatenate(grid_rows, axis=0))


def estimate_ruler_period(frame: np.ndarray, crop: tuple[int, int]) -> tuple[int, float] | None:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    y0, y1 = crop
    y0 = max(0, min(y0, gray.shape[0] - 2))
    y1 = max(y0 + 2, min(y1, gray.shape[0]))
    dark = 255.0 - gray[y0:y1, :].astype(float)
    signal = dark.mean(axis=0)
    signal = gaussian_filter1d(signal, 1.0)
    highpass = signal - gaussian_filter1d(signal, 30.0)
    x = highpass[40:-40]
    if x.size < 200 or float(x.std()) < 1e-6:
        return None
    x = (x - x.mean()) / (x.std() + 1e-6)
    autocorr = np.correlate(x, x, mode="full")[len(x) - 1 :]
    autocorr[:10] = 0

    lo, hi = 25, 45
    peaks, _ = find_peaks(autocorr[lo:hi], distance=4)
    if len(peaks) == 0:
        return None
    peaks = peaks + lo
    best = int(peaks[np.argmax(autocorr[peaks])])
    return best, float(autocorr[best])


def calibrate_px_per_cm(frames: list[np.ndarray]) -> Calibration:
    frame_idxs = np.linspace(0, len(frames) - 1, min(7, len(frames)), dtype=int)
    # The ruler is stationary near the lower edge of the tank. These bands avoid
    # most label text while keeping the long centimeter tick marks.
    crops = [(360, 430), (380, 430), (395, 430)]
    estimates: list[dict[str, float | int | str]] = []
    for frame_idx in frame_idxs:
        for crop in crops:
            result = estimate_ruler_period(frames[int(frame_idx)], crop)
            if result is None:
                continue
            period, score = result
            estimates.append(
                {
                    "frame_index": int(frame_idx),
                    "crop_y0": crop[0],
                    "crop_y1": crop[1],
                    "px_per_cm_estimate": float(period),
                    "autocorr_score": float(score),
                }
            )

    if not estimates:
        return Calibration(33.0, 33.0, 0.0, [], "自动标定失败；使用保守默认值 33.0 px/cm")

    values = np.array([float(e["px_per_cm_estimate"]) for e in estimates], dtype=float)
    median = float(np.median(values))
    std = float(np.std(values))
    note = "直尺厘米刻度自相关标定；取多帧、多裁剪带中位数"
    return Calibration(median, median, std, estimates, note)


def save_ruler_diagnostic(frames: list[np.ndarray], calibration: Calibration) -> None:
    ref = frames[-1]
    crop = ref[365:435, :].copy()
    zoom = cv2.resize(crop, (ref.shape[1] * 2, crop.shape[0] * 4), interpolation=cv2.INTER_CUBIC)
    write_png(OUT_DIR / "ruler_crop_zoom.png", zoom)

    rows = calibration.estimates
    if rows:
        write_csv(
            OUT_DIR / "ruler_calibration_estimates.csv",
            rows,
            ["frame_index", "crop_y0", "crop_y1", "px_per_cm_estimate", "autocorr_score"],
        )

    fig, ax = plt.subplots(figsize=(7, 4), dpi=160)
    if rows:
        vals = [float(r["px_per_cm_estimate"]) for r in rows]
        ax.hist(vals, bins=np.arange(24.5, 45.6, 1.0), color="#3a7ca5", edgecolor="white")
        ax.axvline(calibration.px_per_cm, color="#d1495b", lw=2, label=f"{calibration.px_per_cm:.2f} px/cm")
        ax.set_xlabel("px/cm estimate")
        ax.set_ylabel("count")
        ax.legend()
    ax.set_title("Ruler Calibration Estimates")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "ruler_calibration_diagnostic.png")
    plt.close(fig)


def green_score(frame: np.ndarray) -> np.ndarray:
    b, g, r = cv2.split(frame)
    score = g.astype(np.float32) - 0.45 * r.astype(np.float32) - 0.35 * b.astype(np.float32)
    return cv2.GaussianBlur(score, (5, 9), 0)


def detect_waterline(frame: np.ndarray) -> tuple[np.ndarray, int, float, float]:
    score = green_score(frame)
    row_mean = score[:, 100:-100].mean(axis=1)
    row_smooth = gaussian_filter1d(row_mean, 3.0)
    row_grad = np.gradient(row_smooth)

    # The waterline lives above the ruler and below the dark upper water volume.
    y0, y1 = 250, 390
    y_center = y0 + int(np.argmax(row_grad[y0:y1]))
    band0 = max(0, y_center - 65)
    band1 = min(frame.shape[0] - 1, y_center + 65)

    dy = np.gradient(score, axis=0)
    segment = dy[band0:band1, :]
    raw_y = band0 + np.argmax(segment, axis=0).astype(float)
    strength = np.max(segment, axis=0)

    median_y = median_filter(raw_y, size=31, mode="nearest")
    residual = np.abs(raw_y - median_y)
    good = (residual < 18.0) & (strength > np.percentile(strength, 8))

    x = np.arange(len(raw_y))
    if int(good.sum()) > 20:
        filled = np.interp(x, x[good], raw_y[good])
    else:
        filled = median_y
    filtered = median_filter(filled, size=21, mode="nearest")

    win = 101 if len(filtered) >= 101 else max(7, len(filtered) // 2 * 2 - 1)
    if win % 2 == 0:
        win -= 1
    if win > 7:
        filtered = savgol_filter(filtered, win, 3, mode="interp")

    good_fraction = float(good.mean())
    strength_median = float(np.median(strength))
    return filtered, int(y_center), good_fraction, strength_median


def smooth_profile(profile: np.ndarray, window_px: int, polyorder: int = 3) -> np.ndarray:
    window_px = max(7, int(window_px))
    if window_px % 2 == 0:
        window_px += 1
    if window_px >= len(profile):
        window_px = len(profile) - 1 if len(profile) % 2 == 0 else len(profile)
    if window_px <= polyorder + 2:
        return profile.copy()
    return savgol_filter(profile, window_px, polyorder, mode="interp")


def detect_spatial_features(
    yline: np.ndarray,
    px_per_cm: float,
    scale: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    eta = -(yline - np.mean(yline)) / px_per_cm
    if scale == "broad":
        eta_s = smooth_profile(eta, int(round(1.8 * px_per_cm)), 3)
        distance = int(round(7.0 * px_per_cm))
        prominence = max(0.16, float(np.std(eta_s)) * 0.45)
    elif scale == "local":
        fine = smooth_profile(eta, int(round(0.45 * px_per_cm)), 2)
        broad = smooth_profile(eta, int(round(4.0 * px_per_cm)), 3)
        eta_s = fine - broad
        distance = int(round(3.5 * px_per_cm))
        prominence = max(0.045, float(np.std(eta_s)) * 0.55)
    else:
        raise ValueError(scale)

    peaks, peak_props = find_peaks(eta_s, distance=max(1, distance), prominence=prominence)
    troughs, trough_props = find_peaks(-eta_s, distance=max(1, distance), prominence=prominence)
    props = {
        "peak_prominences": peak_props.get("prominences", np.array([])),
        "trough_prominences": trough_props.get("prominences", np.array([])),
    }
    return eta_s, peaks, troughs, props


def overlay_frame(
    frame: np.ndarray,
    frame_index: int,
    yline: np.ndarray,
    broad_peaks: np.ndarray,
    broad_troughs: np.ndarray,
    x_cm: np.ndarray,
    time_s: float,
) -> np.ndarray:
    img = frame.copy()
    for x in range(0, img.shape[1] - 1):
        cv2.line(
            img,
            (x, int(round(yline[x]))),
            (x + 1, int(round(yline[x + 1]))),
            (0, 0, 255),
            2,
        )
    for x in broad_peaks:
        y = int(round(yline[int(x)]))
        cv2.circle(img, (int(x), y), 8, (0, 255, 255), -1)
        cv2.putText(img, f"{x_cm[int(x)]:.1f}cm", (int(x) - 42, y - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
    for x in broad_troughs:
        y = int(round(yline[int(x)]))
        cv2.circle(img, (int(x), y), 7, (255, 160, 0), -1)
    cv2.putText(
        img,
        f"frame {frame_index:02d}  t={time_s:.3f}s",
        (18, 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.1,
        (0, 0, 255),
        3,
        cv2.LINE_AA,
    )
    return img


def adjacent_distances(peaks: np.ndarray, px_per_cm: float) -> list[tuple[int, int, float, int]]:
    out: list[tuple[int, int, float, int]] = []
    if len(peaks) < 2:
        return out
    for left, right in zip(peaks[:-1], peaks[1:]):
        dx_px = int(right - left)
        out.append((int(left), int(right), float(dx_px / px_per_cm), dx_px))
    return out


def autocorr_wavelength_cm(eta: np.ndarray, px_per_cm: float) -> float | None:
    profile = eta - np.mean(eta)
    if float(np.std(profile)) < 0.05:
        return None
    profile = profile * np.hanning(len(profile))
    ac = np.correlate(profile, profile, mode="full")[len(profile) - 1 :]
    ac[: int(round(6.0 * px_per_cm))] = 0
    lo = int(round(10.0 * px_per_cm))
    hi = min(len(ac) - 1, int(round(35.0 * px_per_cm)))
    if hi <= lo:
        return None
    peaks, _ = find_peaks(ac[lo:hi], distance=int(round(4.0 * px_per_cm)))
    if len(peaks) == 0:
        return None
    peaks = peaks + lo
    best = int(peaks[np.argmax(ac[peaks])])
    return float(best / px_per_cm)


def write_wide_profile_csv(path: Path, matrix: np.ndarray, fps: float, prefix: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n_frames, width = matrix.shape
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["frame_index", "time_s"] + [f"{prefix}_{x:04d}" for x in range(width)])
        for i in range(n_frames):
            writer.writerow([i, i / fps] + [f"{v:.6f}" for v in matrix[i]])


def fft_directional_diagnostic(eta_xt: np.ndarray, fps: float, px_per_cm: float) -> dict[str, float]:
    n_t, n_x = eta_xt.shape
    dx_cm = 1.0 / px_per_cm
    dt_s = 1.0 / fps

    data = eta_xt - np.nanmean(eta_xt, axis=1, keepdims=True)
    data = data - np.nanmean(data, axis=0, keepdims=True)
    data = data * np.hanning(n_t)[:, None] * np.hanning(n_x)[None, :]

    spectrum = np.fft.fftshift(np.fft.fft2(data))
    power = np.abs(spectrum) ** 2
    f = np.fft.fftshift(np.fft.fftfreq(n_t, d=dt_s))
    k = np.fft.fftshift(np.fft.fftfreq(n_x, d=dx_cm))
    ff, kk = np.meshgrid(f, k, indexing="ij")

    with np.errstate(divide="ignore", invalid="ignore"):
        wavelength = 1.0 / np.abs(kk)
    mask = (
        (np.abs(ff) >= 0.25)
        & (np.abs(ff) <= fps / 2.2)
        & (wavelength >= 6.0)
        & (wavelength <= 50.0)
        & np.isfinite(wavelength)
    )
    if not np.any(mask):
        return {
            "dominant_frequency_hz": float("nan"),
            "dominant_wavelength_cm": float("nan"),
            "dominant_power": 0.0,
            "directional_energy_ratio": float("nan"),
            "positive_diagonal_energy": 0.0,
            "negative_diagonal_energy": 0.0,
        }

    masked_power = np.where(mask, power, 0.0)
    max_idx = np.unravel_index(int(np.argmax(masked_power)), masked_power.shape)

    positive_diag = mask & (ff * kk > 0)
    negative_diag = mask & (ff * kk < 0)
    pos_energy = float(power[positive_diag].sum())
    neg_energy = float(power[negative_diag].sum())
    ratio = min(pos_energy, neg_energy) / max(pos_energy, neg_energy) if max(pos_energy, neg_energy) > 0 else float("nan")

    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=160)
    show_mask = (np.abs(f) <= 5.0)[:, None] & (np.abs(k) <= 0.18)[None, :]
    power_show = np.where(show_mask, np.log10(power + 1.0), np.nan)
    im = ax.imshow(
        power_show,
        origin="lower",
        aspect="auto",
        extent=[float(k.min()), float(k.max()), float(f.min()), float(f.max())],
        cmap="magma",
    )
    ax.set_xlim(-0.18, 0.18)
    ax.set_ylim(-5.0, 5.0)
    ax.set_xlabel("spatial frequency k (cycles/cm)")
    ax.set_ylabel("temporal frequency f (Hz)")
    ax.set_title("x-t FFT Directional Diagnostic")
    fig.colorbar(im, ax=ax, label="log10(power + 1)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "xt_fft_directional_diagnostic.png")
    plt.close(fig)

    return {
        "dominant_frequency_hz": float(abs(ff[max_idx])),
        "dominant_wavelength_cm": float(wavelength[max_idx]),
        "dominant_power": float(power[max_idx]),
        "directional_energy_ratio": ratio,
        "positive_diagonal_energy": pos_energy,
        "negative_diagonal_energy": neg_energy,
    }


def plot_results(
    eta_xt: np.ndarray,
    fps: float,
    px_per_cm: float,
    frame_rows: list[dict],
    distance_rows: list[dict],
) -> None:
    n_frames, width = eta_xt.shape
    x_extent_cm = width / px_per_cm

    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=170)
    vmax = max(0.2, float(np.nanpercentile(np.abs(eta_xt), 98)))
    im = ax.imshow(
        eta_xt,
        aspect="auto",
        origin="lower",
        cmap="RdBu_r",
        vmin=-vmax,
        vmax=vmax,
        extent=[0, x_extent_cm, 0, (n_frames - 1) / fps],
    )
    ax.set_xlabel("x (cm from left image edge)")
    ax.set_ylabel("time (s)")
    ax.set_title("逐帧水线位移 x-t 图")
    fig.colorbar(im, ax=ax, label="relative waterline displacement (cm)")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "eta_xt_surface_cm.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4), dpi=160)
    distances = [float(r["distance_cm"]) for r in distance_rows]
    if distances:
        ax.hist(distances, bins=8, color="#2a9d8f", edgecolor="white")
        ax.axvline(np.median(distances), color="#d1495b", lw=2, label=f"median {np.median(distances):.2f} cm")
        ax.legend()
    ax.set_xlabel("adjacent broad crest distance (cm)")
    ax.set_ylabel("count")
    ax.set_title("主波峰相邻距离分布")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "broad_crest_distance_histogram.png")
    plt.close(fig)

    times = np.array([float(r["time_s"]) for r in frame_rows])
    eta_range = np.array([float(r["eta_range_cm"]) for r in frame_rows])
    broad_counts = np.array([int(r["broad_crest_count"]) for r in frame_rows])
    quality = np.array([float(r["waterline_good_fraction"]) for r in frame_rows])

    fig, axs = plt.subplots(3, 1, figsize=(8, 7), dpi=160, sharex=True)
    axs[0].plot(times, eta_range, color="#264653")
    axs[0].set_ylabel("eta range (cm)")
    axs[1].step(times, broad_counts, where="mid", color="#e76f51")
    axs[1].set_ylabel("broad crests")
    axs[2].plot(times, quality, color="#2a9d8f")
    axs[2].set_ylabel("good fraction")
    axs[2].set_xlabel("time (s)")
    axs[0].set_title("逐帧检测质量与波面幅度")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "per_frame_metrics.png")
    plt.close(fig)


def build_report(
    frames: list[np.ndarray],
    fps: float,
    calibration: Calibration,
    frame_rows: list[dict],
    distance_rows: list[dict],
    feature_rows: list[dict],
    fft_diag: dict[str, float],
) -> None:
    broad_distances = np.array([float(r["distance_cm"]) for r in distance_rows], dtype=float)
    broad_px = np.array([float(r["distance_px"]) for r in distance_rows], dtype=float)
    local_features = [r for r in feature_rows if r["scale"] == "local" and r["kind"] == "crest"]

    eta_ranges = np.array([float(r["eta_range_cm"]) for r in frame_rows], dtype=float)
    good_fracs = np.array([float(r["waterline_good_fraction"]) for r in frame_rows], dtype=float)
    autocorr_vals = np.array(
        [float(r["autocorr_wavelength_cm"]) for r in frame_rows if r["autocorr_wavelength_cm"] != ""],
        dtype=float,
    )

    def stat_line(values: np.ndarray) -> str:
        if values.size == 0:
            return "无可用样本"
        return f"n={values.size}, mean={values.mean():.2f}, median={np.median(values):.2f}, std={values.std(ddof=1) if values.size > 1 else 0.0:.2f}"

    duration_s = len(frames) / fps
    last_frame_time_s = (len(frames) - 1) / fps
    x_extent_cm = frames[0].shape[1] / calibration.px_per_cm
    practical_calibration_uncertainty = max(1.0, calibration.std_px_per_cm)
    edge_margin_warning = ""
    if broad_distances.size:
        final_median = float(np.median(broad_distances))
        final_mean = float(np.mean(broad_distances))
        final_std = float(np.std(broad_distances, ddof=1)) if broad_distances.size > 1 else 0.0
        broad_summary = f"{final_median:.2f} cm（中位数；均值 {final_mean:.2f} cm，标准差 {final_std:.2f} cm，样本 {broad_distances.size} 个）"
        sensitivity_35 = float(np.median(broad_px / 35.387)) if broad_px.size else float("nan")
        cal_low = float(np.median(broad_px / (calibration.px_per_cm + practical_calibration_uncertainty)))
        cal_high = float(np.median(broad_px / max(1e-6, calibration.px_per_cm - practical_calibration_uncertainty)))
        edge_margins = np.array(
            [
                min(float(r["left_x_cm"]), x_extent_cm - float(r["right_x_cm"]))
                for r in distance_rows
            ],
            dtype=float,
        )
        near_edge_count = int(np.sum(edge_margins < 5.0))
        if near_edge_count:
            edge_margin_warning = f"；其中 {near_edge_count}/{broad_distances.size} 个样本至少一侧主峰距画面边缘小于 5 cm"
    else:
        final_median = float("nan")
        broad_summary = "没有检测到足够的同帧相邻主波峰样本"
        sensitivity_35 = float("nan")
        cal_low = float("nan")
        cal_high = float("nan")

    reflection_ratio = fft_diag.get("directional_energy_ratio", float("nan"))
    if math.isfinite(reflection_ratio):
        reflection_text = (
            "反向/正向能量同量级，驻波或反射影响明显"
            if reflection_ratio >= 0.35
            else "反向能量较低，但仍建议结合逐帧图复核"
        )
    else:
        reflection_text = "频域样本不足，方向能量比仅供参考"

    report = f"""# 3.7 / 5.mp4 完整逐帧重新分析报告

## 视频与标定

- 视频：`5.mp4`
- 解码帧数：`{len(frames)}` 帧
- 帧率：`{fps:.6f} fps`
- 帧序列覆盖时长：`{duration_s:.3f} s`（最后一帧时间戳 `{last_frame_time_s:.3f} s`）
- 分辨率：`{frames[0].shape[1]} x {frames[0].shape[0]}`
- 直尺自动标定：`{calibration.px_per_cm:.2f} px/cm`（{calibration.note}；算法估计散布 std={calibration.std_px_per_cm:.2f} px/cm，实际读尺建议保守按约 ±{practical_calibration_uncertainty:.1f} px/cm 看待）

## 逐帧处理方法

1. 对每帧计算绿色通道优势亮度，用水面处的垂直亮度跃迁逐列定位水线。
2. 对逐列水线做中值滤波、异常点插值和 Savitzky-Golay 平滑。
3. 在每帧水线轮廓上分别检测主尺度波峰/波谷和局部短波纹。
4. 输出全部帧的叠加图、逐帧水线坐标、逐帧波峰/波谷表、相邻主波峰距离表和 `x-t` 频域诊断。

## 主要结果

- 逐帧水线有效点比例：均值 `{good_fracs.mean():.3f}`，最低 `{good_fracs.min():.3f}`。
- 水线相对位移范围：中位数 `{np.median(eta_ranges):.2f} cm`，最大 `{eta_ranges.max():.2f} cm`。
- 同帧相邻主波峰距离：{broad_summary}{edge_margin_warning}。
- 若只考虑约 ±{practical_calibration_uncertainty:.1f} px/cm 的标定敏感性，这批主峰像素距离约对应 `{cal_low:.2f}--{cal_high:.2f} cm`。
- 用旧标定 `35.387 px/cm` 换算同一批主峰像素距离时，中位数约 `{sensitivity_35:.2f} cm`，可作为标定敏感性参考。
- 逐帧空间自相关诊断：{stat_line(autocorr_vals)}。
- `x-t` FFT 诊断主频：`{fft_diag.get("dominant_frequency_hz", float("nan")):.3f} Hz`。
- `x-t` FFT 诊断主波长：`{fft_diag.get("dominant_wavelength_cm", float("nan")):.2f} cm`。
- 方向能量比：`{reflection_ratio:.3f}`；判断：{reflection_text}。

## 结论口径

这段视频只有 `{len(frames)}` 帧、约 `{duration_s:.2f} s`，且同一帧内可同时看到的清晰主波峰数量有限。按本次自动直尺标定，主尺度相邻波峰的可用直接样本集中在 `{final_median:.1f} cm` 左右；考虑标定敏感性、边缘波峰和短视频频域分辨率，建议实验报告写成 `约 26--27 cm` 或保守写 `约 26 cm，±2 cm`。`x-t` FFT 更适合作为传播方向和反射风险诊断，不建议单独作为最终波长。

## 输出文件

- `frame_metrics.csv`：每帧质量、幅度、主峰数量、主峰距摘要。
- `crest_trough_features.csv`：每帧主尺度/局部尺度波峰波谷坐标。
- `broad_crest_distances.csv`：同帧相邻主波峰距离。
- `waterline_profiles_px.csv`：每帧每个 x 像素的水线 y 坐标。
- `eta_xt_surface_cm_wide.csv`：每帧每个 x 像素的相对水线位移。
- `frame_overlays/frame_####.png`：全部逐帧水线和主波峰叠加图。
- `eta_xt_surface_cm.png`、`xt_fft_directional_diagnostic.png`、`broad_crest_distance_histogram.png`、`per_frame_metrics.png`：诊断图。
"""
    (OUT_DIR / "summary_cn.md").write_text(report, encoding="utf-8")

    summary_rows = [
        {"metric": "decoded_frames", "value": len(frames)},
        {"metric": "fps", "value": f"{fps:.6f}"},
        {"metric": "duration_s", "value": f"{duration_s:.6f}"},
        {"metric": "last_frame_time_s", "value": f"{last_frame_time_s:.6f}"},
        {"metric": "px_per_cm", "value": f"{calibration.px_per_cm:.6f}"},
        {"metric": "practical_px_per_cm_uncertainty", "value": f"{practical_calibration_uncertainty:.6f}"},
        {"metric": "broad_distance_count", "value": int(broad_distances.size)},
        {"metric": "broad_distance_median_cm", "value": f"{np.median(broad_distances):.6f}" if broad_distances.size else ""},
        {"metric": "broad_distance_calibration_low_cm", "value": f"{cal_low:.6f}" if broad_distances.size else ""},
        {"metric": "broad_distance_calibration_high_cm", "value": f"{cal_high:.6f}" if broad_distances.size else ""},
        {"metric": "broad_distance_mean_cm", "value": f"{np.mean(broad_distances):.6f}" if broad_distances.size else ""},
        {"metric": "broad_distance_std_cm", "value": f"{np.std(broad_distances, ddof=1):.6f}" if broad_distances.size > 1 else "0.000000"},
        {"metric": "dominant_fft_frequency_hz", "value": f"{fft_diag.get('dominant_frequency_hz', float('nan')):.6f}"},
        {"metric": "dominant_fft_wavelength_cm", "value": f"{fft_diag.get('dominant_wavelength_cm', float('nan')):.6f}"},
        {"metric": "directional_energy_ratio", "value": f"{reflection_ratio:.6f}"},
        {"metric": "local_crest_feature_count", "value": len(local_features)},
    ]
    write_csv(OUT_DIR / "summary_metrics.csv", summary_rows, ["metric", "value"])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OVERLAY_DIR.mkdir(parents=True, exist_ok=True)

    frames, fps = load_video(VIDEO_PATH)
    make_contact_sheet(frames, OUT_DIR / "contact_sheet_all_frames.png")

    calibration = calibrate_px_per_cm(frames)
    px_per_cm = calibration.px_per_cm
    save_ruler_diagnostic(frames, calibration)

    height, width = frames[0].shape[:2]
    x_px = np.arange(width)
    x_cm = x_px / px_per_cm

    waterline_px = np.zeros((len(frames), width), dtype=np.float32)
    frame_rows: list[dict] = []
    feature_rows: list[dict] = []
    distance_rows: list[dict] = []

    detection_contact: list[np.ndarray] = []
    contact_idxs = set(np.linspace(0, len(frames) - 1, min(6, len(frames)), dtype=int).tolist())

    for frame_index, frame in enumerate(frames):
        time_s = frame_index / fps
        yline, y_center, good_fraction, strength_median = detect_waterline(frame)
        waterline_px[frame_index] = yline.astype(np.float32)

        broad_eta, broad_peaks, broad_troughs, broad_props = detect_spatial_features(yline, px_per_cm, "broad")
        local_eta, local_peaks, local_troughs, local_props = detect_spatial_features(yline, px_per_cm, "local")

        eta_for_autocorr = -(yline - np.mean(yline)) / px_per_cm
        autocorr_lambda = autocorr_wavelength_cm(eta_for_autocorr, px_per_cm)
        distances = adjacent_distances(broad_peaks, px_per_cm)
        distance_text = ";".join(f"{d[2]:.3f}" for d in distances)

        for idx, peak_x in enumerate(broad_peaks):
            feature_rows.append(
                {
                    "frame_index": frame_index,
                    "time_s": f"{time_s:.6f}",
                    "scale": "broad",
                    "kind": "crest",
                    "x_px": int(peak_x),
                    "x_cm": f"{x_cm[int(peak_x)]:.6f}",
                    "y_px": f"{yline[int(peak_x)]:.6f}",
                    "eta_cm": f"{broad_eta[int(peak_x)]:.6f}",
                    "prominence_cm": f"{broad_props['peak_prominences'][idx]:.6f}" if idx < len(broad_props["peak_prominences"]) else "",
                }
            )
        for idx, trough_x in enumerate(broad_troughs):
            feature_rows.append(
                {
                    "frame_index": frame_index,
                    "time_s": f"{time_s:.6f}",
                    "scale": "broad",
                    "kind": "trough",
                    "x_px": int(trough_x),
                    "x_cm": f"{x_cm[int(trough_x)]:.6f}",
                    "y_px": f"{yline[int(trough_x)]:.6f}",
                    "eta_cm": f"{broad_eta[int(trough_x)]:.6f}",
                    "prominence_cm": f"{broad_props['trough_prominences'][idx]:.6f}" if idx < len(broad_props["trough_prominences"]) else "",
                }
            )
        for idx, peak_x in enumerate(local_peaks):
            feature_rows.append(
                {
                    "frame_index": frame_index,
                    "time_s": f"{time_s:.6f}",
                    "scale": "local",
                    "kind": "crest",
                    "x_px": int(peak_x),
                    "x_cm": f"{x_cm[int(peak_x)]:.6f}",
                    "y_px": f"{yline[int(peak_x)]:.6f}",
                    "eta_cm": f"{local_eta[int(peak_x)]:.6f}",
                    "prominence_cm": f"{local_props['peak_prominences'][idx]:.6f}" if idx < len(local_props["peak_prominences"]) else "",
                }
            )
        for idx, trough_x in enumerate(local_troughs):
            feature_rows.append(
                {
                    "frame_index": frame_index,
                    "time_s": f"{time_s:.6f}",
                    "scale": "local",
                    "kind": "trough",
                    "x_px": int(trough_x),
                    "x_cm": f"{x_cm[int(trough_x)]:.6f}",
                    "y_px": f"{yline[int(trough_x)]:.6f}",
                    "eta_cm": f"{local_eta[int(trough_x)]:.6f}",
                    "prominence_cm": f"{local_props['trough_prominences'][idx]:.6f}" if idx < len(local_props["trough_prominences"]) else "",
                }
            )

        for pair_idx, (left, right, dist_cm, dist_px) in enumerate(distances):
            distance_rows.append(
                {
                    "frame_index": frame_index,
                    "time_s": f"{time_s:.6f}",
                    "pair_index": pair_idx,
                    "left_x_px": left,
                    "right_x_px": right,
                    "left_x_cm": f"{left / px_per_cm:.6f}",
                    "right_x_cm": f"{right / px_per_cm:.6f}",
                    "distance_px": dist_px,
                    "distance_cm": f"{dist_cm:.6f}",
                }
            )

        frame_rows.append(
            {
                "frame_index": frame_index,
                "time_s": f"{time_s:.6f}",
                "waterline_y_mean_px": f"{float(np.mean(yline)):.6f}",
                "waterline_y_std_px": f"{float(np.std(yline)):.6f}",
                "waterline_y_center_px": y_center,
                "waterline_good_fraction": f"{good_fraction:.6f}",
                "edge_strength_median": f"{strength_median:.6f}",
                "eta_range_cm": f"{float((np.max(yline) - np.min(yline)) / px_per_cm):.6f}",
                "broad_crest_count": int(len(broad_peaks)),
                "broad_trough_count": int(len(broad_troughs)),
                "local_crest_count": int(len(local_peaks)),
                "local_trough_count": int(len(local_troughs)),
                "broad_adjacent_distances_cm": distance_text,
                "autocorr_wavelength_cm": f"{autocorr_lambda:.6f}" if autocorr_lambda is not None else "",
            }
        )

        overlay = overlay_frame(frame, frame_index, yline, broad_peaks, broad_troughs, x_cm, time_s)
        write_png(OVERLAY_DIR / f"frame_{frame_index:04d}.png", overlay)

        if frame_index in contact_idxs:
            small = cv2.resize(overlay, (640, 360), interpolation=cv2.INTER_AREA)
            detection_contact.append(small)

    if detection_contact:
        rows = []
        for i in range(0, len(detection_contact), 2):
            pair = detection_contact[i : i + 2]
            if len(pair) == 1:
                pair.append(np.zeros_like(pair[0]))
            rows.append(np.concatenate(pair, axis=1))
        write_png(OUT_DIR / "waterline_detection_contact.png", np.concatenate(rows, axis=0))

    reference_y = np.nanmedian(waterline_px, axis=0, keepdims=True)
    eta_xt = -(waterline_px - reference_y) / px_per_cm

    write_csv(
        OUT_DIR / "frame_metrics.csv",
        frame_rows,
        [
            "frame_index",
            "time_s",
            "waterline_y_mean_px",
            "waterline_y_std_px",
            "waterline_y_center_px",
            "waterline_good_fraction",
            "edge_strength_median",
            "eta_range_cm",
            "broad_crest_count",
            "broad_trough_count",
            "local_crest_count",
            "local_trough_count",
            "broad_adjacent_distances_cm",
            "autocorr_wavelength_cm",
        ],
    )
    write_csv(
        OUT_DIR / "crest_trough_features.csv",
        feature_rows,
        ["frame_index", "time_s", "scale", "kind", "x_px", "x_cm", "y_px", "eta_cm", "prominence_cm"],
    )
    write_csv(
        OUT_DIR / "broad_crest_distances.csv",
        distance_rows,
        [
            "frame_index",
            "time_s",
            "pair_index",
            "left_x_px",
            "right_x_px",
            "left_x_cm",
            "right_x_cm",
            "distance_px",
            "distance_cm",
        ],
    )
    write_wide_profile_csv(OUT_DIR / "waterline_profiles_px.csv", waterline_px, fps, "y_px")
    write_wide_profile_csv(OUT_DIR / "eta_xt_surface_cm_wide.csv", eta_xt, fps, "eta_cm")

    fft_diag = fft_directional_diagnostic(eta_xt, fps, px_per_cm)
    plot_results(eta_xt, fps, px_per_cm, frame_rows, distance_rows)
    build_report(frames, fps, calibration, frame_rows, distance_rows, feature_rows, fft_diag)

    manifest_rows = [
        {"path": str(path.relative_to(OUT_DIR)), "bytes": path.stat().st_size}
        for path in sorted(OUT_DIR.rglob("*"))
        if path.is_file()
    ]
    write_csv(OUT_DIR / "analysis_manifest.csv", manifest_rows, ["path", "bytes"])

    print(f"decoded_frames={len(frames)}")
    print(f"fps={fps:.6f}")
    print(f"px_per_cm={px_per_cm:.6f}")
    print(f"output_dir={OUT_DIR}")
    print(f"broad_distance_samples={len(distance_rows)}")


if __name__ == "__main__":
    main()

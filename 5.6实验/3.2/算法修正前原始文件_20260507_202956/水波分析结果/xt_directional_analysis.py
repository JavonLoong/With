from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks, savgol_filter
from skimage.filters import threshold_otsu


@dataclass(frozen=True)
class VideoInfo:
    name: str
    relative_path: str
    px_per_cm: float


VIDEOS = [
    VideoInfo("4.mp4", "5.6实验/3.2/4.mp4", 31.650),
    VideoInfo("5.mp4", "5.6实验/3.7/5.mp4", 35.387),
    VideoInfo("6.mp4", "5.6实验/4.4/6.mp4", 30.160),
]

MAIN_WAVELENGTH_BAND_CM = (18.0, 30.0)
SECONDARY_WAVELENGTH_BAND_CM = (6.0, 17.0)


def ruler_band(gray: np.ndarray) -> tuple[int, int]:
    dark = gray < 70
    row = dark.sum(axis=1)
    ys = np.where(row > 200)[0]
    if len(ys) == 0:
        return int(gray.shape[0] * 0.6), int(gray.shape[0] * 0.7)

    groups: list[tuple[int, int, int]] = []
    start = prev = int(ys[0])
    for y0 in ys[1:]:
        y = int(y0)
        if y == prev + 1:
            prev = y
        else:
            groups.append((start, prev, int(row[start : prev + 1].max())))
            start = prev = y
    groups.append((start, prev, int(row[start : prev + 1].max())))

    candidates = [
        g for g in groups if g[2] > 700 and g[0] > gray.shape[0] * 0.25
    ]
    if not candidates:
        candidates = [g for g in groups if g[0] > gray.shape[0] * 0.25]
    return candidates[-1][0], candidates[-1][1]


def extract_surface_line(rgb: np.ndarray) -> np.ndarray | None:
    gray = rgb.mean(axis=2)
    ry1, _ = ruler_band(gray)
    y0 = 10
    y1 = max(40, ry1 - 25)
    roi = rgb[y0:y1, :, :]
    green = cv2.GaussianBlur(roi[:, :, 1], (9, 9), 0)

    try:
        threshold = float(threshold_otsu(green))
    except Exception:
        threshold = float(np.percentile(green, 60))
    p35, p85 = np.percentile(green, [35, 85])
    threshold = max(threshold, float(p35 + 0.35 * (p85 - p35)))

    mask = green > threshold
    mask = ndi.binary_closing(mask, structure=np.ones((5, 21)))
    mask = ndi.binary_opening(mask, structure=np.ones((3, 7)))
    labels, count = ndi.label(mask)
    if count == 0:
        return None

    objects = ndi.find_objects(labels)
    scored: list[tuple[float, int]] = []
    for label_id, slices in enumerate(objects, start=1):
        if slices is None:
            continue
        yy, xx = slices
        area = int((labels[slices] == label_id).sum())
        width = xx.stop - xx.start
        bottom = yy.stop
        score = area + 50 * width
        if bottom > 0.75 * (y1 - y0):
            score += 100000
        scored.append((score, label_id))
    if not scored:
        return None

    component = max(scored)[1]
    component_mask = labels == component
    xs = np.arange(rgb.shape[1])
    ys = np.full(rgb.shape[1], np.nan)
    for x in range(rgb.shape[1]):
        column = np.where(component_mask[:, x])[0]
        if len(column):
            ys[x] = column[0] + y0

    good = np.isfinite(ys)
    if good.sum() < rgb.shape[1] * 0.4:
        return None

    ys = np.interp(xs, xs[good], ys[good])
    ys = ndi.median_filter(ys, size=21, mode="nearest")
    return savgol_filter(ys, 151, 3, mode="interp")


def load_surface_lines(video_path: Path, out_dir: Path) -> tuple[np.ndarray, float]:
    stem = video_path.stem
    cached = out_dir / f"{stem}_surface_lines.npy"
    fps_cache = out_dir / f"{stem}_fps.txt"
    if cached.exists() and fps_cache.exists():
        return np.load(cached), float(fps_cache.read_text().strip())

    cap = cv2.VideoCapture(video_path.as_posix())
    if not cap.isOpened():
        raise RuntimeError(f"Could not open {video_path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    lines: list[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        line = extract_surface_line(rgb)
        if line is not None:
            lines.append(line)
    cap.release()

    if not lines:
        raise RuntimeError(f"No surface lines extracted from {video_path}")

    arr = np.vstack(lines)
    np.save(cached, arr)
    fps_cache.write_text(f"{fps:.12g}")
    return arr, fps


def eta_field(lines: np.ndarray) -> np.ndarray:
    # Pixel y grows downward; eta should grow upward.
    eta = np.median(lines, axis=1, keepdims=True) - lines
    eta -= np.mean(eta, axis=0, keepdims=True)
    eta -= np.mean(eta, axis=1, keepdims=True)
    return eta


def directional_fft(
    eta: np.ndarray, fps: float, px_per_cm: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    dt = 1.0 / fps
    dx = 1.0 / px_per_cm
    window_t = np.hanning(eta.shape[0])[:, None]
    window_x = np.hanning(eta.shape[1])[None, :]
    windowed = eta * window_t * window_x
    spectrum = np.fft.fftshift(np.fft.fft2(windowed))
    ft = np.fft.fftshift(np.fft.fftfreq(eta.shape[0], d=dt))
    kx = np.fft.fftshift(np.fft.fftfreq(eta.shape[1], d=dx))
    FT, KX = np.meshgrid(ft, kx, indexing="ij")
    power = np.abs(spectrum) ** 2
    return spectrum, power, ft, kx, FT * KX


def band_mask(
    ft: np.ndarray,
    kx: np.ndarray,
    wavelength_band_cm: tuple[float, float],
    direction: str,
    min_temporal_hz: float = 0.15,
) -> np.ndarray:
    lo_cm, hi_cm = wavelength_band_cm
    k_abs = np.abs(kx)[None, :]
    f_abs = np.abs(ft)[:, None]
    KX, FT = np.meshgrid(kx, ft)
    band = (k_abs >= 1.0 / hi_cm) & (k_abs <= 1.0 / lo_cm) & (f_abs >= min_temporal_hz)
    if direction == "right":
        return band & (KX * FT < 0)
    if direction == "left":
        return band & (KX * FT > 0)
    return band


def dominant_wavelength(
    power: np.ndarray,
    ft: np.ndarray,
    kx: np.ndarray,
    wavelength_band_cm: tuple[float, float],
    direction: str,
) -> tuple[float, float, float]:
    mask = band_mask(ft, kx, wavelength_band_cm, direction)
    if not np.any(mask):
        return np.nan, np.nan, np.nan

    score = np.where(mask, power, 0.0).sum(axis=0)
    abs_k = np.abs(kx)
    valid = score > 0
    unique_k: dict[float, float] = {}
    for k, s in zip(abs_k[valid], score[valid]):
        if k == 0:
            continue
        key = float(np.round(k, 8))
        unique_k[key] = unique_k.get(key, 0.0) + float(s)
    if not unique_k:
        return np.nan, np.nan, np.nan

    ks = np.array(sorted(unique_k))
    ss = np.array([unique_k[float(k)] for k in ks])
    ss = ndi.gaussian_filter1d(ss, sigma=1.0, mode="nearest")
    peak_idx = int(np.argmax(ss))
    peak_k = float(ks[peak_idx])
    lo = max(0, peak_idx - 2)
    hi = min(len(ks), peak_idx + 3)
    weights = ss[lo:hi]
    weighted_k = float(np.sum(ks[lo:hi] * weights) / np.sum(weights))
    wavelength = 1.0 / weighted_k

    total_dir_energy = float(np.where(mask, power, 0.0).sum())
    return wavelength, peak_k, total_dir_energy


def inverse_direction_component(
    spectrum: np.ndarray,
    ft: np.ndarray,
    kx: np.ndarray,
    wavelength_band_cm: tuple[float, float],
    direction: str,
) -> np.ndarray:
    mask = band_mask(ft, kx, wavelength_band_cm, direction)
    filtered = np.zeros_like(spectrum)
    filtered[mask] = spectrum[mask]
    return np.real(np.fft.ifft2(np.fft.ifftshift(filtered)))


def window_estimates(
    eta: np.ndarray,
    fps: float,
    px_per_cm: float,
    wavelength_band_cm: tuple[float, float],
    direction: str,
    window_s: float,
    step_s: float,
) -> list[dict[str, float]]:
    n = eta.shape[0]
    win = max(16, int(round(window_s * fps)))
    step = max(1, int(round(step_s * fps)))
    rows: list[dict[str, float]] = []
    for start in range(0, max(1, n - win + 1), step):
        stop = min(n, start + win)
        if stop - start < 16:
            continue
        chunk = eta[start:stop]
        _, power, ft, kx, _ = directional_fft(chunk, fps, px_per_cm)
        lam, peak_k, energy = dominant_wavelength(power, ft, kx, wavelength_band_cm, direction)
        if np.isfinite(lam):
            rows.append(
                {
                    "start_s": start / fps,
                    "end_s": stop / fps,
                    "center_s": (start + stop) / (2 * fps),
                    "wavelength_cm": lam,
                    "peak_k_cycles_per_cm": peak_k,
                    "energy": energy,
                }
            )
    return rows


def naive_main_distances(csv_path: Path, video_name: str) -> list[float]:
    if not csv_path.exists():
        return []
    vals: list[float] = []
    with csv_path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["video"] != video_name:
                continue
            distance = float(row["distance_cm"])
            if MAIN_WAVELENGTH_BAND_CM[0] <= distance <= MAIN_WAVELENGTH_BAND_CM[1]:
                vals.append(distance)
    return vals


def draw_directional_plots(
    out_dir: Path,
    stem: str,
    eta: np.ndarray,
    fps: float,
    px_per_cm: float,
    incident: np.ndarray,
    right_lambda: float,
    left_lambda: float,
) -> None:
    duration = eta.shape[0] / fps
    width_cm = eta.shape[1] / px_per_cm
    vmax = float(np.percentile(np.abs(eta), 98))
    incident_vmax = float(np.percentile(np.abs(incident), 98))
    if incident_vmax == 0:
        incident_vmax = 1.0

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.2), dpi=170, sharey=True)
    extent = [0, width_cm, duration, 0]
    axes[0].imshow(eta, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax, extent=extent)
    axes[0].set_title(f"{stem}.mp4 full x-t field")
    axes[0].set_xlabel("position (cm, relative)")
    axes[0].set_ylabel("time (s)")
    axes[1].imshow(
        incident,
        aspect="auto",
        cmap="RdBu_r",
        vmin=-incident_vmax,
        vmax=incident_vmax,
        extent=extent,
    )
    axes[1].set_title(
        f"dominant-direction component\nright={right_lambda:.2f} cm, left={left_lambda:.2f} cm"
    )
    axes[1].set_xlabel("position (cm, relative)")
    fig.tight_layout()
    fig.savefig(out_dir / f"{stem}_xt_direction_filtered.png")
    plt.close(fig)


def summarize_video(video: VideoInfo, root: Path, out_dir: Path) -> dict[str, float | str | int]:
    video_path = root / video.relative_path
    lines, fps = load_surface_lines(video_path, out_dir)
    eta = eta_field(lines)
    spectrum, power, ft, kx, _ = directional_fft(eta, fps, video.px_per_cm)

    right_lam, _, right_energy = dominant_wavelength(
        power, ft, kx, MAIN_WAVELENGTH_BAND_CM, "right"
    )
    left_lam, _, left_energy = dominant_wavelength(
        power, ft, kx, MAIN_WAVELENGTH_BAND_CM, "left"
    )
    incident_direction = "right" if right_energy >= left_energy else "left"
    incident_lam = right_lam if incident_direction == "right" else left_lam
    reflection_lam = left_lam if incident_direction == "right" else right_lam
    incident_energy = max(right_energy, left_energy)
    reflection_energy = min(right_energy, left_energy)
    reflection_ratio = reflection_energy / incident_energy if incident_energy else np.nan

    secondary_lam, _, secondary_energy = dominant_wavelength(
        power, ft, kx, SECONDARY_WAVELENGTH_BAND_CM, incident_direction
    )

    window_s = min(1.2, max(0.8, lines.shape[0] / fps * 0.35))
    windows = window_estimates(
        eta,
        fps,
        video.px_per_cm,
        MAIN_WAVELENGTH_BAND_CM,
        incident_direction,
        window_s=window_s,
        step_s=0.15,
    )
    if windows:
        with (out_dir / f"{video_path.stem}_incident_window_wavelengths.csv").open(
            "w", newline="", encoding="utf-8-sig"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=list(windows[0].keys()))
            writer.writeheader()
            writer.writerows(windows)
        window_lams = np.array([row["wavelength_cm"] for row in windows])
        stable_mask = np.abs(window_lams - np.nanmedian(window_lams)) <= 1.0
        stable_lams = window_lams[stable_mask] if np.any(stable_mask) else window_lams
        window_mean = float(np.nanmean(stable_lams))
        window_std = float(np.nanstd(stable_lams, ddof=1)) if len(stable_lams) > 1 else 0.0
        window_n = int(len(stable_lams))
        window_min_t = float(min(row["start_s"] for row in windows))
        window_max_t = float(max(row["end_s"] for row in windows))
    else:
        window_mean = window_std = window_min_t = window_max_t = np.nan
        window_n = 0

    incident = inverse_direction_component(
        spectrum, ft, kx, MAIN_WAVELENGTH_BAND_CM, incident_direction
    )
    draw_directional_plots(
        out_dir,
        video_path.stem,
        eta,
        fps,
        video.px_per_cm,
        incident,
        right_lam,
        left_lam,
    )

    naive_vals = naive_main_distances(out_dir / "crest_distances.csv", video.name)
    if naive_vals:
        naive_mean = float(np.mean(naive_vals))
        naive_std = float(np.std(naive_vals, ddof=1)) if len(naive_vals) > 1 else 0.0
        naive_n = len(naive_vals)
        delta_vs_naive = incident_lam - naive_mean
        pct_vs_naive = 100.0 * delta_vs_naive / naive_mean
    else:
        naive_mean = naive_std = delta_vs_naive = pct_vs_naive = np.nan
        naive_n = 0

    return {
        "video": video.name,
        "frames_used": int(lines.shape[0]),
        "duration_s": lines.shape[0] / fps,
        "px_per_cm": video.px_per_cm,
        "incident_direction": incident_direction,
        "incident_fft_lambda_cm": incident_lam,
        "opposite_fft_lambda_cm": reflection_lam,
        "opposite_to_incident_energy_ratio": reflection_ratio,
        "secondary_incident_lambda_cm": secondary_lam,
        "secondary_to_main_energy_ratio": secondary_energy / incident_energy
        if incident_energy
        else np.nan,
        "stable_window_mean_cm": window_mean,
        "stable_window_std_cm": window_std,
        "stable_window_n": window_n,
        "window_time_span_s": f"{window_min_t:.3f}-{window_max_t:.3f}",
        "naive_main_mean_cm": naive_mean,
        "naive_main_std_cm": naive_std,
        "naive_main_n": naive_n,
        "delta_incident_minus_naive_cm": delta_vs_naive,
        "percent_delta_vs_naive": pct_vs_naive,
    }


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    learning_dir = out_dir.parent
    root = learning_dir.parent

    rows = [summarize_video(video, root, out_dir) for video in VIDEOS]
    out_csv = out_dir / "xt_directional_summary.csv"
    with out_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    for row in rows:
        print(row)
    print(out_csv)


if __name__ == "__main__":
    main()

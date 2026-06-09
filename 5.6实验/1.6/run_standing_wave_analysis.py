from __future__ import annotations

from pathlib import Path
import csv
import math
import shutil
import sys

import cv2
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import median_filter, gaussian_filter1d
from scipy.signal import savgol_filter, find_peaks, detrend


plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def write_png(path: Path, img: np.ndarray) -> None:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError(f"cannot encode {path}")
    path.write_bytes(buf.tobytes())


def load_video(video: Path) -> tuple[list[np.ndarray], float]:
    cap = cv2.VideoCapture(video.name)
    frames: list[np.ndarray] = []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame is not None and frame.size:
            frames.append(frame)
    cap.release()
    if frames:
        return frames, float(fps)

    # Fallback for HEVC builds where OpenCV cannot decode.
    try:
        import imageio_ffmpeg

        reader = imageio_ffmpeg.read_frames(str(video), pix_fmt="bgr24")
        meta = next(reader)
        fps = float(meta.get("fps", 30.0) or 30.0)
        w, h = meta["size"]
        frames = []
        for raw in reader:
            arr = np.frombuffer(raw, dtype=np.uint8)
            if arr.size == w * h * 3:
                frames.append(arr.reshape((h, w, 3)).copy())
        return frames, fps
    except Exception as exc:  # pragma: no cover - diagnostic fallback
        raise RuntimeError(f"cannot decode video {video}: {exc}") from exc


def select_valid_frames(frames: list[np.ndarray]) -> tuple[list[np.ndarray], list[int]]:
    valid = []
    bad = []
    for i, f in enumerate(frames):
        gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        if gray.mean() < 8 or gray.std() < 3:
            bad.append(i)
        else:
            valid.append(f)
    return valid, bad


def contact_sheet(frames: list[np.ndarray], out: Path) -> None:
    if not frames:
        return
    n = len(frames)
    picks = [0, max(0, n // 3), max(0, 2 * n // 3), max(0, n - 1)]
    small = []
    for idx in picks:
        f = frames[idx].copy()
        cv2.putText(f, f"frame {idx}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        small.append(cv2.resize(f, (480, 270)))
    canvas = np.vstack([np.hstack(small[:2]), np.hstack(small[2:])])
    write_png(out, canvas)


def find_ruler_band(frame: np.ndarray) -> tuple[int, int]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    y0, y1 = int(h * 0.55), int(h * 0.78)
    crop = gray[y0:y1]
    # The ruler band has many dark digits/ticks and horizontal dark lines.
    dark = (crop < np.percentile(crop, 28)).astype(np.uint8)
    row_score = dark.sum(axis=1).astype(float)
    row_score = gaussian_filter1d(row_score, 2.5)
    yc = y0 + int(np.argmax(row_score))
    top = max(0, yc - int(h * 0.045))
    bot = min(h, yc + int(h * 0.045))
    return top, bot


def estimate_px_per_cm(frame: np.ndarray, out_dir: Path) -> tuple[float, float, dict[str, float]]:
    h, w = frame.shape[:2]
    y0, y1 = find_ruler_band(frame)
    crop = frame[y0:y1, :]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    # Enhance dark tick/text structure.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    eq = clahe.apply(gray)
    mask = (eq < np.percentile(eq, 34)).astype(np.float32)
    proj = mask.sum(axis=0)
    proj -= gaussian_filter1d(proj, 18)
    proj -= proj.mean()
    proj /= proj.std() + 1e-9

    min_lag = max(10, int(w / 90))
    max_lag = min(60, int(w / 15))
    lags = np.arange(min_lag, max_lag + 1)
    ac = []
    for lag in lags:
        ac.append(float(np.dot(proj[:-lag], proj[lag:]) / max(1, len(proj) - lag)))
    ac = np.array(ac)
    # Prefer cm-period peak, but avoid tiny digit-stroke harmonics.
    peaks, props = find_peaks(ac, prominence=max(0.02, 0.12 * np.std(ac)))
    if len(peaks):
        p = peaks[np.argmax(ac[peaks])]
        px_ac = float(lags[p])
    else:
        px_ac = float(lags[np.argmax(ac)])

    # FFT cross-check in plausible cm-period range.
    freqs = np.fft.rfftfreq(len(proj), d=1.0)
    power = np.abs(np.fft.rfft(proj)) ** 2
    periods = np.divide(1.0, freqs, out=np.full_like(freqs, np.inf), where=freqs > 0)
    band = (periods >= min_lag) & (periods <= max_lag)
    if np.any(band):
        idx = np.where(band)[0][np.argmax(power[band])]
        px_fft = float(periods[idx])
    else:
        px_fft = px_ac

    # Digit/text periodicity can lock to half-centimeter in some crops. If the
    # strongest period is too small for this video scale, test its 2x harmonic.
    candidates = [px_ac, px_fft]
    for p in list(candidates):
        if p * 2 <= max_lag:
            candidates.append(p * 2)
    candidates = [p for p in candidates if min_lag <= p <= max_lag]
    px_per_cm = float(np.median(candidates))

    # Snap to a nearby strong autocorrelation peak if available.
    near = [float(lags[i]) for i in peaks if abs(float(lags[i]) - px_per_cm) < 0.18 * px_per_cm]
    if near:
        px_per_cm = float(np.median(near + [px_per_cm]))

    spread = float(np.std(candidates)) if len(candidates) > 1 else max(0.02 * px_per_cm, 0.2)

    diag = frame.copy()
    cv2.rectangle(diag, (0, y0), (w - 1, y1), (0, 0, 255), 2)
    txt = f"px/cm={px_per_cm:.3f}, ac={px_ac:.2f}, fft={px_fft:.2f}"
    cv2.putText(diag, txt, (20, max(30, y0 - 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    write_png(out_dir / "ruler_calibration_diagnostic.png", diag)

    with (out_dir / "ruler_calibration.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["item", "value"])
        writer.writerow(["px_per_cm", f"{px_per_cm:.8f}"])
        writer.writerow(["cm_per_px", f"{1 / px_per_cm:.10f}"])
        writer.writerow(["diagnostic_std_px_per_cm", f"{spread:.8f}"])
        writer.writerow(["autocorr_px", f"{px_ac:.8f}"])
        writer.writerow(["fft_px", f"{px_fft:.8f}"])
        writer.writerow(["ruler_band_y0", y0])
        writer.writerow(["ruler_band_y1", y1])

    return px_per_cm, spread, {"autocorr_px": px_ac, "fft_px": px_fft, "y0": y0, "y1": y1}


def extract_waterline(frames: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray, tuple[int, int]]:
    h, w = frames[0].shape[:2]
    # Free surface is near upper edge of bright green/cyan water. Use lower half
    # enough for low-amplitude early frames, but avoid ruler band.
    y0, y1 = int(h * 0.32), int(h * 0.68)
    xs = np.arange(w)
    lines = []
    for frame in frames:
        b, g, r = cv2.split(frame)
        score = 0.55 * g.astype(np.float32) + 0.55 * b.astype(np.float32) - 0.18 * r.astype(np.float32)
        score = cv2.GaussianBlur(score, (5, 5), 0)
        roi = score[y0:y1]
        grad = np.gradient(roi, axis=0)
        lo, hi = max(4, int(0.03 * (y1 - y0))), int(0.92 * (y1 - y0))
        sub = grad[lo:hi]
        krel = np.argmax(sub, axis=0)
        strengths = sub[krel, np.arange(w)]
        y = (y0 + lo + krel).astype(np.float32)
        weak = strengths < np.percentile(strengths, 18)
        y[weak] = np.nan
        valid = np.isfinite(y)
        if valid.sum() > max(50, int(0.15 * w)):
            y = np.interp(xs, xs[valid], y[valid]).astype(np.float32)
        else:
            y = np.nan_to_num(y, nan=np.nanmedian(y)).astype(np.float32)
        y = median_filter(y, size=max(7, (w // 80) | 1), mode="nearest")
        win = max(31, ((w // 12) | 1))
        if win >= w:
            win = w - 1 if (w - 1) % 2 else w - 2
        y = savgol_filter(y, win, 3, mode="interp").astype(np.float32)
        lines.append(y)
    lines_arr = np.vstack(lines)
    return xs, lines_arr, (y0, y1)


def save_waterline_check(frame: np.ndarray, yline: np.ndarray, out: Path, title: str = "") -> None:
    img = frame.copy()
    pts = np.column_stack([np.arange(len(yline)), np.round(yline).astype(int)]).reshape(-1, 1, 2)
    cv2.polylines(img, [pts], False, (0, 0, 255), 2, cv2.LINE_AA)
    if title:
        cv2.putText(img, title, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    write_png(out, img)


def direction_filter(eta: np.ndarray, fps: float, dx_cm: float) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    z = eta.astype(float)
    z = detrend(z, axis=0, type="linear")
    z = detrend(z, axis=1, type="linear")
    z -= z.mean()
    nt, nx = z.shape
    f = np.fft.fftfreq(nt, d=1.0 / fps)
    k = np.fft.fftfreq(nx, d=dx_cm)
    F = np.fft.fft2(z)
    FT, KX = np.meshgrid(f, k, indexing="ij")
    band = (
        (np.abs(FT) >= 0.25)
        & (np.abs(FT) <= 5.0)
        & (np.abs(KX) >= 1 / 65.0)
        & (np.abs(KX) <= 1 / 6.0)
    )
    pos = band & ((FT * KX) > 0)
    neg = band & ((FT * KX) < 0)
    power = np.abs(F) ** 2
    epos = float(power[pos].sum())
    eneg = float(power[neg].sum())
    # Use the stronger direction as incident.
    inc_mask = pos if epos >= eneg else neg
    ref_mask = neg if epos >= eneg else pos
    inc = np.real(np.fft.ifft2(F * inc_mask))
    ref = np.real(np.fft.ifft2(F * ref_mask))
    ratio = min(epos, eneg) / max(epos, eneg) if max(epos, eneg) > 0 else float("nan")

    # Dominant diagnostic wavelength on incident mask.
    masked_power = np.where(inc_mask, power, 0)
    masked_power[np.abs(FT) < 0.25] = 0
    masked_power[np.abs(KX) < 1 / 65] = 0
    idx = np.unravel_index(np.argmax(masked_power), masked_power.shape)
    k0 = abs(float(KX[idx]))
    f0 = abs(float(FT[idx]))
    lam = 1.0 / k0 if k0 > 1e-9 else float("nan")
    sign = "+x/right" if (epos >= eneg and np.any(pos)) else "-x/left"
    return inc, ref, {
        "global_reflection_ratio": ratio,
        "energy_pos": epos,
        "energy_neg": eneg,
        "fft_lambda_cm": lam,
        "fft_freq_hz": f0,
        "incident_direction": sign,
    }


def window_reflection_series(
    inc: np.ndarray, ref: np.ndarray, time: np.ndarray, fps: float, win_s: float = 0.9
) -> list[dict[str, float]]:
    win = max(8, int(round(win_s * fps)))
    step = max(1, int(round(0.1 * fps)))
    rows = []
    n = inc.shape[0]
    for start in range(0, max(1, n - win + 1), step):
        end = min(n, start + win)
        ir = float(np.sqrt(np.mean(inc[start:end] ** 2)))
        rr = float(np.sqrt(np.mean(ref[start:end] ** 2)))
        ratio = (rr / ir) ** 2 if ir > 1e-12 else float("nan")
        rows.append(
            {
                "start_frame": start,
                "end_frame": end,
                "center_s": float(time[(start + end - 1) // 2]),
                "incident_rms": ir,
                "reflected_rms": rr,
                "reflection_energy_ratio": ratio,
                "reflection_amplitude_ratio": rr / ir if ir > 1e-12 else float("nan"),
            }
        )
    return rows


def choose_stable_window(rows: list[dict[str, float]]) -> tuple[int, int, dict[str, float]]:
    finite = [r for r in rows if np.isfinite(r["reflection_energy_ratio"]) and r["incident_rms"] > 1e-5]
    if not finite:
        r = rows[0]
        return int(r["start_frame"]), int(r["end_frame"]), r
    incident_vals = np.array([r["incident_rms"] for r in finite])
    cutoff = np.percentile(incident_vals, 35)
    candidates = [r for r in finite if r["incident_rms"] >= cutoff]
    chosen = min(candidates, key=lambda r: r["reflection_energy_ratio"])
    return int(chosen["start_frame"]), int(chosen["end_frame"]), chosen


def autocorr_period(Z: np.ndarray, dx_cm: float, lo: float = 8.0, hi: float = 42.0) -> tuple[float, float, int]:
    periods = []
    for row in Z:
        row = detrend(row, type="linear")
        row = row - row.mean()
        den = float(np.dot(row, row))
        if den < 1e-12:
            continue
        corr = np.correlate(row, row, mode="full")[len(row) - 1 :] / den
        lags = np.arange(len(corr)) * dx_cm
        mask = (lags >= lo) & (lags <= hi)
        idxs = np.where(mask)[0]
        if idxs.size == 0:
            continue
        sm = savgol_filter(corr, min(51, idxs.size if idxs.size % 2 else idxs.size - 1), 3, mode="interp")
        peaks, props = find_peaks(sm[idxs], prominence=0.015)
        if len(peaks):
            p = idxs[peaks[np.argmax(sm[idxs][peaks])]]
        else:
            p = idxs[np.argmax(sm[idxs])]
        periods.append(float(lags[p]))
    if not periods:
        return float("nan"), float("nan"), 0
    arr = np.array(periods)
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    return med, mad, len(periods)


def peak_distances(Z: np.ndarray, dx_cm: float, period_hint: float) -> tuple[float, float, int, list[float]]:
    distances = []
    min_dist = max(5, int(round(max(6.0, 0.45 * period_hint) / dx_cm))) if np.isfinite(period_hint) else int(8 / dx_cm)
    for row in Z:
        row = savgol_filter(row, min(41, len(row) if len(row) % 2 else len(row) - 1), 3, mode="interp")
        row = detrend(row, type="linear")
        prom = max(0.20 * np.std(row), 0.002)
        peaks, _ = find_peaks(row, distance=min_dist, prominence=prom)
        if len(peaks) >= 2:
            ds = np.diff(peaks) * dx_cm
            if np.isfinite(period_hint):
                ds = ds[(ds >= 0.55 * period_hint) & (ds <= 1.45 * period_hint)]
            else:
                ds = ds[(ds >= 8.0) & (ds <= 45.0)]
            distances.extend([float(d) for d in ds])
    if not distances:
        return float("nan"), float("nan"), 0, []
    arr = np.array(distances)
    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    return med, mad, len(distances), distances


def plot_xt(time: np.ndarray, x_cm: np.ndarray, raw: np.ndarray, inc: np.ndarray, ref: np.ndarray, out: Path) -> None:
    vmax = np.nanpercentile(np.abs(raw), 98)
    vmax = max(vmax, 1e-6)
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), dpi=150, sharex=True, sharey=True)
    for ax, z, title in zip(axes, [raw, inc, ref], ["原始水面位移", "方向分离：入射分量", "方向分离：反射分量"]):
        im = ax.imshow(
            z,
            aspect="auto",
            origin="lower",
            cmap="RdBu_r",
            extent=[x_cm[0], x_cm[-1], time[0], time[-1]],
            vmin=-vmax,
            vmax=vmax,
        )
        ax.set_title(title)
        ax.set_ylabel("时间 (s)")
    axes[-1].set_xlabel("水平位置 (cm)")
    fig.colorbar(im, ax=axes, label="相对水面位移 (cm)", shrink=0.9)
    plt.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_reflection(rows: list[dict[str, float]], out: Path) -> None:
    t = [r["center_s"] for r in rows]
    ratio = [r["reflection_energy_ratio"] for r in rows]
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=150)
    ax.plot(t, ratio, "-o", ms=3)
    ax.axhline(0.05, color="green", ls="--", lw=1, label="5%")
    ax.axhline(0.10, color="orange", ls="--", lw=1, label="10%")
    ax.set_xlabel("时间 (s)")
    ax.set_ylabel("反射/入射能量比")
    ax.set_title("反射强度随时间变化")
    ax.grid(True, alpha=0.25)
    ax.legend()
    plt.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_judgement(
    direct: float,
    inc: float,
    refl: float,
    fft_lam: float,
    out: Path,
    group: str,
) -> None:
    fig, ax1 = plt.subplots(figsize=(9, 5), dpi=150)
    labels = ["直接峰距", "入射剖面峰距"]
    vals = [direct, inc]
    ax1.bar(labels, vals, color=["#4C78A8", "#F58518"], alpha=0.85)
    ax1.set_ylabel("波长 / 峰距 (cm)")
    ax1.set_title(f"数据组 {group}：直接峰距与入射分量对比")
    if np.isfinite(fft_lam):
        ax1.axhline(fft_lam, color="gray", ls=":", label=f"FFT诊断值 {fft_lam:.2f} cm")
    ax2 = ax1.twinx()
    ax2.plot([0, 1], [refl, refl], color="crimson", marker="o", label=f"反射/入射能量比 {refl:.3f}")
    ax2.set_ylim(0, max(0.2, refl * 1.6))
    ax2.set_ylabel("反射/入射能量比")
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
    plt.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def wave_measurement_plot(
    frame: np.ndarray,
    yline: np.ndarray,
    px_per_cm: float,
    direct_period: float,
    out: Path,
    frame_idx: int,
) -> None:
    img = frame.copy()
    pts = np.column_stack([np.arange(len(yline)), np.round(yline).astype(int)]).reshape(-1, 1, 2)
    cv2.polylines(img, [pts], False, (0, 0, 255), 2, cv2.LINE_AA)
    row = -yline.astype(float)
    row = savgol_filter(row, min(81, len(row) if len(row) % 2 else len(row) - 1), 3, mode="interp")
    min_dist = max(5, int(round(max(8.0, 0.55 * direct_period) * px_per_cm)))
    peaks, _ = find_peaks(row, distance=min_dist, prominence=max(0.15 * np.std(row), 0.4))
    if len(peaks) >= 2:
        # choose pair closest to period.
        ds = np.diff(peaks) / px_per_cm
        j = int(np.argmin(np.abs(ds - direct_period)))
        p1, p2 = int(peaks[j]), int(peaks[j + 1])
        y1, y2 = int(round(yline[p1])), int(round(yline[p2]))
        cv2.drawMarker(img, (p1, y1), (255, 0, 0), cv2.MARKER_CROSS, 24, 2)
        cv2.drawMarker(img, (p2, y2), (255, 0, 0), cv2.MARKER_CROSS, 24, 2)
        cv2.line(img, (p1, y1), (p2, y2), (0, 255, 255), 2)
        label = f"peak distance {ds[j]:.2f} cm"
    else:
        label = f"period estimate {direct_period:.2f} cm"
    cv2.putText(img, f"frame {frame_idx}, {label}", (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 255, 255), 2)
    write_png(out, img)


def analyze_group(group_dir: Path) -> dict[str, object]:
    video = next(group_dir.glob("*.mp4"))
    frames_all, fps = load_video(video)
    frames, bad = select_valid_frames(frames_all)
    if len(frames) < 10:
        raise RuntimeError("too few valid frames")
    n = len(frames)
    h, w = frames[0].shape[:2]
    time = np.arange(n) / fps
    contact_sheet(frames, group_dir / "__contact_sheet.png")
    px_per_cm, px_spread, cal_diag = estimate_px_per_cm(frames[min(n - 1, n // 2)], group_dir)
    dx_cm = 1.0 / px_per_cm
    xs_px, ylines, roi = extract_waterline(frames)
    mid = min(n - 1, max(0, n // 2))
    save_waterline_check(frames[mid], ylines[mid], group_dir / "waterline_extraction_check.png", f"frame {mid}")

    eta_px = -ylines
    eta_px = eta_px - np.median(eta_px, axis=0, keepdims=True)
    eta_px = eta_px - np.median(eta_px, axis=1, keepdims=True)
    eta_cm = eta_px * dx_cm
    eta_cm = median_filter(eta_cm, size=(1, 5), mode="nearest")
    inc, ref, dmeta = direction_filter(eta_cm, fps, dx_cm)
    rows = window_reflection_series(inc, ref, time, fps)
    start, end, chosen = choose_stable_window(rows)
    raw_win = eta_cm[start:end]
    inc_win = inc[start:end]
    direct_ac, direct_ac_mad, direct_ac_n = autocorr_period(raw_win, dx_cm)
    inc_ac, inc_ac_mad, inc_ac_n = autocorr_period(inc_win, dx_cm)
    direct_peak, direct_mad, direct_n, direct_dist = peak_distances(raw_win, dx_cm, direct_ac)
    inc_peak, inc_mad, inc_n, inc_dist = peak_distances(inc_win, dx_cm, inc_ac)

    # Prefer peak distances if enough samples, otherwise autocorrelation.
    direct_main = direct_peak if direct_n >= 3 and np.isfinite(direct_peak) else direct_ac
    inc_main = inc_peak if inc_n >= 3 and np.isfinite(inc_peak) else inc_ac
    direct_unc = direct_mad if direct_n >= 3 and np.isfinite(direct_mad) else direct_ac_mad
    inc_unc = inc_mad if inc_n >= 3 and np.isfinite(inc_mad) else inc_ac_mad
    diff = direct_main - inc_main
    rel = abs(diff) / inc_main * 100 if np.isfinite(inc_main) and inc_main else float("nan")
    refl = float(chosen["reflection_energy_ratio"])

    if refl < 0.05 and rel < 3:
        judgement = "反射较弱，不需要强驻波修正"
    elif refl < 0.12 and rel < 6:
        judgement = "反射影响中等，建议纳入不确定度"
    else:
        judgement = "需要考虑反射/驻波影响"

    # Plots.
    x_cm = xs_px * dx_cm
    plot_xt(time, x_cm, eta_cm, inc, ref, group_dir / "xt_raw_incident_reflected_panels.png")
    plot_reflection(rows, group_dir / "reflection_strength.png")
    plot_judgement(direct_main, inc_main, refl, dmeta["fft_lambda_cm"], group_dir / "standing_wave_judgement_cn.png", group_dir.name)
    rep_idx = min(n - 1, max(start, (start + end) // 2))
    wave_measurement_plot(frames[rep_idx], ylines[rep_idx], px_per_cm, direct_main, group_dir / "wave_peak_measurement.png", rep_idx)

    # Data files.
    np.savez_compressed(
        group_dir / "standing_wave_analysis_data.npz",
        eta_cm=eta_cm,
        eta_incident_cm=inc,
        eta_reflected_cm=ref,
        surface_y_px=ylines,
        time_s=time,
        x_cm=x_cm,
        fps=fps,
        px_per_cm=px_per_cm,
    )
    # Downsample x for CSV if needed to keep file reasonable.
    step = max(1, w // 640)
    with (group_dir / "eta_xt_surface_cm.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["time_s"] + [f"x_{x:.3f}_cm" for x in x_cm[::step]])
        for t, row in zip(time, eta_cm):
            writer.writerow([f"{t:.6f}"] + [f"{v:.7f}" for v in row[::step]])
    with (group_dir / "reflection_time_series.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with (group_dir / "peak_measurements.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["type", "distance_cm"])
        for d in direct_dist:
            writer.writerow(["direct_peak", f"{d:.6f}"])
        for d in inc_dist:
            writer.writerow(["incident_peak", f"{d:.6f}"])

    summary = {
        "数据组": group_dir.name,
        "视频": video.name,
        "读取帧数": len(frames_all),
        "分析帧数": n,
        "剔除无效帧索引": ";".join(map(str, bad)) if bad else "",
        "帧率_fps": f"{fps:.6f}",
        "时长_s": f"{len(frames_all) / fps:.6f}",
        "px_per_cm": f"{px_per_cm:.6f}",
        "px_per_cm诊断散布": f"{px_spread:.6f}",
        "视场宽度_cm": f"{x_cm[-1] - x_cm[0]:.6f}",
        "稳定窗口_start_s": f"{time[start]:.6f}",
        "稳定窗口_end_s": f"{time[min(end - 1, n - 1)]:.6f}",
        "窗口反射入射能量比": f"{refl:.6f}",
        "直接峰距_cm": f"{direct_main:.6f}",
        "直接峰距不确定度_cm": f"{direct_unc:.6f}",
        "直接峰距样本数": direct_n if direct_n else direct_ac_n,
        "直接自相关主周期_cm": f"{direct_ac:.6f}",
        "入射峰距_cm": f"{inc_main:.6f}",
        "入射峰距不确定度_cm": f"{inc_unc:.6f}",
        "入射峰距样本数": inc_n if inc_n else inc_ac_n,
        "入射自相关主周期_cm": f"{inc_ac:.6f}",
        "FFT诊断波长_cm": f"{dmeta['fft_lambda_cm']:.6f}",
        "FFT主频_Hz": f"{dmeta['fft_freq_hz']:.6f}",
        "入射方向": dmeta["incident_direction"],
        "全局反射入射能量比": f"{dmeta['global_reflection_ratio']:.6f}",
        "差值_直接减入射_cm": f"{diff:.6f}",
        "相对差异_pct": f"{rel:.6f}",
        "判断": judgement,
        "FFT说明": "全帧2D FFT仅作诊断；短视频/有限视场下不单独作为最终高精度波长。",
    }
    with (group_dir / "standing_wave_summary_cn.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    report = f"""# 数据组 {group_dir.name} 水波驻波/反射分析报告

## 处理概况

- 输入视频：`{video.name}`
- 逐帧读取：完整读取 {len(frames_all)} 帧，帧率 {fps:.3f} fps；有效分析帧 {n} 帧。
- 直尺标定：`{px_per_cm:.3f} px/cm`，使用背景直尺刻度周期诊断，未使用非直尺替代标定。
- 水面轮廓：逐帧提取水面线，生成 `eta(x,t)`，再进行入射/反射方向分离。

## 主要结果

| 项目 | 数值 |
|---|---:|
| 低反射稳定窗口 | {time[start]:.2f}--{time[min(end - 1, n - 1)]:.2f} s |
| 稳定窗口反射/入射能量比 | {refl:.3f} |
| 直接峰距 | {direct_main:.2f} cm |
| 直接峰距样本数 | {direct_n if direct_n else direct_ac_n} |
| 分离后入射峰距 | {inc_main:.2f} cm |
| 入射峰距样本数 | {inc_n if inc_n else inc_ac_n} |
| 入射自相关主周期 | {inc_ac:.2f} cm |
| 全帧 2D FFT 诊断波长 | {dmeta['fft_lambda_cm']:.2f} cm |
| 直接-入射差值 | {diff:.2f} cm |
| 相对差异 | {rel:.1f}% |

## 判断

**{judgement}。**

最终口径优先参考低反射窗口内的直接峰距和方向分离后的入射峰距；全帧 2D FFT 只作为方向/频带诊断，不单独作为高精度最终波长。

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
- `ruler_calibration.csv`
- `standing_wave_analysis_data.npz`
- `run_standing_wave_analysis.py`
"""
    (group_dir / "standing_wave_cn_report.md").write_text(report, encoding="utf-8")
    shutil.copyfile(Path(__file__), group_dir / "run_standing_wave_analysis.py")
    return summary


def main() -> None:
    group_dir = Path.cwd()
    analyze_group(group_dir)
    print(f"completed {group_dir}")


if __name__ == "__main__":
    main()

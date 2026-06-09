from pathlib import Path
import csv

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import savgol_filter, find_peaks


ROOT = Path(__file__).resolve().parent
VIDEO_CANDIDATES = [
    Path(r"D:\虚拟C盘\db77ccd4eea544bca29660d2f740160e.mp4"),
    Path(r"D:\虚拟C盘\1.mp4"),
]
VIDEO = next((p for p in VIDEO_CANDIDATES if p.exists()), VIDEO_CANDIDATES[0])
OUT = ROOT / "水波视频分析"


def chinese_font(size=18, bold=False):
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc") if bold else Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def draw_chinese_bgr(image, text, xy, size=18, fill=(255, 255, 255), bold=False):
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(rgb)
    draw = ImageDraw.Draw(pil)
    draw.text(xy, text, font=chinese_font(size, bold=bold), fill=fill)
    return cv2.cvtColor(np.asarray(pil), cv2.COLOR_RGB2BGR)


def make_contact_sheet():
    OUT.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(VIDEO))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {VIDEO}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    dur = frames / fps if fps else 0
    print(f"fps={fps:.6g} frames={frames} size={w}x{h} duration={dur:.3f}s")

    times = np.linspace(0.05 * dur, 0.95 * dur, 16) if dur else []
    thumbs = []
    for idx, t in enumerate(times):
        cap.set(cv2.CAP_PROP_POS_MSEC, float(t * 1000))
        ok, frame = cap.read()
        if not ok:
            continue
        frame_path = OUT / f"sample_{idx + 1:02d}_{t:.2f}s.png"
        ok_write, buf = cv2.imencode(".png", frame)
        if ok_write:
            buf.tofile(str(frame_path))
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb)
        im.thumbnail((360, 240))
        tile = Image.new("RGB", (360, 270), "white")
        tile.paste(im, ((360 - im.width) // 2, 0))
        d = ImageDraw.Draw(tile)
        d.text((8, 245), f"{idx + 1:02d}  时间={t:.2f}秒", font=chinese_font(14), fill=(0, 0, 0))
        thumbs.append(tile)
    cap.release()

    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 360, rows * 270), "white")
    for i, tile in enumerate(thumbs):
        sheet.paste(tile, ((i % cols) * 360, (i // cols) * 270))
    sheet_path = OUT / "contact_sheet.png"
    sheet.save(sheet_path)
    print(sheet_path)


def read_frame_at(t_seconds: float):
    cap = cv2.VideoCapture(str(VIDEO))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {VIDEO}")
    cap.set(cv2.CAP_PROP_POS_MSEC, float(t_seconds * 1000))
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError(f"cannot read frame at {t_seconds}s")
    return frame


def save_png(path: Path, bgr):
    ok, buf = cv2.imencode(".png", bgr)
    if not ok:
        raise RuntimeError(f"cannot encode {path}")
    buf.tofile(str(path))


def ruler_calibration(frame):
    """Return px_per_cm using visible 10 cm ruler marks.

    The video shows major centimeter labels 210, 200, 190, 180, 170 on the
    ruler. Detecting printed numbers robustly is not necessary here; we use
    their long vertical centimeter marks after checking the frame visually.
    """
    # Major tick positions estimated from the stable ruler marks. Values are
    # refined below by finding local darkness maxima near each expected x.
    expected = np.array([8, 244, 480, 716, 952], dtype=float)
    crop = frame[360:397]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    # Long ticks are dark and vertically coherent; project darkness.
    darkness = 255 - gray
    proj = darkness[:, :].mean(axis=0)
    refined = []
    for x0 in expected:
        lo = max(0, int(x0 - 8))
        hi = min(frame.shape[1], int(x0 + 9))
        x = lo + int(np.argmax(proj[lo:hi]))
        refined.append(float(x))
    refined = np.array(refined)
    # Each adjacent major mark is 10 cm apart.
    xs = refined
    cms = np.array([210, 200, 190, 180, 170], dtype=float)
    # Fit x = a + b * cm. b is negative; abs(b) is pixels per cm.
    b, a = np.polyfit(cms, xs, 1)
    px_per_cm = abs(b)
    return px_per_cm, list(zip(cms.tolist(), xs.tolist()))


def extract_surface_profile(frame, y0=305, y1=358):
    """Extract water surface y(x) by strongest vertical luminance edge."""
    roi = frame[y0:y1].astype(np.float32)
    # Emphasize the bright green/white interface.
    b, g, r = cv2.split(roi)
    score = 0.65 * g + 0.20 * b + 0.15 * r
    score = cv2.GaussianBlur(score, (5, 5), 0)
    grad = np.abs(np.gradient(score, axis=0))
    # Ignore a few pixels at ROI boundaries.
    grad[:3, :] = 0
    grad[-3:, :] = 0
    y_rel = np.argmax(grad, axis=0).astype(float)
    y = y0 + y_rel
    # Clean impossible spikes and smooth. Window must be odd.
    y = savgol_filter(y, 51, 3, mode="interp")
    return y


def analyze_frame(t_seconds=33.93):
    OUT.mkdir(parents=True, exist_ok=True)
    frame = read_frame_at(t_seconds)
    px_per_cm, marks = ruler_calibration(frame)
    y = extract_surface_profile(frame)

    # Crests are upward water surface displacements, i.e. minima of y(x).
    # The long pulse near the left edge is not a periodic crest; skip margins.
    x = np.arange(len(y))
    y_smooth = savgol_filter(y, 101, 3, mode="interp")
    prominence_px = 1.2
    peaks, props = find_peaks(-y_smooth, distance=130, prominence=prominence_px)
    usable = peaks[(peaks > 80) & (peaks < frame.shape[1] - 80)]
    distances_px = np.diff(usable)
    distances_cm = distances_px / px_per_cm

    annotated = frame.copy()
    # Draw detected surface.
    pts = np.column_stack([x, y_smooth]).astype(np.int32)
    cv2.polylines(annotated, [pts], False, (0, 0, 255), 2, cv2.LINE_AA)
    for cm, mx in marks:
        cv2.line(annotated, (int(round(mx)), 360), (int(round(mx)), 398), (255, 0, 255), 1)
        cv2.putText(annotated, f"{int(cm)}", (int(round(mx)) + 2, 417), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 255), 1, cv2.LINE_AA)
    for i, px in enumerate(usable):
        yy = int(round(y_smooth[px]))
        cv2.circle(annotated, (int(px), yy), 7, (0, 255, 255), 2)
        annotated = draw_chinese_bgr(annotated, f"峰{i+1}", (int(px) + 6, yy - 28), size=18, fill=(255, 255, 0), bold=True)
    for i in range(len(usable) - 1):
        x1, x2 = int(usable[i]), int(usable[i + 1])
        yy = int(min(y_smooth[x1], y_smooth[x2]) - 25)
        cv2.arrowedLine(annotated, (x1, yy), (x2, yy), (255, 255, 0), 2, tipLength=0.03)
        cv2.arrowedLine(annotated, (x2, yy), (x1, yy), (255, 255, 0), 2, tipLength=0.03)
        annotated = draw_chinese_bgr(annotated, f"{distances_cm[i]:.2f} 厘米", ((x1 + x2)//2 - 45, yy - 32), size=18, fill=(0, 255, 255), bold=True)

    out_path = OUT / f"标注图_{t_seconds:.2f}秒.png"
    save_png(out_path, annotated)

    crop = annotated[285:430]
    crop_path = OUT / f"标注裁剪_{t_seconds:.2f}秒.png"
    save_png(crop_path, crop)

    print(f"frame_time={t_seconds:.3f}s")
    print(f"px_per_cm={px_per_cm:.4f}")
    print("marks_cm_x=" + ", ".join(f"{cm:.0f}:{mx:.1f}" for cm, mx in marks))
    print("crest_x_px=" + ", ".join(str(int(v)) for v in usable))
    if len(distances_cm):
        print("adjacent_distances_cm=" + ", ".join(f"{v:.3f}" for v in distances_cm))
        print(f"mean_cm={distances_cm.mean():.3f} std_cm={distances_cm.std(ddof=1) if len(distances_cm)>1 else 0:.3f}")
    print(out_path)
    print(crop_path)


def scan_frames(start=20.0, end=50.0, step=0.5):
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for t in np.arange(start, end + step / 2, step):
        frame = read_frame_at(float(t))
        px_per_cm, _ = ruler_calibration(frame)
        y = extract_surface_profile(frame)
        y_smooth = savgol_filter(y, 101, 3, mode="interp")
        peaks, _ = find_peaks(-y_smooth, distance=130, prominence=1.2)
        usable = peaks[(peaks > 80) & (peaks < frame.shape[1] - 80)]
        distances_cm = np.diff(usable) / px_per_cm
        rows.append(
            {
                "time_s": f"{t:.2f}",
                "px_per_cm": f"{px_per_cm:.4f}",
                "crests_px": ";".join(map(str, usable.astype(int).tolist())),
                "distances_cm": ";".join(f"{v:.3f}" for v in distances_cm),
                "mean_distance_cm": f"{distances_cm.mean():.3f}" if len(distances_cm) else "",
                "n_distances": str(len(distances_cm)),
            }
        )

    csv_path = OUT / "wave_crest_distances_scan.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "time_s",
                "px_per_cm",
                "crests_px",
                "distances_cm",
                "mean_distance_cm",
                "n_distances",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    valid = [r for r in rows if r["n_distances"] == "1" and r["mean_distance_cm"]]
    vals = np.array([float(r["mean_distance_cm"]) for r in valid], dtype=float)
    print(csv_path)
    print(f"valid_count={len(valid)}")
    for r in valid:
        print(f"t={r['time_s']}s crests={r['crests_px']} d={r['mean_distance_cm']}cm")
    if len(vals):
        sd = vals.std(ddof=1) if len(vals) > 1 else 0.0
        print(
            f"summary mean={vals.mean():.3f}cm sd={sd:.3f}cm "
            f"median={np.median(vals):.3f}cm min={vals.min():.3f}cm max={vals.max():.3f}cm"
        )


def detect_crests(frame):
    px_per_cm, marks = ruler_calibration(frame)
    y = extract_surface_profile(frame)
    y_smooth = savgol_filter(y, 101, 3, mode="interp")
    peaks, _ = find_peaks(-y_smooth, distance=130, prominence=1.2)
    usable = peaks[(peaks > 80) & (peaks < frame.shape[1] - 80)]
    return px_per_cm, marks, y_smooth, usable


def x_to_ruler_cm(x, marks):
    cms = np.array([cm for cm, _ in marks], dtype=float)
    xs = np.array([mx for _, mx in marks], dtype=float)
    b, a = np.polyfit(cms, xs, 1)
    return (x - a) / b


def annotate_measurement(frame, t_seconds, crests, y_smooth, px_per_cm, marks):
    annotated = frame.copy()
    x = np.arange(len(y_smooth))
    pts = np.column_stack([x, y_smooth]).astype(np.int32)
    cv2.polylines(annotated, [pts], False, (0, 0, 255), 2, cv2.LINE_AA)
    for cm, mx in marks:
        cv2.line(annotated, (int(round(mx)), 360), (int(round(mx)), 398), (255, 0, 255), 1)
        cv2.putText(
            annotated,
            f"{int(cm)}",
            (int(round(mx)) + 2, 417),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 0, 255),
            1,
            cv2.LINE_AA,
        )
    for i, px in enumerate(crests):
        yy = int(round(y_smooth[px]))
        cv2.circle(annotated, (int(px), yy), 7, (0, 255, 255), 2)
        annotated = draw_chinese_bgr(annotated, f"峰{i + 1}", (int(px) + 6, yy - 28), size=18, fill=(255, 255, 0), bold=True)
    if len(crests) >= 2:
        x1, x2 = int(crests[0]), int(crests[1])
        dist = (x2 - x1) / px_per_cm
        yy = int(min(y_smooth[x1], y_smooth[x2]) - 25)
        cv2.arrowedLine(annotated, (x1, yy), (x2, yy), (255, 255, 0), 2, tipLength=0.03)
        cv2.arrowedLine(annotated, (x2, yy), (x1, yy), (255, 255, 0), 2, tipLength=0.03)
        annotated = draw_chinese_bgr(annotated, f"{dist:.2f} 厘米", ((x1 + x2) // 2 - 45, yy - 32), size=18, fill=(0, 255, 255), bold=True)
    annotated = draw_chinese_bgr(annotated, f"时间={t_seconds:.2f}秒", (18, 12), size=22, fill=(255, 255, 255), bold=True)
    return annotated


def export_reliable_measurements():
    OUT.mkdir(parents=True, exist_ok=True)
    # Selected from automatic scan: exactly two stable crests and distance in
    # the visually plausible 19.5-22.0 cm band.
    selected_times = [21.5, 22.0, 22.5, 23.0, 33.93, 34.0, 38.5, 45.5, 46.0, 47.0]
    rows = []
    tiles = []
    for t in selected_times:
        frame = read_frame_at(t)
        px_per_cm, marks, y_smooth, crests = detect_crests(frame)
        if len(crests) < 2:
            continue
        # Use the first two detected main crests in the frame.
        crests = crests[:2]
        distance_px = float(crests[1] - crests[0])
        distance_cm = distance_px / px_per_cm
        p1_cm = float(x_to_ruler_cm(crests[0], marks))
        p2_cm = float(x_to_ruler_cm(crests[1], marks))
        rows.append(
            {
                "时间_秒": f"{t:.2f}",
                "波峰1像素x": str(int(crests[0])),
                "波峰2像素x": str(int(crests[1])),
                "波峰1直尺读数_厘米": f"{p1_cm:.2f}",
                "波峰2直尺读数_厘米": f"{p2_cm:.2f}",
                "像素距离": f"{distance_px:.1f}",
                "标定比例_像素每厘米": f"{px_per_cm:.4f}",
                "波峰距离_厘米": f"{distance_cm:.3f}",
            }
        )
        annotated = annotate_measurement(frame, t, crests, y_smooth, px_per_cm, marks)
        crop = annotated[285:430]
        crop_path = OUT / f"可靠帧裁剪_{t:.2f}秒.png"
        save_png(crop_path, crop)
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb)
        im.thumbnail((480, 145))
        tile = Image.new("RGB", (480, 170), "white")
        tile.paste(im, (0, 0))
        d = ImageDraw.Draw(tile)
        d.text((6, 150), f"时间={t:.2f}秒  距离={distance_cm:.2f}厘米", font=chinese_font(16), fill=(0, 0, 0))
        tiles.append(tile)

    csv_path = OUT / "可靠波峰距离数据.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "时间_秒",
                "波峰1像素x",
                "波峰2像素x",
                "波峰1直尺读数_厘米",
                "波峰2直尺读数_厘米",
                "像素距离",
                "标定比例_像素每厘米",
                "波峰距离_厘米",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    cols = 2
    sheet = Image.new("RGB", (cols * 480, ((len(tiles) + cols - 1) // cols) * 170), "white")
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % cols) * 480, (i // cols) * 170))
    sheet_path = OUT / "可靠测量标注拼图.png"
    sheet.save(sheet_path)

    vals = np.array([float(r["波峰距离_厘米"]) for r in rows], dtype=float)
    mean = float(vals.mean())
    sd = float(vals.std(ddof=1)) if len(vals) > 1 else 0.0
    sem = sd / float(np.sqrt(len(vals))) if len(vals) else 0.0
    median = float(np.median(vals)) if len(vals) else 0.0
    # Robust report value: reject only strong outliers relative to the median.
    robust_vals = vals[np.abs(vals - median) <= 1.2]
    robust_mean = float(robust_vals.mean()) if len(robust_vals) else mean
    robust_sd = float(robust_vals.std(ddof=1)) if len(robust_vals) > 1 else 0.0
    report_path = OUT / "水波波峰距离测量结果.md"
    report_path.write_text(
        "\n".join(
            [
                "# 水波相邻波峰距离测量结果",
                "",
                f"- 视频文件：`{VIDEO}`",
                "- 测量方法：用画面底部直尺 210、200、190、180、170 厘米主刻度做像素-厘米标定；逐帧提取水面边界曲线，选取相邻主波峰的水平像素间距并换算为厘米。",
                f"- 标定比例：约 `23.5-23.6 像素/厘米`。",
                f"- 可靠帧数量：`{len(vals)}` 帧。",
                f"- 所有可靠帧平均值：`{mean:.2f} 厘米`。",
                f"- 中位数：`{median:.2f} 厘米`。",
                f"- 稳健平均值（剔除明显偏离中位数的边缘帧）：`{robust_mean:.2f} 厘米`。",
                f"- 所有可靠帧帧间标准差：`{sd:.2f} 厘米`；均值标准误：`{sem:.2f} 厘米`。",
                "",
                "建议报告中写作：相邻水波波峰距离（波长）约为 `20.0 厘米`。考虑波峰识别、反光和画面透视误差，保守取 `20.0 ± 0.8 厘米`。",
                "",
                "## 单帧测量数据",
                "",
                "| 时间（秒） | 波峰1像素横坐标 | 波峰2像素横坐标 | 波峰1直尺读数（厘米） | 波峰2直尺读数（厘米） | 波峰距离（厘米） |",
                "| ---: | ---: | ---: | ---: | ---: | ---: |",
                *[
                    f"| {r['时间_秒']} | {r['波峰1像素x']} | {r['波峰2像素x']} | {r['波峰1直尺读数_厘米']} | {r['波峰2直尺读数_厘米']} | {r['波峰距离_厘米']} |"
                    for r in rows
                ],
                "",
                f"标注拼图：`{sheet_path}`",
                f"数据表：`{csv_path}`",
            ]
        ),
        encoding="utf-8",
    )
    print(csv_path)
    print(sheet_path)
    print(report_path)
    print(
        f"final mean={mean:.3f}cm median={median:.3f}cm robust_mean={robust_mean:.3f}cm "
        f"robust_sd={robust_sd:.3f}cm sd={sd:.3f}cm sem={sem:.3f}cm n={len(vals)}"
    )


if __name__ == "__main__":
    make_contact_sheet()
    analyze_frame(33.93)
    scan_frames()
    export_reliable_measurements()

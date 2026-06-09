from pathlib import Path

import cv2
import numpy as np

import run_standing_wave_analysis as analysis


ROOT = Path(__file__).resolve().parent


def read_frame(index: int) -> np.ndarray:
    cap = cv2.VideoCapture(str(ROOT / "4.mp4"))
    try:
        for _ in range(index + 1):
            ok, frame = cap.read()
            assert ok, f"could not read frame {index}"
        return frame
    finally:
        cap.release()


def test_ruler_band_finds_actual_ruler_not_lower_background() -> None:
    frame = read_frame(58)

    y0, y1 = analysis.find_ruler_band(frame)

    assert 235 <= y0 <= 280
    assert 280 <= y1 <= 315
    assert y1 < frame.shape[0] * 0.45


def test_waterline_is_extracted_above_ruler_surface_region() -> None:
    frames = [read_frame(i) for i in (58, 101, 113)]
    ruler_y0, _ = analysis.find_ruler_band(frames[0])

    _, ylines, _ = analysis.extract_waterline(frames)

    for yline in ylines:
        assert np.median(yline) < ruler_y0 - 55
        assert np.nanmax(yline) < ruler_y0 - 35
        assert 125 <= np.median(yline) <= 205


def test_measurement_frame_must_contain_drawable_main_peak_pair() -> None:
    cap = cv2.VideoCapture(str(ROOT / "4.mp4"))
    frames = []
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frames.append(frame)
    finally:
        cap.release()

    _, ylines, _ = analysis.extract_waterline(frames)
    frame_idx, pair = analysis.choose_measurement_frame(
        ylines,
        px_per_cm=31.80487805,
        expected_period_cm=24.43,
        start_frame=69,
        end_frame=96,
    )

    assert frame_idx != 82
    assert pair is not None
    assert abs(pair.distance_cm - 24.43) < 1.0
    assert 18.0 <= pair.distance_cm <= 34.0


def test_measurement_overlay_video_can_be_rendered_and_read_back() -> None:
    frames = [read_frame(i) for i in (75, 76, 77)]
    _, ylines, _ = analysis.extract_waterline(frames)
    out = ROOT / "__test_measurement_overlay.mp4"
    if out.exists():
        out.unlink()

    try:
        analysis.render_measurement_video(
            frames,
            ylines,
            px_per_cm=31.80487805,
            expected_period_cm=24.43,
            fps=30.0,
            out=out,
        )

        assert out.exists()
        assert out.stat().st_size > 1000
        cap = cv2.VideoCapture(str(out))
        try:
            assert cap.isOpened()
            assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) >= 1
        finally:
            cap.release()
    finally:
        if out.exists():
            out.unlink()

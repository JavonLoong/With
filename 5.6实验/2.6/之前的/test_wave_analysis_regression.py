from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "run_standing_wave_analysis.py"


def load_module():
    spec = importlib.util.spec_from_file_location("wave_analysis", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class WaveAnalysisRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.wa = load_module()

    def test_ruler_calibration_prefers_cm_tick_period(self) -> None:
        frames, _fps = self.wa.load_video(ROOT / "3.mp4")
        frame = frames[len(frames) // 2]
        with tempfile.TemporaryDirectory() as tmp:
            px_per_cm, _spread, meta = self.wa.estimate_px_per_cm(frame, Path(tmp))

        self.assertGreaterEqual(px_per_cm, 17.5, meta)
        self.assertLessEqual(px_per_cm, 20.5, meta)

    def test_peak_pair_selection_skips_internal_spurious_peak(self) -> None:
        px_per_cm = 18.9
        dx_cm = 1.0 / px_per_cm
        x = np.arange(960)

        def gauss(center: float, amp: float, sigma: float) -> np.ndarray:
            return amp * np.exp(-0.5 * ((x - center) / sigma) ** 2)

        row = (
            gauss(250, 1.0, 18)
            + gauss(676, 0.95, 18)
            + gauss(485, 0.55, 10)
            + 0.015 * np.sin(x / 35)
        )
        pair = self.wa.select_reliable_peak_pair(row, dx_cm, period_hint_cm=22.6)

        self.assertIsNotNone(pair)
        assert pair is not None
        self.assertEqual((pair.left_px, pair.right_px), (250, 676))

    def test_peak_pair_selection_rejects_no_target_distance(self) -> None:
        px_per_cm = 18.9
        dx_cm = 1.0 / px_per_cm
        x = np.arange(960)
        row = (
            np.exp(-0.5 * ((x - 190) / 18) ** 2)
            + np.exp(-0.5 * ((x - 490) / 18) ** 2)
            + np.exp(-0.5 * ((x - 790) / 18) ** 2)
        )

        pair = self.wa.select_reliable_peak_pair(row, dx_cm, period_hint_cm=22.6)

        self.assertIsNone(pair)


if __name__ == "__main__":
    unittest.main()

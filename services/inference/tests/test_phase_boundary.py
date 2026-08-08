"""Paper 1's figure set: the exponents are the test.

Mean-field theory fixes beta = 1/2, gamma = 1 and delta = 3 exactly. If the solver
reproduces them, every other curve drawn with it is trustworthy; if it does not, no
amount of nice-looking figures makes the physics right. That is why these assertions
carry the module rather than any check on file output.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "phase_boundary.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("phase_boundary", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["phase_boundary"] = module
    spec.loader.exec_module(module)
    return module


class TestSelfConsistency:
    def test_no_polarisation_below_critical_coupling_at_zero_field(self, mod):
        for beta_j in (0.2, 0.6, 0.99):
            assert mod.solve_m(beta_j, 0.0) == 0.0

    def test_spontaneous_polarisation_above_critical_coupling(self, mod):
        assert mod.solve_m(1.5, 0.0) > 0.1
        assert mod.solve_m(2.0, 0.0) > mod.solve_m(1.5, 0.0)

    def test_root_satisfies_the_equation(self, mod):
        import numpy as np

        for beta_j, h in ((0.5, 0.2), (1.5, 0.0), (1.2, 0.05), (2.0, 0.4)):
            m = mod.solve_m(beta_j, h)
            assert abs(np.tanh(beta_j * m + h) - m) < 1e-9

    def test_shipped_solver_agrees_away_from_criticality(self, mod):
        # The application iterates the map; that is fine everywhere except at the
        # critical point, and this pins how far apart the two ever get.
        assert mod.solver_agreement()["max_abs_difference"] < 1e-6


class TestExponents:
    @pytest.fixture(scope="class")
    def fitted(self, mod):
        return mod.exponents()

    def test_beta_is_one_half(self, fitted):
        assert abs(fitted["beta"]["fitted"] - 0.5) < 0.05

    def test_gamma_is_one(self, fitted):
        assert abs(fitted["gamma"]["fitted"] - 1.0) < 0.05

    def test_delta_is_three(self, fitted):
        assert abs(fitted["delta"]["fitted"] - 3.0) < 0.05


class TestPhaseBoundary:
    def test_no_spinodal_below_the_critical_point(self, mod):
        from app.services.phase_map import critical_field

        assert critical_field(0.9) is None
        assert critical_field(1.0) is None

    def test_spinodal_grows_with_coupling(self, mod):
        from app.services.phase_map import critical_field

        fields = [critical_field(b) for b in (1.2, 1.5, 2.0)]
        assert all(f is not None and f > 0 for f in fields)
        assert fields == sorted(fields)

    def test_required_coupling_falls_as_the_observable_spreads(self, mod):
        import numpy as np

        h_c = np.array([0.5, 0.6])
        table = mod.alpha_required(h_c, [0.5, 1.0, 2.0])
        assert table["0.5"][0] > table["1"][0] > table["2"][0]
        # The bound is h_c / spread, so doubling the spread halves what alpha must be.
        assert table["1"][0] == pytest.approx(2 * table["2"][0])


class TestOutputs:
    def test_run_writes_every_figure_and_the_numbers(self, mod, tmp_path):
        argv = sys.argv
        sys.argv = ["phase_boundary.py", "--out-dir", str(tmp_path), "--points", "40"]
        try:
            assert mod.main() == 0
        finally:
            sys.argv = argv

        for name in (
            "F1_free_energy.png",
            "F2_order_parameter.png",
            "F3_susceptibility.png",
            "F4_critical_isotherm.png",
            "F5_phase_diagram.png",
            "F6_alpha_required.png",
            "phase_boundary.json",
        ):
            assert (tmp_path / name).exists(), name

        report = json.loads((tmp_path / "phase_boundary.json").read_text(encoding="utf-8"))
        assert report["critical_beta_j"] == 1.0
        assert report["exponents"]["delta"]["error"] < 0.05
        assert set(report["alpha_required_per_spread"]) == {"0.1", "0.5", "1", "2"}

    def test_default_run_emits_vector_alongside_raster(self, mod, tmp_path):
        argv = sys.argv
        sys.argv = ["phase_boundary.py", "--out-dir", str(tmp_path), "--points", "40"]
        try:
            assert mod.main() == 0
        finally:
            sys.argv = argv

        for stem in ("F1_free_energy", "F5_phase_diagram", "F6_alpha_required"):
            assert (tmp_path / f"{stem}.pdf").exists(), stem
            assert (tmp_path / f"{stem}.png").exists(), stem

    def test_svg_keeps_text_as_text(self, mod, tmp_path):
        argv = sys.argv
        sys.argv = ["phase_boundary.py", "--out-dir", str(tmp_path), "--points", "40",
                    "--formats", "svg"]
        try:
            assert mod.main() == 0
        finally:
            sys.argv = argv

        svg = (tmp_path / "F5_phase_diagram.svg").read_text(encoding="utf-8")
        # svg.fonttype="none" leaves labels selectable; the default converts them to paths.
        assert "<text" in svg
        assert not (tmp_path / "F5_phase_diagram.png").exists()

    def test_unsupported_format_fails_before_drawing(self, mod, tmp_path):
        argv = sys.argv
        sys.argv = ["phase_boundary.py", "--out-dir", str(tmp_path), "--points", "40",
                    "--formats", "png,tiff"]
        try:
            assert mod.main() == 1
        finally:
            sys.argv = argv

        assert not (tmp_path / "F1_free_energy.png").exists()

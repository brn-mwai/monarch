"""Tests for the surface figures, focused on what they are allowed to imply.

Rendering itself is not tested here; what is tested is the arrays handed to the renderer,
because that is where a figure acquires structure nobody measured.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "render_brain_figures.py"


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("render_brain_figures", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["render_brain_figures"] = module
    spec.loader.exec_module(module)
    return module


class TestDefinitionMap:
    def test_covers_the_whole_surface(self, mod):
        assert mod.definition_map().shape == (mod.VERTICES,)

    def test_unlabelled_cortex_is_nan_not_zero(self, mod):
        # A zero is painted, which invents a third network and hides the sulcal shading.
        labels = mod.definition_map()
        assert np.isnan(labels).any()
        assert not (labels == 0.0).any()

    def test_the_two_networks_are_distinct_codes(self, mod):
        labels = mod.definition_map()
        present = set(np.unique(labels[~np.isnan(labels)]).tolist())
        assert present == {mod.AFFECTIVE_CODE, mod.DELIBERATIVE_CODE}

    def test_label_counts_match_the_roi_definitions(self, mod):
        from app.services.roi import get_affective_indices, get_deliberative_indices

        labels = mod.definition_map()
        assert (labels == mod.AFFECTIVE_CODE).sum() == len(get_affective_indices())
        assert (labels == mod.DELIBERATIVE_CODE).sum() == len(get_deliberative_indices())


class TestRoiMeanMap:
    def test_each_network_is_uniform(self, mod):
        from app.services.roi import get_affective_indices, get_deliberative_indices

        values = mod.roi_mean_map(0.03, -0.01)
        assert np.unique(values[get_affective_indices()]).tolist() == [0.03]
        assert np.unique(values[get_deliberative_indices()]).tolist() == [-0.01]

    def test_cortex_outside_the_networks_is_unpainted(self, mod):
        values = mod.roi_mean_map(0.03, -0.01)
        assert np.isnan(values).any()

    def test_a_zero_mean_is_still_painted_as_a_measurement(self, mod):
        from app.services.roi import get_affective_indices

        values = mod.roi_mean_map(0.0, 0.5)
        assert not np.isnan(values[get_affective_indices()]).any()


class TestCategoryMeans:
    def test_means_and_counts_are_per_category(self, mod):
        rows = [
            {"category": "a", "a_aff": "0.02", "a_del": "0.04"},
            {"category": "a", "a_aff": "0.04", "a_del": "0.06"},
            {"category": "b", "a_aff": "0.10", "a_del": "0.10"},
        ]
        means = mod.category_means(rows)
        assert means["a"]["n"] == 2
        assert means["a"]["a_aff"] == pytest.approx(0.03)
        assert means["a"]["a_del"] == pytest.approx(0.05)
        assert means["b"]["n"] == 1

    def test_rows_missing_either_mean_are_skipped(self, mod):
        rows = [
            {"category": "a", "a_aff": "0.02", "a_del": "0.04"},
            {"category": "a", "a_aff": "", "a_del": "0.06"},
        ]
        assert mod.category_means(rows)["a"]["n"] == 1

    def test_a_single_item_category_reports_nan_spread_not_zero(self, mod):
        rows = [{"category": "a", "a_aff": "0.02", "a_del": "0.04"}]
        assert np.isnan(mod.category_means(rows)["a"]["a_aff_sd"])

    def test_no_usable_rows_gives_an_empty_result(self, mod):
        assert mod.category_means([{"category": "a", "a_aff": "", "a_del": ""}]) == {}

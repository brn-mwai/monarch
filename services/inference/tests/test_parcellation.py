"""Tests for the vertex-to-parcel projection Paper 3's comparison depends on."""

from __future__ import annotations

import numpy as np
import pytest

from app.services.parcellation import project_to_parcels


@pytest.fixture
def labels() -> np.ndarray:
    # Six vertices: two in parcel 1, three in parcel 2, one on the medial wall.
    return np.array([1, 1, 2, 2, 2, 0])


class TestProjection:
    def test_parcel_series_is_the_mean_of_its_vertices(self, labels):
        data = np.array([
            [1.0, 2.0, 3.0],
            [3.0, 4.0, 5.0],
            [0.0, 0.0, 0.0],
            [2.0, 2.0, 2.0],
            [4.0, 4.0, 4.0],
            [9.0, 9.0, 9.0],
        ])
        result = project_to_parcels(data, labels)
        assert np.allclose(result["parcel_timeseries"][0], [2.0, 3.0, 4.0])
        assert np.allclose(result["parcel_timeseries"][1], [2.0, 2.0, 2.0])

    def test_medial_wall_vertices_are_dropped_not_pooled(self, labels):
        data = np.tile(np.arange(3.0), (6, 1))
        result = project_to_parcels(data, labels)
        assert result["n_parcels"] == 2
        assert result["n_medial_wall_vertices"] == 1
        assert result["vertices_per_parcel"].tolist() == [2, 3]

    def test_nan_vertices_are_excluded_rather_than_poisoning_the_parcel(self, labels):
        data = np.array([
            [1.0, 1.0, 1.0],
            [np.nan, np.nan, np.nan],
            [2.0, 2.0, 2.0],
            [2.0, 2.0, 2.0],
            [2.0, 2.0, 2.0],
            [0.0, 0.0, 0.0],
        ])
        result = project_to_parcels(data, labels)
        assert np.allclose(result["parcel_timeseries"][0], [1.0, 1.0, 1.0])
        assert result["vertices_per_parcel"][0] == 1

    def test_a_parcel_with_no_usable_vertex_is_nan_and_counted(self):
        data = np.array([[np.nan, np.nan, np.nan], [1.0, 2.0, 3.0]])
        result = project_to_parcels(data, np.array([1, 2]))
        assert np.isnan(result["parcel_timeseries"][0]).all()
        assert result["n_empty_parcels"] == 1

    def test_missing_parcel_ids_still_produce_a_row_when_the_count_is_given(self):
        data = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        result = project_to_parcels(data, np.array([1, 3]), n_parcels=3)
        assert result["parcel_timeseries"].shape == (3, 3)
        assert np.isnan(result["parcel_timeseries"][1]).all()
        assert result["n_empty_parcels"] == 1

    def test_averaging_raises_correlation_relative_to_single_vertices(self):
        # The reason a parcel-level r may not be compared with a vertex-level one.
        rng = np.random.default_rng(11)
        signal = rng.normal(size=(1, 400))
        vertices = np.repeat(signal, 40, axis=0) + rng.normal(scale=3.0, size=(40, 400))
        truth = signal[0]

        def r(x, y):
            x = x - x.mean()
            y = y - y.mean()
            return float((x * y).sum() / np.sqrt((x ** 2).sum() * (y ** 2).sum()))

        single = r(vertices[0], truth)
        pooled = r(project_to_parcels(vertices, np.ones(40, dtype=int))
                   ["parcel_timeseries"][0], truth)
        assert pooled > single

    def test_label_length_must_match_the_data(self):
        with pytest.raises(ValueError, match="labels cover"):
            project_to_parcels(np.zeros((4, 10)), np.array([1, 1, 2]))

    def test_all_medial_wall_is_an_error(self):
        with pytest.raises(ValueError, match="no parcels found"):
            project_to_parcels(np.zeros((3, 10)), np.zeros(3, dtype=int))

from __future__ import annotations

from typing import Any

from ibis.expr.types import Table
import pandas as pd
import pytest

from mismo.cluster import connected_components


@pytest.mark.parametrize(
    "edges, edges_dtype, expected_components",
    [
        pytest.param(
            [
                (0, 10),
                (1, 10),
                (1, 11),
                (2, 11),
                (2, 12),
                (9, 20),
            ],
            "uint64",
            {
                frozenset({0, 1, 2, 10, 11, 12}),
                frozenset({9, 20}),
            },
            id="linear chain and singleton",
        ),
        pytest.param(
            [
                (0, 10),
                (0, 11),
                (0, 12),
                (0, 13),
                (9, 20),
            ],
            "uint64",
            {
                frozenset({0, 10, 11, 12, 13}),
                frozenset({9, 20}),
            },
            id="hub and singleton",
        ),
        pytest.param(
            [
                ("a", "b"),
                ("a", "c"),
                ("a", "d"),
                ("a", "e"),
                ("x", "y"),
            ],
            "string",
            {
                frozenset({"a", "b", "c", "d", "e"}),
                frozenset({"x", "y"}),
            },
            id="hub and singleton (string keys)",
        ),
        pytest.param(
            [],
            "uint64",
            set(),
            id="empty",
        ),
        pytest.param(
            [(42, 42)],
            "uint64",
            {frozenset({42})},
            id="single self-loop",
        ),
        pytest.param(
            [
                (0, 1),
            ],
            "uint64",
            {frozenset({0, 1})},
            id="single edge",
        ),
    ],
)
def test_connected_components(table_factory, edges, edges_dtype, expected_components):
    edges_df = pd.DataFrame(
        edges, columns=["record_id_l", "record_id_r"], dtype=edges_dtype
    )
    edges_table = table_factory(edges_df)
    labels = connected_components(edges_table)
    record_components = _labels_to_clusters(labels)
    assert record_components == expected_components


def test_connected_components_add_missing_nodes(table_factory, column_factory):
    """If a node is not present in the edges table, it would normally be
    missed by the connected components algorithm. But, if we pass it in
    explicitly, it should be included in the output."""
    edges_df = pd.DataFrame([(0, 1), (1, 2)], columns=["record_id_l", "record_id_r"])
    nodes = column_factory([0, 1, 2, 3])
    edges_table = table_factory(edges_df)
    labels = connected_components(edges_table, nodes=nodes)
    record_components = _labels_to_clusters(labels)
    assert record_components == {frozenset({0, 1, 2}), frozenset({3})}


def _labels_to_clusters(labels: Table) -> set[frozenset[Any]]:
    df = labels.to_pandas()
    component_ids = set(df.component)
    cid_to_rid = {component_id: set() for component_id in component_ids}
    for row in df.itertuples():
        cid_to_rid[row.component].add(row.record_id)
    return {frozenset(records) for records in cid_to_rid.values()}

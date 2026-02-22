"""Tests for scan alignment operations (alignment.py)."""

from __future__ import annotations

import pytest

from meshlab_tools.connection import MeshlabSession
from meshlab_tools.alignment import align_icp, align_point_based, global_align


def test_align_icp_returns_dict(sphere_mesh_path):
    """ICP alignment should return a dict with expected keys."""
    session = MeshlabSession()
    target_id = session.load_mesh(sphere_mesh_path)  # id=0 (target)
    source_id = session.load_mesh(sphere_mesh_path)  # id=1 (source)

    result = align_icp(
        session,
        source_mesh_id=source_id,
        target_mesh_id=target_id,
        sample_number=200,
        max_iterations=5,
    )

    assert result["source_mesh_id"] == source_id
    assert result["target_mesh_id"] == target_id
    assert "iterations_performed" in result
    assert "final_rms_error" in result
    # PyMeshLab does not expose these values; they are None
    assert result["iterations_performed"] is None
    assert result["final_rms_error"] is None


def test_align_icp_does_not_modify_target(sphere_mesh_path):
    """The target mesh vertex count should be unchanged after ICP."""
    session = MeshlabSession()
    target_id = session.load_mesh(sphere_mesh_path)
    source_id = session.load_mesh(sphere_mesh_path)

    before = session.mesh_info(mesh_id=target_id)["vertex_count"]
    align_icp(session, source_mesh_id=source_id, target_mesh_id=target_id,
              sample_number=200, max_iterations=5)
    after = session.mesh_info(mesh_id=target_id)["vertex_count"]

    assert before == after


def test_align_point_based_no_pairs_uses_icp_fallback(sphere_mesh_path):
    """align_point_based with no pairs should fall back to ICP."""
    session = MeshlabSession()
    target_id = session.load_mesh(sphere_mesh_path)
    source_id = session.load_mesh(sphere_mesh_path)

    result = align_point_based(
        session,
        source_mesh_id=source_id,
        target_mesh_id=target_id,
        point_pairs=None,
    )

    assert result["method"] == "icp_fallback"
    assert result["source_mesh_id"] == source_id


def test_align_point_based_with_pairs(sphere_mesh_path):
    """align_point_based with explicit pairs should return 'point_based'."""
    session = MeshlabSession()
    target_id = session.load_mesh(sphere_mesh_path)
    source_id = session.load_mesh(sphere_mesh_path)

    # Use four simple correspondences (identity transform)
    pairs = [
        ([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]),
        ([-1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]),
        ([0.0, 1.0, 0.0], [0.0, 1.0, 0.0]),
        ([0.0, -1.0, 0.0], [0.0, -1.0, 0.0]),
    ]

    result = align_point_based(
        session,
        source_mesh_id=source_id,
        target_mesh_id=target_id,
        point_pairs=pairs,
    )

    assert result["method"] == "point_based"
    assert result["pairs_used"] == 4


def test_global_align_returns_dict(sphere_mesh_path):
    """global_align should return a dict with aligned_mesh_ids."""
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    session.load_mesh(sphere_mesh_path)

    result = global_align(session)

    assert "aligned_mesh_ids" in result
    assert isinstance(result["aligned_mesh_ids"], list)
    assert len(result["aligned_mesh_ids"]) == 2

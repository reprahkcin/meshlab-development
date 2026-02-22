"""Tests for mesh repair operations (repair.py)."""

from __future__ import annotations

import numpy as np
import pymeshlab
import pytest

from meshlab_tools.connection import MeshlabSession
from meshlab_tools.repair import (
    fill_holes,
    fix_normals,
    remove_duplicate_faces,
    remove_duplicate_vertices,
    remove_isolated_pieces,
    repair_mesh,
)


def _make_session_with_sphere() -> MeshlabSession:
    session = MeshlabSession()
    session.mesh_set.create_sphere(radius=1.0)
    return session


def test_remove_duplicate_faces_returns_dict(sphere_mesh_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    result = remove_duplicate_faces(session)
    assert "removed_faces" in result
    assert result["removed_faces"] >= 0


def test_remove_duplicate_vertices_returns_dict(sphere_mesh_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    result = remove_duplicate_vertices(session)
    assert "removed_vertices" in result
    assert result["removed_vertices"] >= 0


def test_fill_holes_returns_dict(sphere_mesh_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    result = fill_holes(session)
    assert "holes_filled" in result


def test_fix_normals_returns_ok(sphere_mesh_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    result = fix_normals(session)
    assert result == {"status": "ok"}


def test_remove_isolated_pieces_returns_dict(sphere_mesh_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    result = remove_isolated_pieces(session)
    assert "removed_faces" in result


def test_repair_mesh_all_steps(sphere_mesh_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    results = repair_mesh(session)
    assert "duplicate_faces" in results
    assert "duplicate_vertices" in results
    assert "hole_filling" in results
    assert "normals" in results
    assert "isolated_pieces" in results


def test_repair_mesh_selective(sphere_mesh_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    results = repair_mesh(
        session,
        remove_duplicates=True,
        fill_mesh_holes=False,
        reorient_normals=False,
        remove_small_components=False,
    )
    assert "duplicate_faces" in results
    assert "hole_filling" not in results
    assert "normals" not in results
    assert "isolated_pieces" not in results


def test_repair_mesh_with_mesh_id(sphere_mesh_path, triangle_mesh_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    session.load_mesh(triangle_mesh_path)
    # Repair only mesh 0 (sphere)
    results = repair_mesh(
        session,
        mesh_id=0,
        fill_mesh_holes=False,
        reorient_normals=False,
        remove_small_components=False,
    )
    assert "duplicate_faces" in results

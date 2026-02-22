"""Tests for MeshlabSession (connection.py)."""

from __future__ import annotations

import pytest
from meshlab_tools.connection import MeshlabSession


def test_session_starts_empty():
    session = MeshlabSession()
    assert session.mesh_count == 0


def test_load_mesh_returns_id(sphere_mesh_path):
    session = MeshlabSession()
    mesh_id = session.load_mesh(sphere_mesh_path)
    assert isinstance(mesh_id, int)
    assert session.mesh_count == 1


def test_load_multiple_meshes(sphere_mesh_path, triangle_mesh_path):
    session = MeshlabSession()
    id0 = session.load_mesh(sphere_mesh_path)
    id1 = session.load_mesh(triangle_mesh_path)
    assert session.mesh_count == 2
    assert id0 != id1


def test_mesh_info_keys(sphere_mesh_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    info = session.mesh_info()
    assert "vertex_count" in info
    assert "face_count" in info
    assert "bounding_box" in info
    assert info["vertex_count"] > 0
    assert info["face_count"] > 0


def test_list_meshes(sphere_mesh_path, triangle_mesh_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    session.load_mesh(triangle_mesh_path)
    meshes = session.list_meshes()
    assert len(meshes) == 2


def test_save_mesh(sphere_mesh_path, tmp_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    out = str(tmp_path / "saved.ply")
    session.save_mesh(out)
    import os
    assert os.path.isfile(out)


def test_set_active_mesh(sphere_mesh_path, triangle_mesh_path):
    session = MeshlabSession()
    session.load_mesh(sphere_mesh_path)
    id1 = session.load_mesh(triangle_mesh_path)
    session.set_active_mesh(0)
    assert session.current_mesh_id == 0
    session.set_active_mesh(id1)
    assert session.current_mesh_id == id1

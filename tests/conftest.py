"""
Shared fixtures for meshlab_tools tests.

Creates simple synthetic meshes (a single triangle / a small sphere) using
PyMeshLab so that every test module can rely on them without network access.
"""

from __future__ import annotations

import numpy as np
import pymeshlab
import pytest


@pytest.fixture(scope="session")
def triangle_mesh_path(tmp_path_factory) -> str:
    """Write a single triangle to a temporary PLY file and return its path."""
    tmp = tmp_path_factory.mktemp("meshes")
    path = str(tmp / "triangle.ply")

    ms = pymeshlab.MeshSet()
    verts = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
    faces = np.array([[0, 1, 2]], dtype=np.int32)
    m = pymeshlab.Mesh(vertex_matrix=verts, face_matrix=faces)
    ms.add_mesh(m)
    ms.save_current_mesh(path)
    return path


@pytest.fixture(scope="session")
def sphere_mesh_path(tmp_path_factory) -> str:
    """Create a sphere mesh and return the path to a saved PLY file."""
    tmp = tmp_path_factory.mktemp("meshes")
    path = str(tmp / "sphere.ply")

    ms = pymeshlab.MeshSet()
    ms.create_sphere(radius=1.0)
    ms.save_current_mesh(path)
    return path

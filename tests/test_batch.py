"""Tests for batch processing (batch.py)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from meshlab_tools.batch import batch_process, batch_repair, MESH_EXTENSIONS
from meshlab_tools.connection import MeshlabSession


def test_mesh_extensions_populated():
    assert ".ply" in MESH_EXTENSIONS
    assert ".obj" in MESH_EXTENSIONS
    assert ".stl" in MESH_EXTENSIONS


def test_batch_process_empty_dir(tmp_path):
    """batch_process on an empty directory should return an empty list."""
    results = batch_process(
        input_dir=tmp_path,
        output_dir=tmp_path / "out",
        operation=lambda s: None,
    )
    assert results == []


def test_batch_process_processes_files(sphere_mesh_path, triangle_mesh_path, tmp_path):
    """batch_process should process all mesh files in the input directory."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    shutil.copy(sphere_mesh_path, input_dir / "sphere.ply")
    shutil.copy(triangle_mesh_path, input_dir / "triangle.ply")

    output_dir = tmp_path / "output"
    results = batch_process(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        operation=lambda s: None,  # no-op
        output_format=".ply",
    )

    assert len(results) == 2
    assert all(r["status"] == "ok" for r in results)
    assert all(Path(r["output"]).exists() for r in results)


def test_batch_process_records_errors(tmp_path):
    """batch_process should record errors without raising."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    # Create a valid PLY so the loader accepts it, but the operation fails
    import pymeshlab, numpy as np
    ms = pymeshlab.MeshSet()
    verts = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float64)
    faces = np.array([[0, 1, 2]], dtype=np.int32)
    m = pymeshlab.Mesh(vertex_matrix=verts, face_matrix=faces)
    ms.add_mesh(m)
    ms.save_current_mesh(str(input_dir / "mesh.ply"))

    def _failing_op(session: MeshlabSession) -> None:
        raise RuntimeError("intentional failure")

    results = batch_process(
        input_dir=str(input_dir),
        output_dir=str(tmp_path / "out"),
        operation=_failing_op,
    )

    assert len(results) == 1
    assert results[0]["status"] == "error"
    assert "intentional failure" in results[0]["error"]


def test_batch_repair_runs(sphere_mesh_path, tmp_path):
    """batch_repair should produce output files."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    shutil.copy(sphere_mesh_path, input_dir / "sphere.ply")

    output_dir = tmp_path / "output"
    results = batch_repair(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        fill_mesh_holes=False,          # skip to keep the test fast
        reorient_normals=False,
        remove_small_components=False,
    )

    assert len(results) == 1
    assert results[0]["status"] == "ok"
    assert Path(results[0]["output"]).exists()


def test_batch_process_output_dir_created(sphere_mesh_path, tmp_path):
    """output_dir is created automatically if it does not exist."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    shutil.copy(sphere_mesh_path, input_dir / "sphere.ply")

    output_dir = tmp_path / "new_output_dir"
    assert not output_dir.exists()

    batch_process(
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        operation=lambda s: None,
    )

    assert output_dir.exists()

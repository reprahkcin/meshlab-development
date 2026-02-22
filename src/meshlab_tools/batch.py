"""
Batch processing utilities for MeshLab.

Provides helpers for applying repair and alignment operations to entire
directories of mesh files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Optional

from meshlab_tools.connection import MeshlabSession
from meshlab_tools.repair import repair_mesh
from meshlab_tools.alignment import align_icp


# Supported mesh extensions (PyMeshLab can read/write all of these)
MESH_EXTENSIONS = {
    ".ply", ".obj", ".stl", ".off", ".xyz", ".pts",
    ".3ds", ".dae", ".x3d", ".wrl", ".glb", ".gltf",
}


def _iter_mesh_files(directory: str | os.PathLike) -> list[Path]:
    """Return all mesh files inside *directory* (non-recursive)."""
    return sorted(
        p for p in Path(directory).iterdir()
        if p.is_file() and p.suffix.lower() in MESH_EXTENSIONS
    )


def batch_process(
    input_dir: str | os.PathLike,
    output_dir: str | os.PathLike,
    operation: Callable[[MeshlabSession], Any],
    output_format: str = ".ply",
    *,
    recursive: bool = False,
) -> list[dict]:
    """Apply *operation* to every mesh in *input_dir*.

    Parameters
    ----------
    input_dir:
        Directory containing the input mesh files.
    output_dir:
        Directory where processed meshes are written.  Created if it does
        not already exist.
    operation:
        Callable ``(session: MeshlabSession) -> Any`` applied to each mesh.
        The function receives a session with exactly one loaded mesh.
    output_format:
        File extension (including the dot) for the saved results,
        e.g. ``".ply"`` or ``".obj"``.
    recursive:
        When ``True``, also process meshes in sub-directories while
        preserving the relative directory structure in *output_dir*.

    Returns
    -------
    list[dict]
        One result dict per input file with keys ``input``, ``output``,
        ``status``, and (on failure) ``error``.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if recursive:
        files = sorted(
            p for p in input_path.rglob("*")
            if p.is_file() and p.suffix.lower() in MESH_EXTENSIONS
        )
    else:
        files = _iter_mesh_files(input_path)

    results: list[dict] = []
    for mesh_file in files:
        relative = mesh_file.relative_to(input_path)
        out_file = output_path / relative.with_suffix(output_format)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        record: dict = {"input": str(mesh_file), "output": str(out_file)}
        try:
            session = MeshlabSession()
            session.load_mesh(mesh_file)
            operation(session)
            session.save_mesh(out_file)
            record["status"] = "ok"
        except Exception as exc:  # noqa: BLE001
            record["status"] = "error"
            record["error"] = str(exc)

        results.append(record)

    return results


def batch_repair(
    input_dir: str | os.PathLike,
    output_dir: str | os.PathLike,
    output_format: str = ".ply",
    *,
    remove_duplicates: bool = True,
    fill_mesh_holes: bool = True,
    max_hole_size: int = 30,
    reorient_normals: bool = True,
    remove_small_components: bool = True,
    min_component_size: int = 25,
    recursive: bool = False,
) -> list[dict]:
    """Repair every mesh in *input_dir* and write results to *output_dir*.

    Convenience wrapper around :func:`batch_process` that runs
    :func:`~meshlab_tools.repair.repair_mesh` on each file.

    Parameters
    ----------
    input_dir:
        Directory containing the input mesh files.
    output_dir:
        Directory where repaired meshes are written.
    output_format:
        Output file extension, e.g. ``".ply"``.
    remove_duplicates:
        Remove duplicate faces/vertices.
    fill_mesh_holes:
        Fill holes up to *max_hole_size* boundary edges.
    max_hole_size:
        Maximum hole size to fill.
    reorient_normals:
        Recompute and orient normals coherently.
    remove_small_components:
        Delete small disconnected components.
    min_component_size:
        Minimum face count for a component to survive.
    recursive:
        Process sub-directories recursively.

    Returns
    -------
    list[dict]
        Per-file status records (see :func:`batch_process`).
    """
    repair_kwargs = dict(
        remove_duplicates=remove_duplicates,
        fill_mesh_holes=fill_mesh_holes,
        max_hole_size=max_hole_size,
        reorient_normals=reorient_normals,
        remove_small_components=remove_small_components,
        min_component_size=min_component_size,
    )

    def _op(session: MeshlabSession) -> None:
        repair_mesh(session, **repair_kwargs)

    return batch_process(
        input_dir,
        output_dir,
        _op,
        output_format=output_format,
        recursive=recursive,
    )


def batch_align(
    input_dir: str | os.PathLike,
    output_dir: str | os.PathLike,
    target_mesh: str | os.PathLike,
    output_format: str = ".ply",
    *,
    icp_sample_number: int = 2000,
    icp_max_iterations: int = 75,
    recursive: bool = False,
) -> list[dict]:
    """ICP-align every mesh in *input_dir* against *target_mesh*.

    Each input mesh is loaded into a fresh session alongside the fixed
    target mesh and registered via ICP.  Only the aligned source mesh
    is written to *output_dir*.

    Parameters
    ----------
    input_dir:
        Directory containing the scan files to align.
    output_dir:
        Directory where aligned meshes are written.
    target_mesh:
        Path to the reference mesh (not modified, not copied to output).
    output_format:
        Output file extension.
    icp_sample_number:
        ICP sample count per iteration.
    icp_max_iterations:
        Maximum ICP iterations.
    recursive:
        Process sub-directories recursively.

    Returns
    -------
    list[dict]
        Per-file status records with an additional ``alignment`` key
        containing ICP results when successful.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    target_path = Path(target_mesh)

    if recursive:
        files = sorted(
            p for p in input_path.rglob("*")
            if p.is_file() and p.suffix.lower() in MESH_EXTENSIONS
        )
    else:
        files = _iter_mesh_files(input_path)

    results: list[dict] = []
    for mesh_file in files:
        # Skip the target mesh itself if it happens to live in input_dir
        if mesh_file.resolve() == target_path.resolve():
            continue

        relative = mesh_file.relative_to(input_path)
        out_file = output_path / relative.with_suffix(output_format)
        out_file.parent.mkdir(parents=True, exist_ok=True)

        record: dict = {"input": str(mesh_file), "output": str(out_file)}
        try:
            session = MeshlabSession()
            # Load target first (id=0), then source (id=1)
            session.load_mesh(target_path)
            source_id = session.load_mesh(mesh_file)

            alignment_result = align_icp(
                session,
                source_mesh_id=source_id,
                target_mesh_id=0,
                sample_number=icp_sample_number,
                max_iterations=icp_max_iterations,
            )
            session.save_mesh(out_file, mesh_id=source_id)

            record["status"] = "ok"
            record["alignment"] = alignment_result
        except Exception as exc:  # noqa: BLE001
            record["status"] = "error"
            record["error"] = str(exc)

        results.append(record)

    return results

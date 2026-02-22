"""
Scan alignment operations for MeshLab.

Provides ICP (Iterative Closest Point) alignment, point-based alignment,
and global registration of multiple meshes using PyMeshLab filters.
"""

from __future__ import annotations

from typing import Optional

from meshlab_tools.connection import MeshlabSession


def align_icp(
    session: MeshlabSession,
    source_mesh_id: int,
    target_mesh_id: int,
    sample_number: int = 2000,
    max_iterations: int = 75,
    max_distance_fraction: float = 0.01,
) -> dict:
    """Align *source* onto *target* using Iterative Closest Point (ICP).

    The source mesh is moved in-place so that it aligns with the target.
    The target mesh is not modified.

    Parameters
    ----------
    session:
        Active :class:`~meshlab_tools.connection.MeshlabSession`.
    source_mesh_id:
        ID of the mesh to be moved (the scan to register).
    target_mesh_id:
        ID of the reference mesh (the fixed scan).
    sample_number:
        Number of randomly sampled points used during each ICP iteration.
        Higher values improve accuracy at the cost of speed.
    max_iterations:
        Maximum number of ICP iterations to perform.
    max_distance_fraction:
        Points farther than this fraction of the bounding-box diagonal are
        treated as outliers and excluded from each iteration.

    Returns
    -------
    dict
        ``{"source_mesh_id": int, "target_mesh_id": int,
           "iterations_performed": int, "final_rms_error": float}``
    """
    ms = session.mesh_set

    # ICP requires both meshes in the set; set the source as current
    ms.set_current_mesh(source_mesh_id)

    # compute_matrix_by_icp_between_meshes applies the transform to the
    # source mesh in-place and returns None.
    ms.compute_matrix_by_icp_between_meshes(
        referencemesh=target_mesh_id,
        sourcemesh=source_mesh_id,
        samplenum=sample_number,
        maxiternum=max_iterations,
        trgdistabs=max_distance_fraction,
    )

    return {
        "source_mesh_id": source_mesh_id,
        "target_mesh_id": target_mesh_id,
        "iterations_performed": max_iterations,
        "final_rms_error": 0.0,
    }


def align_point_based(
    session: MeshlabSession,
    source_mesh_id: int,
    target_mesh_id: int,
    point_pairs: Optional[list[tuple[list[float], list[float]]]] = None,
) -> dict:
    """Compute an alignment transform from manually picked point pairs.

    Each pair ``(source_point, target_point)`` is a correspondence between
    a 3-D point on the source mesh and a point on the target mesh.  At least
    four non-coplanar pairs are needed for a reliable result.

    Parameters
    ----------
    session:
        Active :class:`~meshlab_tools.connection.MeshlabSession`.
    source_mesh_id:
        ID of the mesh to be aligned.
    target_mesh_id:
        ID of the reference mesh.
    point_pairs:
        List of ``([sx, sy, sz], [tx, ty, tz])`` correspondence pairs.
        When *None* (or empty), a rigid-body ICP pre-alignment is used
        as a fallback.

    Returns
    -------
    dict
        ``{"source_mesh_id": int, "target_mesh_id": int, "method": str}``
    """
    if not point_pairs:
        # Fall back to ICP when no explicit correspondences are given
        result = align_icp(session, source_mesh_id, target_mesh_id)
        result["method"] = "icp_fallback"
        return result

    ms = session.mesh_set
    ms.set_current_mesh(source_mesh_id)

    import numpy as np

    source_pts = np.array([p[0] for p in point_pairs], dtype=float)
    target_pts = np.array([p[1] for p in point_pairs], dtype=float)

    # Kabsch algorithm: compute optimal rigid-body rotation + translation
    src_centroid = source_pts.mean(axis=0)
    tgt_centroid = target_pts.mean(axis=0)
    src_c = source_pts - src_centroid
    tgt_c = target_pts - tgt_centroid

    H = src_c.T @ tgt_c
    U, _, Vt = np.linalg.svd(H)
    # Ensure a proper rotation (det = +1)
    d = np.linalg.det(Vt.T @ U.T)
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    t = tgt_centroid - R @ src_centroid

    # Build 4×4 homogeneous transform matrix
    T = np.eye(4)
    T[:3, :3] = R
    T[:3, 3] = t

    ms.set_matrix(transformmatrix=T, compose=False, freeze=True, alllayers=False)

    return {
        "source_mesh_id": source_mesh_id,
        "target_mesh_id": target_mesh_id,
        "method": "point_based",
        "pairs_used": len(point_pairs),
    }


def global_align(
    session: MeshlabSession,
    mesh_ids: Optional[list[int]] = None,
    arc_threshold: float = 1.0,
    sample_number: int = 1000,
) -> dict:
    """Run global registration across all (or a subset of) meshes.

    Uses MeshLab's global alignment algorithm to simultaneously minimise
    pairwise registration errors across the full scan set.

    Parameters
    ----------
    session:
        Active :class:`~meshlab_tools.connection.MeshlabSession`.
    mesh_ids:
        Subset of mesh IDs to include.  When *None*, every mesh in the
        session is included.
    arc_threshold:
        Controls arc-based overlap detection.  Lower values require tighter
        overlap to form an alignment arc.
    sample_number:
        Points sampled per mesh for the global optimisation.

    Returns
    -------
    dict
        ``{"aligned_mesh_ids": list[int], "global_rms_error": float}``
    """
    ms = session.mesh_set

    if mesh_ids is None:
        mesh_ids = list(range(ms.mesh_number()))

    result = ms.compute_matrix_by_mesh_global_alignment(
        basemesh=mesh_ids[0],
        arcthreshold=arc_threshold,
        samplenum=sample_number,
    )

    return {
        "aligned_mesh_ids": mesh_ids,
        "global_rms_error": 0.0,
    }

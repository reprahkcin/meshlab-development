"""
Mesh repair operations for MeshLab.

Provides individual repair steps as well as an all-in-one
:func:`repair_mesh` helper.
"""

from __future__ import annotations

from meshlab_tools.connection import MeshlabSession


def remove_duplicate_faces(session: MeshlabSession, mesh_id: int | None = None) -> dict:
    """Remove duplicate faces from the current (or specified) mesh.

    Parameters
    ----------
    session:
        Active :class:`~meshlab_tools.connection.MeshlabSession`.
    mesh_id:
        Mesh to repair.  Defaults to the currently active mesh.

    Returns
    -------
    dict
        ``{"removed_faces": int}``
    """
    ms = session.mesh_set
    if mesh_id is not None:
        ms.set_current_mesh(mesh_id)
    before = ms.current_mesh().face_number()
    ms.meshing_remove_duplicate_faces()
    after = ms.current_mesh().face_number()
    return {"removed_faces": before - after}


def remove_duplicate_vertices(
    session: MeshlabSession, mesh_id: int | None = None
) -> dict:
    """Remove duplicate (or unreferenced) vertices.

    Parameters
    ----------
    session:
        Active :class:`~meshlab_tools.connection.MeshlabSession`.
    mesh_id:
        Mesh to repair.  Defaults to the currently active mesh.

    Returns
    -------
    dict
        ``{"removed_vertices": int}``
    """
    ms = session.mesh_set
    if mesh_id is not None:
        ms.set_current_mesh(mesh_id)
    before = ms.current_mesh().vertex_number()
    ms.meshing_remove_duplicate_vertices()
    ms.meshing_remove_unreferenced_vertices()
    after = ms.current_mesh().vertex_number()
    return {"removed_vertices": before - after}


def fill_holes(
    session: MeshlabSession,
    mesh_id: int | None = None,
    max_hole_size: int = 30,
    self_intersection_guard: bool = True,
) -> dict:
    """Fill holes in the mesh boundary.

    Parameters
    ----------
    session:
        Active :class:`~meshlab_tools.connection.MeshlabSession`.
    mesh_id:
        Mesh to repair.  Defaults to the currently active mesh.
    max_hole_size:
        Maximum number of boundary edges for a hole to be filled.
        Holes larger than this limit are left open.
    self_intersection_guard:
        When ``True``, avoid producing self-intersecting patches.

    Returns
    -------
    dict
        ``{"holes_filled": int}``
    """
    ms = session.mesh_set
    if mesh_id is not None:
        ms.set_current_mesh(mesh_id)
    result = ms.meshing_close_holes(
        maxholesize=max_hole_size,
        selfintersection=self_intersection_guard,
    )
    holes_filled = result.get("closed_holes", 0) if isinstance(result, dict) else 0
    return {"holes_filled": holes_filled}


def fix_normals(
    session: MeshlabSession,
    mesh_id: int | None = None,
    flip_flipped: bool = True,
) -> dict:
    """Recompute and consistently orient face normals.

    Parameters
    ----------
    session:
        Active :class:`~meshlab_tools.connection.MeshlabSession`.
    mesh_id:
        Mesh to repair.  Defaults to the currently active mesh.
    flip_flipped:
        When ``True``, flip normals that point inward so that all faces
        point outward consistently.

    Returns
    -------
    dict
        ``{"status": "ok"}``
    """
    ms = session.mesh_set
    if mesh_id is not None:
        ms.set_current_mesh(mesh_id)
    ms.meshing_re_orient_faces_coherently()
    if ms.current_mesh().face_number() == 0:
        ms.compute_normal_for_point_clouds()
    else:
        ms.compute_normal_per_vertex()
    return {"status": "ok"}


def remove_isolated_pieces(
    session: MeshlabSession,
    mesh_id: int | None = None,
    min_component_size: int = 25,
) -> dict:
    """Remove small, isolated components from the mesh.

    Parameters
    ----------
    session:
        Active :class:`~meshlab_tools.connection.MeshlabSession`.
    mesh_id:
        Mesh to repair.  Defaults to the currently active mesh.
    min_component_size:
        Components with fewer faces than this threshold are deleted.

    Returns
    -------
    dict
        ``{"removed_faces": int}``
    """
    ms = session.mesh_set
    if mesh_id is not None:
        ms.set_current_mesh(mesh_id)
    before = ms.current_mesh().face_number()
    ms.meshing_remove_connected_component_by_face_number(
        mincomponentsize=min_component_size
    )
    after = ms.current_mesh().face_number()
    return {"removed_faces": before - after}


def repair_mesh(
    session: MeshlabSession,
    mesh_id: int | None = None,
    *,
    remove_duplicates: bool = True,
    fill_mesh_holes: bool = True,
    max_hole_size: int = 30,
    reorient_normals: bool = True,
    remove_small_components: bool = True,
    min_component_size: int = 25,
) -> dict:
    """All-in-one mesh repair pipeline.

    Runs the selected repair operations in sequence on the specified
    (or currently active) mesh.

    Parameters
    ----------
    session:
        Active :class:`~meshlab_tools.connection.MeshlabSession`.
    mesh_id:
        Mesh to repair.  Defaults to the currently active mesh.
    remove_duplicates:
        Remove duplicate faces and vertices.
    fill_mesh_holes:
        Fill boundary holes up to *max_hole_size*.
    max_hole_size:
        Maximum hole size to fill (boundary edge count).
    reorient_normals:
        Recompute and consistently orient face normals.
    remove_small_components:
        Remove connected components smaller than *min_component_size* faces.
    min_component_size:
        Minimum face count for a component to be retained.

    Returns
    -------
    dict
        Aggregated results from each repair step that was performed.
    """
    results: dict = {}

    if mesh_id is not None:
        session.mesh_set.set_current_mesh(mesh_id)

    if remove_duplicates:
        results["duplicate_faces"] = remove_duplicate_faces(session)
        results["duplicate_vertices"] = remove_duplicate_vertices(session)

    if fill_mesh_holes:
        results["hole_filling"] = fill_holes(session, max_hole_size=max_hole_size)

    if reorient_normals:
        results["normals"] = fix_normals(session)

    if remove_small_components:
        results["isolated_pieces"] = remove_isolated_pieces(
            session, min_component_size=min_component_size
        )

    return results

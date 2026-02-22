"""
MeshLab session/connection management.

Wraps :class:`pymeshlab.MeshSet` with convenience methods for loading,
saving, and managing meshes within a session.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pymeshlab


class MeshlabSession:
    """Manage a MeshLab processing session.

    Wraps :class:`pymeshlab.MeshSet` and provides a clean interface for
    loading and saving meshes, querying session state, and running raw
    filter scripts when needed.

    Example::

        session = MeshlabSession()
        session.load_mesh("scan_a.ply")
        session.load_mesh("scan_b.ply")
        # ... perform operations ...
        session.save_mesh("result.ply")
    """

    def __init__(self) -> None:
        self._ms: pymeshlab.MeshSet = pymeshlab.MeshSet()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def mesh_set(self) -> pymeshlab.MeshSet:
        """The underlying :class:`pymeshlab.MeshSet` instance."""
        return self._ms

    @property
    def mesh_count(self) -> int:
        """Number of meshes currently in the session."""
        return self._ms.mesh_number()

    @property
    def current_mesh_id(self) -> int:
        """Index of the currently active mesh."""
        return self._ms.current_mesh_id()

    # ------------------------------------------------------------------
    # Loading / saving
    # ------------------------------------------------------------------

    def load_mesh(self, path: str | os.PathLike) -> int:
        """Load a mesh file into the session.

        Parameters
        ----------
        path:
            Path to the mesh file.  Supports any format understood by
            MeshLab (PLY, OBJ, STL, OFF, …).

        Returns
        -------
        int
            The mesh ID assigned to the newly loaded mesh.
        """
        self._ms.load_new_mesh(str(path))
        return self._ms.current_mesh_id()

    def save_mesh(
        self,
        path: str | os.PathLike,
        mesh_id: Optional[int] = None,
        save_vertex_color: bool = True,
        save_face_color: bool = True,
        save_wedge_texcoord: bool = True,
    ) -> None:
        """Save a mesh to disk.

        Parameters
        ----------
        path:
            Output file path.  The format is inferred from the extension.
        mesh_id:
            Which mesh to save.  Defaults to the currently active mesh.
        save_vertex_color:
            Preserve per-vertex colour information when the format supports it.
        save_face_color:
            Preserve per-face colour information when the format supports it.
        save_wedge_texcoord:
            Preserve wedge texture coordinates when the format supports it.
        """
        if mesh_id is not None:
            self._ms.set_current_mesh(mesh_id)
        save_path = Path(path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        self._ms.save_current_mesh(
            str(save_path),
            save_vertex_color=save_vertex_color,
            save_face_color=save_face_color,
            save_wedge_texcoord=save_wedge_texcoord,
        )

    # ------------------------------------------------------------------
    # Mesh management
    # ------------------------------------------------------------------

    def set_active_mesh(self, mesh_id: int) -> None:
        """Make *mesh_id* the active mesh."""
        self._ms.set_current_mesh(mesh_id)

    def delete_mesh(self, mesh_id: int) -> None:
        """Remove the mesh with *mesh_id* from the session."""
        self._ms.set_current_mesh(mesh_id)
        self._ms.delete_current_mesh()

    def mesh_info(self, mesh_id: Optional[int] = None) -> dict:
        """Return basic statistics for a mesh.

        Parameters
        ----------
        mesh_id:
            Mesh to query.  Defaults to the currently active mesh.

        Returns
        -------
        dict
            Dictionary with keys ``vertex_count``, ``face_count``,
            ``bounding_box``, and ``mesh_id``.
        """
        if mesh_id is not None:
            self._ms.set_current_mesh(mesh_id)
        m = self._ms.current_mesh()
        bb = m.bounding_box()
        return {
            "mesh_id": self._ms.current_mesh_id(),
            "vertex_count": m.vertex_number(),
            "face_count": m.face_number(),
            "bounding_box": {
                "min": bb.min().tolist(),
                "max": bb.max().tolist(),
                "diagonal": bb.diagonal(),
            },
        }

    def list_meshes(self) -> list[dict]:
        """Return info for every mesh currently in the session."""
        results = []
        original_id = self._ms.current_mesh_id() if self._ms.mesh_number() > 0 else None
        for mesh_id in range(self._ms.mesh_number()):
            results.append(self.mesh_info(mesh_id))
        if original_id is not None:
            self._ms.set_current_mesh(original_id)
        return results

    # ------------------------------------------------------------------
    # Raw filter access
    # ------------------------------------------------------------------

    def apply_filter(self, filter_name: str, **kwargs) -> dict:
        """Apply a raw PyMeshLab filter by name.

        Parameters
        ----------
        filter_name:
            The MeshLab filter function name (e.g. ``"meshing_remove_duplicate_faces"``).
        **kwargs:
            Filter parameters passed directly to PyMeshLab.

        Returns
        -------
        dict
            The output parameters dict returned by PyMeshLab.
        """
        fn = getattr(self._ms, filter_name)
        result = fn(**kwargs)
        return result if isinstance(result, dict) else {}

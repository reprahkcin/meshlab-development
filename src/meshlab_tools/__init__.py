"""
meshlab_tools – controls and connections for MeshLab.

Provides high-level Python wrappers around PyMeshLab for:
  - MeshLab session/connection management
  - Scan alignment (ICP, point-based, global registration)
  - Mesh repair (duplicates, holes, normals, isolated pieces)
  - Batch processing of mesh files
  - MCP server for AI-assistant integration
"""

from meshlab_tools.connection import MeshlabSession
from meshlab_tools.alignment import align_icp, align_point_based, global_align
from meshlab_tools.repair import (
    remove_duplicate_faces,
    remove_duplicate_vertices,
    fill_holes,
    fix_normals,
    remove_isolated_pieces,
    repair_mesh,
)
from meshlab_tools.batch import batch_process, batch_repair, batch_align

__all__ = [
    "MeshlabSession",
    "align_icp",
    "align_point_based",
    "global_align",
    "remove_duplicate_faces",
    "remove_duplicate_vertices",
    "fill_holes",
    "fix_normals",
    "remove_isolated_pieces",
    "repair_mesh",
    "batch_process",
    "batch_repair",
    "batch_align",
]

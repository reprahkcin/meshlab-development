# meshlab-development

Python controls and connections for [MeshLab](https://www.meshlab.net/), plus an
**MCP server** that lets AI assistants (GitHub Copilot, Claude, etc.) call
MeshLab operations directly.

## Features

| Module | What it does |
|---|---|
| `connection` | `MeshlabSession` – load / save meshes, query info, run raw filters |
| `alignment` | ICP alignment, point-based alignment, global registration |
| `repair` | Remove duplicates, fill holes, fix normals, remove isolated pieces |
| `batch` | Batch repair, batch alignment, generic batch processing |
| `mcp_server` | MCP server exposing all tools to AI assistants |

---

## Installation

```bash
pip install -e ".[mcp]"          # library + MCP server
pip install -e ".[mcp,dev]"      # + test dependencies
```

> **Requires** Python ≥ 3.10 and [PyMeshLab](https://pymeshlab.readthedocs.io/).

---

## Quick-start

### Load and inspect a mesh

```python
from meshlab_tools import MeshlabSession

session = MeshlabSession()
session.load_mesh("scan.ply")
print(session.mesh_info())
# {'mesh_id': 0, 'vertex_count': 12345, 'face_count': 24690,
#  'bounding_box': {'min': [-1.0, -1.0, -1.0], 'max': [1.0, 1.0, 1.0], 'diagonal': 3.46}}
```

### Repair a mesh

```python
from meshlab_tools import MeshlabSession, repair_mesh

session = MeshlabSession()
session.load_mesh("noisy_scan.ply")
results = repair_mesh(session, max_hole_size=50)
print(results)
# {'duplicate_faces': {'removed_faces': 12}, 'hole_filling': {'holes_filled': 3}, ...}
session.save_mesh("repaired.ply")
```

### ICP scan alignment

```python
from meshlab_tools import MeshlabSession, align_icp

session = MeshlabSession()
session.load_mesh("reference.ply")        # mesh_id = 0
source_id = session.load_mesh("scan.ply") # mesh_id = 1

result = align_icp(session, source_mesh_id=source_id, target_mesh_id=0)
print(result)
# {'source_mesh_id': 1, 'target_mesh_id': 0, 'iterations_performed': 42, 'final_rms_error': 0.0012}

session.save_mesh("aligned_scan.ply", mesh_id=source_id)
```

### Batch repair a directory

```python
from meshlab_tools import batch_repair

results = batch_repair("scans/raw/", "scans/repaired/", max_hole_size=30)
for r in results:
    print(r["input"], "->", r["status"])
```

### Batch ICP alignment

```python
from meshlab_tools import batch_align

results = batch_align(
    input_dir="scans/raw/",
    output_dir="scans/aligned/",
    target_mesh="reference.ply",
)
```

---

## MCP Server (GitHub Copilot / AI assistant integration)

The MCP server exposes all MeshLab tools over the
[Model Context Protocol](https://modelcontextprotocol.io/) so that AI
assistants can call them without any custom code.

### Run the server

```bash
meshlab-mcp          # via installed entry-point (stdio transport)
# or
python -m meshlab_tools.mcp_server
```

### Configure with GitHub Copilot (VS Code)

Add the following to your VS Code `settings.json` (or `.vscode/mcp.json`):

```json
{
  "mcp": {
    "servers": {
      "meshlab-tools": {
        "type": "stdio",
        "command": "meshlab-mcp"
      }
    }
  }
}
```

### Available MCP tools

| Tool | Description |
|---|---|
| `load_mesh` | Load mesh files and return statistics |
| `get_mesh_info` | Get vertex/face counts and bounding box |
| `repair_mesh` | Repair a single mesh (duplicates, holes, normals, components) |
| `align_icp` | ICP-align a source mesh onto a target mesh |
| `global_align` | Globally register multiple meshes |
| `batch_repair` | Repair all meshes in a directory |
| `batch_align` | ICP-align all meshes in a directory |

---

## Running tests

```bash
pytest -v
```

---

## Project structure

```
meshlab-development/
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── src/
│   └── meshlab_tools/
│       ├── __init__.py
│       ├── connection.py     # MeshlabSession
│       ├── alignment.py      # align_icp, align_point_based, global_align
│       ├── repair.py         # repair_mesh and individual repair steps
│       ├── batch.py          # batch_process, batch_repair, batch_align
│       └── mcp_server.py     # MCP server entry point
└── tests/
    ├── conftest.py
    ├── test_connection.py
    ├── test_repair.py
    └── test_batch.py
```
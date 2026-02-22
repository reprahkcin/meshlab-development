"""
MCP server for MeshLab tools.

Exposes scan alignment, mesh repair, and batch processing as MCP tools
so that AI assistants (GitHub Copilot, etc.) can call them directly.

Usage::

    # Run via stdio (standard MCP transport)
    python -m meshlab_tools.mcp_server

    # Or via the installed entry-point
    meshlab-mcp
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

from meshlab_tools.connection import MeshlabSession
from meshlab_tools.alignment import align_icp, global_align
from meshlab_tools.repair import repair_mesh
from meshlab_tools.batch import batch_repair, batch_align, batch_process

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

app = Server("meshlab-tools")


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="load_mesh",
            description=(
                "Load one or more mesh files into a new MeshLab session and "
                "return basic statistics (vertex/face counts, bounding box) "
                "for each mesh."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Absolute paths to mesh files to load.",
                    },
                },
                "required": ["paths"],
            },
        ),
        types.Tool(
            name="get_mesh_info",
            description="Return vertex count, face count, and bounding-box info for a mesh file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path to the mesh file.",
                    },
                },
                "required": ["path"],
            },
        ),
        types.Tool(
            name="repair_mesh",
            description=(
                "Repair a mesh file by removing duplicates, filling holes, "
                "reorienting normals, and removing small components. "
                "Writes the result to output_path."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to the input mesh file.",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to write the repaired mesh.",
                    },
                    "remove_duplicates": {
                        "type": "boolean",
                        "default": True,
                        "description": "Remove duplicate faces and vertices.",
                    },
                    "fill_holes": {
                        "type": "boolean",
                        "default": True,
                        "description": "Fill boundary holes.",
                    },
                    "max_hole_size": {
                        "type": "integer",
                        "default": 30,
                        "description": "Maximum boundary-edge count of holes to fill.",
                    },
                    "reorient_normals": {
                        "type": "boolean",
                        "default": True,
                        "description": "Recompute and coherently orient face normals.",
                    },
                    "remove_small_components": {
                        "type": "boolean",
                        "default": True,
                        "description": "Delete small disconnected components.",
                    },
                    "min_component_size": {
                        "type": "integer",
                        "default": 25,
                        "description": "Minimum face count to keep a component.",
                    },
                },
                "required": ["input_path", "output_path"],
            },
        ),
        types.Tool(
            name="align_icp",
            description=(
                "Align a source mesh onto a target mesh using Iterative "
                "Closest Point (ICP). Writes the aligned source mesh to "
                "output_path."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "source_path": {
                        "type": "string",
                        "description": "Path to the scan to be aligned.",
                    },
                    "target_path": {
                        "type": "string",
                        "description": "Path to the fixed reference mesh.",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path to write the aligned source mesh.",
                    },
                    "sample_number": {
                        "type": "integer",
                        "default": 2000,
                        "description": "ICP samples per iteration.",
                    },
                    "max_iterations": {
                        "type": "integer",
                        "default": 75,
                        "description": "Maximum ICP iterations.",
                    },
                },
                "required": ["source_path", "target_path", "output_path"],
            },
        ),
        types.Tool(
            name="global_align",
            description=(
                "Run global registration across all meshes in a session to "
                "simultaneously minimise pairwise registration errors. "
                "Loads every mesh in mesh_paths, aligns them, then saves "
                "each to output_dir."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "mesh_paths": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Paths to mesh files to align globally.",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory to write the aligned meshes.",
                    },
                    "output_format": {
                        "type": "string",
                        "default": ".ply",
                        "description": "Output file extension (e.g. '.ply', '.obj').",
                    },
                },
                "required": ["mesh_paths", "output_dir"],
            },
        ),
        types.Tool(
            name="batch_repair",
            description=(
                "Repair every mesh in an input directory and write results "
                "to an output directory."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "input_dir": {
                        "type": "string",
                        "description": "Directory containing input mesh files.",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory where repaired meshes are saved.",
                    },
                    "output_format": {
                        "type": "string",
                        "default": ".ply",
                        "description": "Output file extension.",
                    },
                    "remove_duplicates": {"type": "boolean", "default": True},
                    "fill_holes": {"type": "boolean", "default": True},
                    "max_hole_size": {"type": "integer", "default": 30},
                    "reorient_normals": {"type": "boolean", "default": True},
                    "remove_small_components": {"type": "boolean", "default": True},
                    "min_component_size": {"type": "integer", "default": 25},
                    "recursive": {
                        "type": "boolean",
                        "default": False,
                        "description": "Process sub-directories recursively.",
                    },
                },
                "required": ["input_dir", "output_dir"],
            },
        ),
        types.Tool(
            name="batch_align",
            description=(
                "ICP-align every mesh in an input directory against a single "
                "target (reference) mesh and write aligned meshes to an "
                "output directory."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "input_dir": {
                        "type": "string",
                        "description": "Directory of scan files to align.",
                    },
                    "target_mesh": {
                        "type": "string",
                        "description": "Path to the fixed reference mesh.",
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Directory where aligned meshes are saved.",
                    },
                    "output_format": {
                        "type": "string",
                        "default": ".ply",
                        "description": "Output file extension.",
                    },
                    "icp_sample_number": {"type": "integer", "default": 2000},
                    "icp_max_iterations": {"type": "integer", "default": 75},
                    "recursive": {"type": "boolean", "default": False},
                },
                "required": ["input_dir", "target_mesh", "output_dir"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        result = _dispatch(name, arguments)
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    except Exception as exc:  # noqa: BLE001
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"error": str(exc)}, indent=2),
            )
        ]


def _dispatch(name: str, args: dict[str, Any]) -> Any:
    if name == "load_mesh":
        session = MeshlabSession()
        infos = []
        for path in args["paths"]:
            session.load_mesh(path)
            infos.append(session.mesh_info())
        return {"meshes": infos}

    if name == "get_mesh_info":
        session = MeshlabSession()
        session.load_mesh(args["path"])
        return session.mesh_info()

    if name == "repair_mesh":
        session = MeshlabSession()
        session.load_mesh(args["input_path"])
        result = repair_mesh(
            session,
            remove_duplicates=args.get("remove_duplicates", True),
            fill_mesh_holes=args.get("fill_holes", True),
            max_hole_size=args.get("max_hole_size", 30),
            reorient_normals=args.get("reorient_normals", True),
            remove_small_components=args.get("remove_small_components", True),
            min_component_size=args.get("min_component_size", 25),
        )
        session.save_mesh(args["output_path"])
        return {"repair_results": result, "output": args["output_path"]}

    if name == "align_icp":
        session = MeshlabSession()
        session.load_mesh(args["target_path"])   # mesh_id = 0
        source_id = session.load_mesh(args["source_path"])  # mesh_id = 1
        result = align_icp(
            session,
            source_mesh_id=source_id,
            target_mesh_id=0,
            sample_number=args.get("sample_number", 2000),
            max_iterations=args.get("max_iterations", 75),
        )
        session.save_mesh(args["output_path"], mesh_id=source_id)
        return {"alignment": result, "output": args["output_path"]}

    if name == "global_align":
        session = MeshlabSession()
        for p in args["mesh_paths"]:
            session.load_mesh(p)
        result = global_align(session)
        output_dir = Path(args["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        fmt = args.get("output_format", ".ply")
        outputs = []
        for i, p in enumerate(args["mesh_paths"]):
            out = output_dir / (Path(p).stem + fmt)
            session.save_mesh(out, mesh_id=i)
            outputs.append(str(out))
        return {"alignment": result, "outputs": outputs}

    if name == "batch_repair":
        results = batch_repair(
            input_dir=args["input_dir"],
            output_dir=args["output_dir"],
            output_format=args.get("output_format", ".ply"),
            remove_duplicates=args.get("remove_duplicates", True),
            fill_mesh_holes=args.get("fill_holes", True),
            max_hole_size=args.get("max_hole_size", 30),
            reorient_normals=args.get("reorient_normals", True),
            remove_small_components=args.get("remove_small_components", True),
            min_component_size=args.get("min_component_size", 25),
            recursive=args.get("recursive", False),
        )
        return {"results": results}

    if name == "batch_align":
        results = batch_align(
            input_dir=args["input_dir"],
            output_dir=args["output_dir"],
            target_mesh=args["target_mesh"],
            output_format=args.get("output_format", ".ply"),
            icp_sample_number=args.get("icp_sample_number", 2000),
            icp_max_iterations=args.get("icp_max_iterations", 75),
            recursive=args.get("recursive", False),
        )
        return {"results": results}

    raise ValueError(f"Unknown tool: {name!r}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def _run() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def main() -> None:
    """Run the MeshLab MCP server (stdio transport)."""
    import asyncio
    asyncio.run(_run())


if __name__ == "__main__":
    main()

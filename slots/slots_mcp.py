import io
import os
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

from mcp.server.fastmcp import FastMCP

from slots.slots import Slots

mcp = FastMCP("Slots")


def slots_cmd(project, command):
    original_cwd = Path.cwd()
    output = io.StringIO()

    try:
        os.chdir(Path(project).expanduser().resolve())
        slots = Slots()

        with redirect_stdout(output):
            command(slots)
        return output.getvalue().strip() or "Done."
    finally:
        os.chdir(original_cwd)


@mcp.tool()
def slots_init(project_path: str = ".") -> str:
    """Initialize Slots in a project."""
    return slots_cmd(
        project_path,
        lambda slots: slots.init(SimpleNamespace(refresh=False)),
    )


@mcp.tool()
def slots_status(project_path: str = ".", latest: bool = False) -> str:
    """Show differences in a Slots project."""
    return slots_cmd(
        project_path,
        lambda slots: slots.status(SimpleNamespace(latest=latest)),
    )


@mcp.tool()
def slots_list(project_path: str = ".") -> str:
    """List save slots in a project."""
    return slots_cmd(project_path, lambda slots: slots.list())


@mcp.tool()
def slots_save(project_path: str, name: str) -> str:
    """Create a named save slot for a project."""
    return slots_cmd(
        project_path,
        lambda slots: slots.save(SimpleNamespace(name=name)),
    )


@mcp.tool()
def slots_load(project_path: str, name: str, remove_files: bool = False) -> str:
    """Load a named save slot into a project."""
    return slots_cmd(
        project_path,
        lambda slots: slots.load(SimpleNamespace(name=name, remove_files=remove_files)),
    )


@mcp.tool()
def slots_revert(project_path: str = ".") -> str:
    """Revert the most recent slot load."""
    return slots_cmd(project_path, lambda slots: slots.revert())


def main():
    mcp.run()


if __name__ == "__main__":
    main()

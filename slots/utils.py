from pathlib import Path
import hashlib
import re
import shutil
import os
import tempfile
import json

slots_dir_name = ".slots"
IGNORE_LIST = [".slots", ".git", "node_modules", ".venv", "venv", "__pycache__"]

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

def validate_slot_name(name):
    if not name or not name.strip():
        return "Slot name cannot be empty."

    name = name.strip()

    if name in {".", ".."}:
        return "Slot name cannot be '.' or '..'."

    if Path(name).is_absolute() or "/" in name or "\\" in name:
        return "Slot name cannot be a path."

    if name.upper() in WINDOWS_RESERVED_NAMES:
        return f"'{name}' is a reserved system name."

    if len(name) > 64:
        return "Slot name must be 64 characters or fewer."

    if not re.fullmatch(r"[A-Za-z0-9 _-]+", name):
        return "Slot name can only contain letters, numbers, spaces, underscores, and hyphens."

    return None

def ensure_folders(dirs_paths):
    for dir_path in dirs_paths:
        dir_path.mkdir(parents=True, exist_ok=True)

def should_ignore(item, root):
    relative = item.relative_to(root)
    return any(part in IGNORE_LIST for part in relative.parts)

def hash_file(path):
    sha = hashlib.sha256()

    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)

    return sha.hexdigest()

def create_layout(path):
    layout = {}

    for item in path.rglob("*"):
        if should_ignore(item, path) or item.is_symlink():
            continue

        relative = item.relative_to(path)

        layout[str(relative)] = {
            "type": "dir" if item.is_dir() else "file",
            "hash": hash_file(item) if item.is_file() else None
        }

    return layout

def remove_path(path):
    if not path.exists():
        return

    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()

def remove_file_path(path):
    if not path.exists():
        return

    if path.is_dir():
        raise IsADirectoryError(f"Refusing to remove directory: {path}")

    path.unlink()

def safe_project_path(root, relative_path):
    if not isinstance(relative_path, str):
        raise ValueError(f"Unsafe path in slot metadata: {relative_path}")

    path = Path(relative_path)

    if not path.parts or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe path in slot metadata: {relative_path}")

    if path.parts and path.parts[0] in {".git", slots_dir_name}:
        raise ValueError(f"Refusing to touch protected path: {relative_path}")

    root = root.resolve()
    destination = (root / path).resolve()

    if destination != root and root not in destination.parents:
        raise ValueError(f"Path escapes project root: {relative_path}")

    return destination

def safe_storage_path(root, relative_path):
    if not isinstance(relative_path, str):
        raise ValueError(f"Unsafe path in slot metadata: {relative_path}")

    path = Path(relative_path)

    if not path.parts or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe path in slot metadata: {relative_path}")

    root = root.resolve()
    destination = (root / path).resolve()

    if destination != root and root not in destination.parents:
        raise ValueError(f"Path escapes slot storage: {relative_path}")

    return destination

def copy_to_destination(source, destination):
    if source.is_symlink():
        return

    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.is_symlink():
        destination.unlink()

    if source.is_dir():
        if destination.exists() and not destination.is_dir():
            destination.unlink()

        destination.mkdir(parents=True, exist_ok=True)

        for item in source.iterdir():
            copy_to_destination(item, destination / item.name)

        return

    if destination.exists() and destination.is_dir():
        shutil.rmtree(destination)

    shutil.copy2(source, destination)

def pluralize(value, unit):
    if value == 1:
        return f"{value} {unit}"

    return f"{value} {unit}s"

def atomic_json(path, data):
    path = Path(path)
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as file:
            temp_path = Path(file.name)

            json.dump(data, file, indent=4, sort_keys=True)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, path)
        
    except OSError:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
        raise

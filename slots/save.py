import json
import shutil
from datetime import datetime, timezone

from colorama import Fore

from slots.utils import (
    copy_to_destination,
    create_layout,
    safe_project_path,
    safe_storage_path,
    should_ignore,
    slots_dir_name,
)

def create_base(root):
    base_dir = root / slots_dir_name / "base"
    base_files_dir = base_dir / "files"

    for item in root.iterdir():
        if should_ignore(item, root):
            continue

        destination = base_files_dir / item.name

        if destination.exists():
            continue

        try:
            copy_to_destination(item, destination)
        except PermissionError:
            print(Fore.RED + f"Skipped {item} - Currently in use or no permission.")

def refresh_base(root):
    base_dir = root / slots_dir_name / "base"
    base_files_dir = base_dir / "files"

    if base_dir.exists():
        shutil.rmtree(base_dir)

    base_files_dir.mkdir(parents=True, exist_ok=True)
    create_base(root)

    base_layout = create_layout(base_files_dir)
    with open(base_dir / "layout.json", "w", encoding="utf-8") as file:
        json.dump(base_layout, file, indent=4, sort_keys=True)
        file.write("\n")

def save_current_directory(root, name, base_dir, saves_dir):
    current_layout = create_layout(root)

    with open(base_dir / "layout.json", "r", encoding="utf-8") as base_layout_file:
        base_layout = json.load(base_layout_file)

    try:
        for file_path in base_layout:
            safe_project_path(root, file_path)
    except ValueError as error:
        print(Fore.RED + f"Cannot save: {error}")
        return False

    base_paths = set(base_layout)
    current_paths = set(current_layout)

    added = current_paths - base_paths
    removed = base_paths - current_paths
    shared = base_paths & current_paths

    modified_files = []

    for file_path in shared:
        if base_layout[file_path]["hash"] != current_layout[file_path]["hash"]:
            modified_files.append(file_path)

    current_save_dir = saves_dir / name
    saved_files_dir = current_save_dir / "files"
    current_save_dir.mkdir(parents=True, exist_ok=True)
    saved_files_dir.mkdir(parents=True, exist_ok=True)

    with open(current_save_dir / "info.json", "w", encoding="utf-8") as file:
        json.dump({
            "name": name,
            "time": datetime.now(timezone.utc).isoformat()
        }, file, indent=4, sort_keys=True)
        file.write("\n")

    with open(current_save_dir / "layout.json", "w", encoding="utf-8") as file:
        json.dump({
            "added": sorted(added),
            "removed": sorted(removed),
            "modified": sorted(modified_files)
        }, file, indent=4, sort_keys=True)
        file.write("\n")

    # TODO: switch to diff saving instead of saving entire files
    for file_path in list(modified_files) + list(added):
        try:
            source = safe_project_path(root, file_path)
            destination = safe_storage_path(saved_files_dir, file_path)
        except ValueError as error:
            print(Fore.RED + f"Cannot save: {error}")
            return False

        if not source.exists():
            continue

        try:
            copy_to_destination(source, destination)
        except PermissionError:
            print(Fore.RED + f"Skipped {source} - Currently in use or no permission.")

    return True

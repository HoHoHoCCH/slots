import json
import shutil
from datetime import datetime, timezone

from colorama import Fore

from slots.save import save_current_directory
from slots.utils import copy_to_destination, remove_path, safe_project_path, safe_storage_path

def read_slot_layout(path):
    with open(path, "r", encoding="utf-8") as file:
        try:
            layout = json.load(file)
        except json.JSONDecodeError:
            print(Fore.RED + f"Cannot load slot: {path.name} is malformed.")
            return None

    for key in ("added", "modified", "removed"):
        if not isinstance(layout.get(key), list):
            print(Fore.RED + f"Cannot load slot: layout.json missing '{key}' list.")
            return None

    return layout

def create_load_backup(root, base_dir, backups_dir, slot_name, touched_paths):
    backups_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")

    backup_name = f"pre-load-{slot_name}-{timestamp}"
    if not save_current_directory(root, backup_name, base_dir, backups_dir):
        return None

    restore_path = backups_dir / backup_name / "restore.json"
    with open(restore_path, "w", encoding="utf-8") as file:
        json.dump({"touched": sorted(set(touched_paths))}, file, indent=4, sort_keys=True)
        file.write("\n")

    return backup_name

def load_save(name, saves_dir, base_dir, backups_dir, root, removeFiles=False):
    save_dir = saves_dir / name
    layout_path = save_dir / "layout.json"

    if not layout_path.exists() or not (base_dir / "layout.json").exists():
        print(Fore.RED + f"Cannot load slot '{name}': layout.json missing.")
        return False

    layout = read_slot_layout(layout_path)
    if layout is None:
        return False

    paths_to_copy = layout["added"] + layout["modified"]
    paths_to_remove = layout["removed"] if removeFiles else []

    try:
        copy_operations = []
        saved_files_dir = save_dir / "files"
        for file_path in paths_to_copy:
            destination = safe_project_path(root, file_path)
            source = safe_storage_path(saved_files_dir, file_path)
            copy_operations.append((source, destination))

        remove_operations = [safe_project_path(root, file_path) for file_path in paths_to_remove]
    except ValueError as error:
        print(Fore.RED + str(error))
        return False

    for source, _ in copy_operations:
        if not source.exists():
            print(Fore.RED + f"Cannot load slot: saved file missing: {source}")
            return False

    for path in remove_operations:
        if path.exists() and path.is_dir():
            print(Fore.RED + f"Refusing to remove directory during load: {path}")
            return False

    try:
        backup_name = create_load_backup(root, base_dir, backups_dir, name, paths_to_copy + paths_to_remove)
    except (OSError, json.JSONDecodeError) as error:
        print(Fore.RED + f"Cannot create pre-load backup: {error}")
        return False

    if backup_name is None:
        return False

    try:
        for source, destination in copy_operations:
            copy_to_destination(source, destination)

        for path in sorted(remove_operations, key=lambda item: len(item.parts), reverse=True):
            remove_path(path)

    except (OSError, shutil.Error) as error:
        print(Fore.RED + f"Load failed: {error}")
        print(Fore.YELLOW + f"Run 'slots revert' to restore backup '{backup_name}'.")
        return False

    return True

def find_latest_backup(backups_dir):
    latest_backup = None
    latest_time = None

    for backup in backups_dir.iterdir():
        info_path = backup / "info.json"

        if not backup.is_dir() or not info_path.exists():
            continue

        with open(info_path, "r", encoding="utf-8") as file:
            try:
                info = json.load(file)
            except json.JSONDecodeError:
                continue

        try:
            saved_time = datetime.fromisoformat(info["time"])
        except (KeyError, TypeError, ValueError):
            continue

        if latest_time is None or saved_time > latest_time:
            latest_backup = backup
            latest_time = saved_time

    return latest_backup

def read_restore_manifest(path):
    if not path.exists():
        print(Fore.RED + "Cannot revert: restore.json missing.")
        return None

    with open(path, "r", encoding="utf-8") as file:
        try:
            manifest = json.load(file)
        except json.JSONDecodeError:
            print(Fore.RED + "Cannot revert: restore.json is malformed.")
            return None

    if not isinstance(manifest.get("touched"), list):
        print(Fore.RED + "Cannot revert: restore.json missing 'touched' list.")
        return None

    return manifest

def revert_latest(root, base_dir, backups_dir):
    backup = find_latest_backup(backups_dir)

    if backup is None:
        print(Fore.RED + "No load backup found.")
        return False

    layout = read_slot_layout(backup / "layout.json")
    if layout is None:
        return False

    manifest = read_restore_manifest(backup / "restore.json")
    if manifest is None:
        return False

    try:
        with open(base_dir / "layout.json", "r", encoding="utf-8") as file:
            base_layout = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(Fore.RED + f"Cannot revert: base layout unavailable: {error}")
        return False

    backup_paths = set(layout["added"] + layout["modified"])
    removed_before_load = set(layout["removed"])

    try:
        copy_operations = []
        remove_operations = []
        backup_files_dir = backup / "files"
        base_files_dir = base_dir / "files"

        for file_path in manifest["touched"]:
            destination = safe_project_path(root, file_path)

            if file_path in backup_paths:
                source = safe_storage_path(backup_files_dir, file_path)
                copy_operations.append((source, destination))
            elif file_path in removed_before_load or file_path not in base_layout:
                remove_operations.append(destination)
            else:
                source = safe_storage_path(base_files_dir, file_path)
                copy_operations.append((source, destination))

    except ValueError as error:
        print(Fore.RED + str(error))
        return False

    for source, _ in copy_operations:
        if not source.exists():
            print(Fore.RED + f"Cannot revert: backup file missing: {source}")
            return False

    try:
        for source, destination in copy_operations:
            copy_to_destination(source, destination)

        for path in sorted(remove_operations, key=lambda item: len(item.parts), reverse=True):
            if path.exists() and path.is_dir():
                print(Fore.YELLOW + f"Skipping directory: {path}")
                continue

            remove_path(path)

    except OSError as error:
        print(Fore.RED + f"Revert failed: {error}")
        return False

    return True

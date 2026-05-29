from pathlib import Path
import shutil
from colorama import Fore, Back, Style, init
import json
import hashlib
from datetime import datetime, timezone
import re
init(autoreset=True)
#TODO: change config to config.json in .slots

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

def create_layout(path):
    layout = {}

    for item in path.rglob("*"):

        if should_ignore(item, path):    
            continue

        relative = item.relative_to(path)

        layout[str(relative)] = {
            "type": "dir" if item.is_dir() else "file",
            "hash": hash_file(item) if item.is_file() else None
        }

    return layout


def save_current_directory(root, name, base_dir, saves_dir):
    current_layout = create_layout(root)

    with open(base_dir / "layout.json", "r", encoding="utf-8") as base_layout_file:
        base_layout = json.load(base_layout_file)
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
        source = root / file_path
        destination = saved_files_dir / file_path

        if not source.exists():
            continue

        try:
            copy_to_destination(source, destination)

        except PermissionError:
            print(Fore.RED + f"Skipped {source} - Currently in use or no permission.")

def clear_saves(saves_dir):
    for item in saves_dir.iterdir():
        remove_path(item)


def remove_path(path):
    if not path.exists():
        return

    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()

def copy_to_destination(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)

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

def sorted_deepest_first(paths):
    return sorted(paths, key=lambda file_path: len(Path(file_path).parts), reverse=True)

def pluralize(value, unit):
    if value == 1:
        return f"{value} {unit}"

    return f"{value} {unit}s"

def format_time_since(saved_time):
    now = datetime.now(saved_time.tzinfo or timezone.utc)
    seconds_since_save = max(0, round((now - saved_time).total_seconds()))

    if seconds_since_save < 60:
        return f"{pluralize(seconds_since_save, 'second')} ago"

    minutes_since_save = round(seconds_since_save / 60)

    if minutes_since_save < 60:
        return f"{pluralize(minutes_since_save, 'minute')} ago"

    hours = minutes_since_save // 60
    minutes = minutes_since_save % 60

    if minutes == 0:
        return f"{pluralize(hours, 'hour')} ago"

    return f"{pluralize(hours, 'hour')} {pluralize(minutes, 'minute')} ago"

def format_saved_time(saved_time):
    return saved_time.astimezone().strftime("%H:%M")

def load_save(name, saves_dir, base_dir, root):
    base_files_dir = base_dir / "files"

    if not Path.exists(saves_dir / name / "layout.json") or not Path.exists(base_dir / "layout.json"):
        print(Fore.RED + f"Cannot load slot '{name}': layout.json missing.")
        return

    with open(saves_dir / name / "layout.json", "r", encoding="utf-8") as file:
        try:
            save_layout = json.load(file)
        except json.JSONDecodeError:
            print(Fore.RED + f"Cannot load slot: layout.json for base state is malformed.")
            return


    with open(base_dir / "layout.json", "r", encoding="utf-8") as file:
        try:
            base_layout = json.load(file)
        except json.JSONDecodeError:
            print(Fore.RED + f"Cannot load slot: layout.json for slot '{name}' is malformed.")

    target_paths = (set(base_layout) - set(save_layout["removed"])) | set(save_layout["added"]) | set(save_layout["modified"])
    current_paths = set(create_layout(root))

    for file_path in sorted_deepest_first(current_paths - target_paths):
        remove_path(root / file_path)

    for file_path in sorted(base_layout):
        source = base_files_dir / file_path
        destination = root / file_path

        if not source.exists():
            print(Fore.YELLOW + f"Skipped missing base path: {file_path}")
            continue

        copy_to_destination(source, destination)

    for file_path in save_layout["added"] + save_layout["modified"]:
        source = saves_dir / name / "files" / file_path
        destination = root / file_path

        if not source.exists():
            print(Fore.YELLOW + f"Skipped missing saved file: {file_path}")
            continue

        copy_to_destination(source, destination)

    for file_path in sorted_deepest_first(save_layout["removed"]):
        remove_path(root / file_path)



def list_saves(saves_dir):
    saves = []
    for save in saves_dir.iterdir():

        info_path = save / "info.json"

        if not save.is_dir():
            continue

        if not info_path.exists():
            print(Fore.YELLOW + f"Skipping save '{save.name}', missing info.json")
            continue

        with open(info_path, "r", encoding="utf-8") as file:
            try:
                info = json.load(file)
            except json.JSONDecodeError:
                print(Fore.YELLOW + f"Skipping save '{save.name}', malformed info.json")
                continue

        saved_time_value = info.get("time") or info.get("saved_at")

        try:
            saved_time = datetime.fromisoformat(saved_time_value)
        except (TypeError, ValueError):
            print(Fore.YELLOW + f"Skipping save '{save.name}', missing or invalid save time")
            continue

        saves.append({
            "name": info.get("name", save.name),
            "time": saved_time
        })

    saves.sort(
        key=lambda save: save["time"],
        reverse=True
    )

    print(Fore.GREEN + "Save slots: ")
    for save in saves:
        time_since_save = format_time_since(save["time"])
        saved_at = format_saved_time(save["time"])
        print(f"{save['name']} - {time_since_save} (Saved at {saved_at})")


class Slots:
    def __init__(self):
        self.root = Path.cwd()
        self.slots_dir = self.root / slots_dir_name
        self.base_dir = self.slots_dir / "base"
        self.saves_dir = self.slots_dir / "saves"
    
    def init(self, args):
        self.root = Path.cwd()

        if args.refresh:
            print(Fore.YELLOW + "Are you sure you want to refresh the base repository state? (This will clear all save slots.)")
            confirmation = input("[y/n]: ")

            if confirmation.lower().strip() == "y":
                if not Path.exists(self.slots_dir):
                    print(Fore.RED + "Cannot refresh base state: Slots not initialized.")
                    return
                refresh_base(self.root)
                clear_saves(self.saves_dir)
                print(Fore.GREEN + "Refreshed base repository to reflect current state.")
            else:
                print(Fore.WHITE + "Operation canceled.")
            return


        if Path.exists(self.root / slots_dir_name):
            print(Fore.RED + "Slots already initialized.")
            return

        ensure_folders([self.slots_dir, self.base_dir / "files", self.saves_dir])
        create_base(self.root)
        base_layout = create_layout(self.base_dir / "files")

        with open(self.base_dir / "layout.json", "w", encoding="utf-8") as file:
            json.dump(base_layout, file, indent=4, sort_keys=True)
            file.write("\n")

        print(Fore.GREEN + "Initialized Slots.")

    def save(self, args):

        if not Path.exists(self.root / slots_dir_name):
            print(Fore.RED + "Cannot save: Slots not initialized.")
            return
        
        if Path.exists(self.saves_dir / args.name):
            print(Fore.RED + f"Cannot save: Slot with the name '{args.name}' already exists.")
            return
        
        error = validate_slot_name(args.name)
        if error:
            print(Fore.RED + f"Invalid slot name: {error}")
            return

        save_current_directory(self.root, args.name.strip(), self.base_dir, self.saves_dir)

        print(Fore.GREEN + f"Created save slot '{args.name}'.")

    def load(self, args):
        if not Path.exists(self.root / slots_dir_name):
            print(Fore.RED + "Cannot load: Slots not initialized.")
            return
        
        error = validate_slot_name(args.name)
        if error:
            print(Fore.RED + f"Invalid slot name: {error}")
            return
        
        if not Path.exists(self.saves_dir / args.name):
            print(Fore.RED + f"No slot with name '{args.name}' found.")
            return
        

        
        load_save(args.name.strip(), self.saves_dir, self.base_dir, self.root)
        print(Fore.GREEN + f"Loaded save slot '{args.name}'.")

    
    def list(self):
        if not Path.exists(self.root / slots_dir_name):
            print(Fore.RED + "Cannot list: Slots not initialized.")
            return
        
        list_saves(self.saves_dir)
        
    def delete(self, args):
        if not Path.exists(self.root / slots_dir_name):
            print(Fore.RED + "Cannot delete: Slots not initialized.")
            return
        
        error = validate_slot_name(args.name)
        if error:
            print(Fore.RED + f"Invalid slot name: {error}")
            return
        
        if not Path.exists(self.saves_dir / args.name):
            print(Fore.RED + f"No slot with name '{args.name}' found.")
            return
        
        slot_path = self.saves_dir / args.name.strip()

        remove_path(slot_path)
        print(Fore.GREEN + f"Deleted slot '{args.name.strip()}'")

    def reset(self):
        print(Fore.YELLOW + "Are you sure you want to reset all slots configuration?")
        confirmation = input("[y/n]: ")

        if confirmation.lower().strip() != "y":
            return
        
        print(Fore.RED + "This action is irreversible. Please make sure this is what you want to do.")
        confirmation = input("[y/n]: ")

        if confirmation.lower().strip() != "y":
            return
        
        shutil.rmtree(self.slots_dir)
        print(Fore.GREEN + "Cleared all slots data. Use 'slots init' to reinitialize slots.")


        


    

from pathlib import Path
import json
import shutil
from datetime import datetime, timezone

from colorama import Fore, init

from slots.load import load_save, revert_latest
from slots.save import create_base, refresh_base, save_current_directory
from slots.utils import (
    create_layout,
    ensure_folders,
    pluralize,
    remove_path,
    slots_dir_name,
    validate_slot_name,
)

init(autoreset=True)

def clear_saves(saves_dir):
    for item in saves_dir.iterdir():
        remove_path(item)

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
        self.backups_dir = self.slots_dir / "backups"

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

        ensure_folders([self.slots_dir, self.base_dir / "files", self.saves_dir, self.backups_dir])
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

        saved = save_current_directory(self.root, args.name.strip(), self.base_dir, self.saves_dir)

        if saved:
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

        removeFiles = getattr(args, "remove_files", False)
        loaded = load_save(args.name.strip(), self.saves_dir, self.base_dir, self.backups_dir, self.root, removeFiles)

        if loaded:
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

    
    def revert(self):
        if not Path.exists(self.root / slots_dir_name):
            print(Fore.RED + "Cannot revert: Slots not initialized.")
            return
        
        reverted = revert_latest(self.root, self.base_dir, self.backups_dir)

        if reverted:
            print(Fore.GREEN + "Reverted last load.")

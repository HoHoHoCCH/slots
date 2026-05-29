import argparse
from slots.slots import Slots

def main():
    slots = Slots()

    parser = argparse.ArgumentParser(description="Slots - Save slots for coding projects.")

    subparsers = parser.add_subparsers(title="Commands", dest="command")

    init_parser = subparsers.add_parser("init", help="Initialize slots")
    init_parser.add_argument("--refresh", action="store_true", help="Update base to current repository state.")

    save_parser = subparsers.add_parser("save", help="Save current repository.")
    save_parser.add_argument("name")

    reset_parser = subparsers.add_parser("reset", help="Destroys all slot-related files and folders.")

    load_parser = subparsers.add_parser("load", help="Load a save slot.")
    load_parser.add_argument("name")
    load_parser.add_argument("--remove-files", action="store_true", help="Remove files that were deleted in the slot.")

    delete_parser = subparsers.add_parser("delete", help="Delete a save slot.")
    delete_parser.add_argument("name")

    list_parser = subparsers.add_parser("list", help="List save slots.")

    revert_parser = subparsers.add_parser("revert", help="Revert the last load.")

    args = parser.parse_args()

    match args.command:
        case "init":
            slots.init(args)
        
        case "save":
            slots.save(args)
        
        case "reset":
            slots.reset()

        case "load":
            slots.load(args)
        
        case "list":
            slots.list()

        case "delete":
            slots.delete(args)

        case "revert":
            slots.revert()

        case _:
            print("Command not found. Use --help for list of commands.")


if __name__ == "__main__":
    main()


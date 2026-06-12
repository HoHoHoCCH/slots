import json
import subprocess
import sys

from slots.load import load_save

from conftest import args, read, write

def init_project(slots, project):
    write(project / "base_clean.txt", "base clean")
    write(project / "base_local.txt", "base local")
    write(project / "remove_me.txt", "remove me")
    slots.init(args(refresh=False))

def test_init_creates_slots_structure(slots, project):
    write(project / "app.py", "print('hello')")

    slots.init(args(refresh=False))

    assert (project / ".slots" / "base" / "files" / "app.py").exists()
    assert (project / ".slots" / "base" / "layout.json").exists()
    assert (project / ".slots" / "saves").is_dir()
    assert (project / ".slots" / "backups").is_dir()

def test_save_records_added_modified_and_removed(slots, project):
    init_project(slots, project)

    write(project / "base_clean.txt", "slot clean")
    write(project / "added.txt", "slot added")
    (project / "remove_me.txt").unlink()

    slots.save(args(name="slot1"))

    save_dir = project / ".slots" / "saves" / "slot1"
    layout = json.loads((save_dir / "layout.json").read_text(encoding="utf-8"))

    assert "added.txt" in layout["added"]
    assert "base_clean.txt" in layout["modified"]
    assert "remove_me.txt" in layout["removed"]
    assert (save_dir / "files" / "added.txt").exists()
    assert (save_dir / "files" / "base_clean.txt").exists()
    assert not (save_dir / "files" / "remove_me.txt").exists()

def test_list_and_delete_save(slots, project, capsys):
    init_project(slots, project)
    slots.save(args(name="slot1"))

    slots.list()
    assert "slot1" in capsys.readouterr().out

    slots.delete(args(name="slot1"))
    assert not (project / ".slots" / "saves" / "slot1").exists()

def test_status_groups_current_differences_from_base(slots, project, capsys):
    init_project(slots, project)

    write(project / "base_clean.txt", "changed")
    write(project / "added.txt", "new")
    (project / "remove_me.txt").unlink()

    slots.status(args(latest=False))
    output = capsys.readouterr().out

    assert "Difference from base state" in output
    assert "3 changed: 1 added, 1 modified, 1 removed" in output
    assert "Added (1)" in output
    assert "+ added.txt" in output
    assert "Modified (1)" in output
    assert "~ base_clean.txt" in output
    assert "Removed (1)" in output
    assert "- remove_me.txt" in output

def test_status_latest_compares_to_most_recent_save(slots, project, capsys):
    init_project(slots, project)

    write(project / "from_first.txt", "first")
    slots.save(args(name="slot1"))

    write(project / "from_latest.txt", "latest")
    slots.save(args(name="slot2"))

    write(project / "from_latest.txt", "changed after latest")
    write(project / "after_latest.txt", "new after latest")

    slots.status(args(latest=True))
    output = capsys.readouterr().out

    assert "Difference from latest save 'slot2'" in output
    assert "2 changed: 1 added, 1 modified, 0 removed" in output
    assert "+ after_latest.txt" in output
    assert "~ from_latest.txt" in output
    assert "from_first.txt" not in output

def test_load_restores_added_and_modified_files_and_keeps_unrelated(slots, project):
    init_project(slots, project)

    write(project / "base_clean.txt", "slot clean")
    write(project / "added.txt", "slot added")
    slots.save(args(name="slot1"))

    write(project / "base_clean.txt", "local clean")
    (project / "added.txt").unlink()
    write(project / "unrelated.txt", "do not touch")

    slots.load(args(name="slot1", remove_files=False))

    assert read(project / "base_clean.txt") == "slot clean"
    assert read(project / "added.txt") == "slot added"
    assert read(project / "unrelated.txt") == "do not touch"

    backups = list((project / ".slots" / "backups").iterdir())
    assert len(backups) == 1
    assert (backups[0] / "info.json").exists()
    assert (backups[0] / "layout.json").exists()
    assert (backups[0] / "files").is_dir()
    assert (backups[0] / "restore.json").exists()

def test_load_remove_files_removes_removed_files(slots, project):
    init_project(slots, project)

    (project / "remove_me.txt").unlink()
    slots.save(args(name="slot1"))
    write(project / "remove_me.txt", "restore before load")

    slots.load(args(name="slot1", remove_files=True))

    assert not (project / "remove_me.txt").exists()

def test_load_remove_files_refuses_to_remove_directories(slots, project):
    write(project / "folder" / "file.txt", "base")
    slots.init(args(refresh=False))

    (project / "folder" / "file.txt").unlink()
    (project / "folder").rmdir()
    slots.save(args(name="slot1"))
    write(project / "folder" / "file.txt", "current")

    slots.load(args(name="slot1", remove_files=True))

    assert read(project / "folder" / "file.txt") == "current"

def test_load_malformed_layout_does_not_mutate(slots, project):
    init_project(slots, project)

    write(project / "base_clean.txt", "slot clean")
    slots.save(args(name="slot1"))
    write(project / "base_clean.txt", "local clean")
    (project / ".slots" / "saves" / "slot1" / "layout.json").write_text("{bad json", encoding="utf-8")

    slots.load(args(name="slot1", remove_files=False))

    assert read(project / "base_clean.txt") == "local clean"

def test_load_rejects_path_traversal_metadata(slots, project):
    init_project(slots, project)

    save_dir = project / ".slots" / "saves" / "bad"
    (save_dir / "files").mkdir(parents=True)
    (save_dir / "layout.json").write_text(
        json.dumps({"added": ["../escape.txt"], "modified": [], "removed": []}),
        encoding="utf-8",
    )

    loaded = load_save("bad", slots.saves_dir, slots.base_dir, slots.backups_dir, slots.root)

    assert loaded is False
    assert not (project.parent / "escape.txt").exists()

def test_revert_restores_latest_load(slots, project):
    init_project(slots, project)

    write(project / "base_clean.txt", "slot clean")
    write(project / "base_local.txt", "slot local")
    write(project / "added.txt", "slot added")
    slots.save(args(name="slot1"))

    write(project / "base_clean.txt", "base clean")
    write(project / "base_local.txt", "local before load")
    (project / "added.txt").unlink()
    write(project / "unrelated.txt", "untouched")

    slots.load(args(name="slot1", remove_files=False))
    assert read(project / "base_clean.txt") == "slot clean"
    assert read(project / "base_local.txt") == "slot local"
    assert read(project / "added.txt") == "slot added"

    slots.revert()

    assert read(project / "base_clean.txt") == "base clean"
    assert read(project / "base_local.txt") == "local before load"
    assert not (project / "added.txt").exists()
    assert read(project / "unrelated.txt") == "untouched"

def test_revert_refuses_directory_removal(slots, project):
    init_project(slots, project)

    write(project / "added_dir" / "file.txt", "slot")
    slots.save(args(name="slot1"))
    (project / "added_dir" / "file.txt").unlink()
    (project / "added_dir").rmdir()

    slots.load(args(name="slot1", remove_files=False))
    write(project / "added_dir" / "extra.txt", "current")

    slots.revert()

    assert (project / "added_dir" / "extra.txt").exists()

def test_revert_missing_restore_manifest_fails_cleanly(slots, project):
    init_project(slots, project)

    write(project / "base_clean.txt", "slot clean")
    slots.save(args(name="slot1"))
    slots.load(args(name="slot1", remove_files=False))

    backup = next((project / ".slots" / "backups").iterdir())
    (backup / "restore.json").unlink()
    write(project / "base_clean.txt", "after load changed again")

    slots.revert()

    assert read(project / "base_clean.txt") == "after load changed again"

def test_cli_help_lists_commands():
    result = subprocess.run(
        [sys.executable, "-m", "slots", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    for command in ["init", "save", "load", "list", "delete", "revert", "status"]:
        assert command in result.stdout

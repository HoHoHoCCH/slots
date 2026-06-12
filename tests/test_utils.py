import json
from pathlib import Path

import pytest

from slots.utils import (
    atomic_json,
    create_layout,
    remove_file_path,
    safe_project_path,
    safe_storage_path,
    validate_slot_name,
)

def test_validate_slot_name_accepts_simple_names():
    assert validate_slot_name("main") is None
    assert validate_slot_name("slot 1") is None
    assert validate_slot_name("feature_test-2") is None

@pytest.mark.parametrize("name", ["", "   ", ".", "..", "a/b", "a\\b", "CON"])
def test_validate_slot_name_rejects_bad_names(name):
    assert validate_slot_name(name) is not None

def test_safe_project_path_rejects_unsafe_paths(tmp_path):
    assert safe_project_path(tmp_path, "src/file.py") == (tmp_path / "src" / "file.py").resolve()

    unsafe_paths = [
        str(tmp_path / "outside.txt"),
        "../outside.txt",
        ".git/config",
        ".slots/layout.json",
        "",
    ]

    for path in unsafe_paths:
        with pytest.raises(ValueError):
            safe_project_path(tmp_path, path)

def test_safe_storage_path_rejects_escape_paths(tmp_path):
    assert safe_storage_path(tmp_path, "files/a.txt") == (tmp_path / "files" / "a.txt").resolve()

    for path in [str(tmp_path / "a.txt"), "../outside.txt", ""]:
        with pytest.raises(ValueError):
            safe_storage_path(tmp_path, path)

def test_create_layout_ignores_internal_ignored_and_symlink_paths(tmp_path):
    (tmp_path / "keep.txt").write_text("keep", encoding="utf-8")
    (tmp_path / ".slots").mkdir()
    (tmp_path / ".slots" / "state.txt").write_text("ignored", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("ignored", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.js").write_text("ignored", encoding="utf-8")

    symlink_path = tmp_path / "link.txt"
    try:
        symlink_path.symlink_to(tmp_path / "keep.txt")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable in this environment")

    layout = create_layout(tmp_path)

    assert "keep.txt" in layout
    assert ".slots/state.txt" not in layout
    assert ".git/config" not in layout
    assert "node_modules/pkg.js" not in layout
    assert "link.txt" not in layout

def test_remove_file_path_removes_files_and_rejects_directories(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("data", encoding="utf-8")
    remove_file_path(file_path)
    assert not file_path.exists()

    directory = tmp_path / "directory"
    directory.mkdir()

    with pytest.raises(IsADirectoryError):
        remove_file_path(directory)

    assert directory.exists()

def test_atomic_json_writes_and_replaces_json(tmp_path):
    path = tmp_path / "data.json"

    atomic_json(path, {"value": 1})
    assert json.loads(path.read_text(encoding="utf-8")) == {"value": 1}

    atomic_json(path, {"value": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"value": 2}

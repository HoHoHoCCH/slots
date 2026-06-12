from types import SimpleNamespace

import pytest

from slots.slots import Slots

def args(**kwargs):
    return SimpleNamespace(**kwargs)

@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path

@pytest.fixture
def slots(project):
    return Slots()

def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def read(path):
    return path.read_text(encoding="utf-8")

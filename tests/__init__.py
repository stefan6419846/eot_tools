from collections.abc import Generator
from contextlib import contextmanager
from importlib.resources import as_file, files
from pathlib import Path


@contextmanager
def get_file(name: str) -> Generator[Path]:
    reference = files("tests") / "files" / name
    with as_file(reference) as path:
        yield path

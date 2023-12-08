import functools
from pathlib import Path
from typing import Any

import dill


def store_object(obj: Any, path: str | Path) -> None:
    with open(path, "wb") as f:
        dill.dump(obj, f)


@functools.lru_cache(maxsize=10)
def load_object(path: str | Path) -> Any:
    with open(path, "rb") as f:
        return dill.load(f)


def load_objects(*paths: str | Path) -> list[Any]:
    return [load_object(path) for path in paths]


def paths_exists(*paths: Path, ignore: bool = False) -> bool:
    """
    Check wether the model already exists.

    If you want to suppress the error then set `ignore` to `True`. Default to `False`.
    """
    return all(i.exists() for i in paths) and not ignore

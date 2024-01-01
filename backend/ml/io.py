from pathlib import Path
from typing import Any

import dill


def dump_object(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    # Finally store with dill library
    with path.open("wb") as f:
        dill.dump(obj, f)


def load_object(path: Path) -> Any:
    with path.open("rb") as f:
        return dill.load(f)


def load_objects(*paths: Path) -> tuple[Any, ...]:
    return tuple(load_object(path) for path in paths)

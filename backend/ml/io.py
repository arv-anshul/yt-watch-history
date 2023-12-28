from pathlib import Path
from typing import Any

import dill


def dump_object(obj: Any, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Finally store with dill library
    with open(path, "wb") as f:
        dill.dump(obj, f)


def load_object(path: str | Path) -> Any:
    with open(path, "rb") as f:
        return dill.load(f)


def load_objects(*paths: str | Path) -> tuple[Any, ...]:
    return tuple(load_object(path) for path in paths)

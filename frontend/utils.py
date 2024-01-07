from itertools import islice
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Iterator


def batch_iter(iterable: "Iterable", n: int, /) -> "Iterator":
    yield from (list(islice(iterable, i, i + n)) for i in range(0, len(iterable), n))  # type: ignore

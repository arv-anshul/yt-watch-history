from __future__ import annotations

from itertools import islice
from typing import Iterable, Iterator


def batch_iter(iterable: Iterable, n: int, /) -> Iterator:
    """
    Iterator function that batches items from an iterator.

    Args:
        iterator (Iterable): An iterator to be batched.
        n (int): The number of items per batch.

    Yields:
        A list of n items from the iterator, or the remaining items if there are less than n.
    """
    yield from (list(islice(iterable, i, i + n)) for i in range(0, len(iterable), n))  # type: ignore

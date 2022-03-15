from contextlib import contextmanager
from itertools import chain
from typing import Iterable

from pytest import fixture

# WARNING: This test suite is essentially using pytest to check itself, what follows is not for the faint of heart.


class ParallelChecker:
    def __init__(self):
        self.contexts = []

    def clear(self):
        self.contexts.clear()

    @contextmanager
    def context(self, name):
        self.contexts.append(name)
        try:
            yield
        finally:
            self.contexts.append(name)

    def context_groups(self):
        group = set()
        for name in self.contexts:
            if name in group:
                group.remove(name)
            else:
                group.add(name)
            yield frozenset(group)

    def assert_concurrent(self, *groups: Iterable[Iterable[str]]):
        con_iterable = iter(self.context_groups())
        for group in groups:
            expected_group = set(group)
            for con_group in con_iterable:
                if con_group >= expected_group:
                    break
            else:
                assert False, f"{expected_group} not in contexts, found {self.contexts}"

    def assert_not_concurrent(self, *ordered_groups: Iterable[Iterable[str]]):
        all_elements = set(chain.from_iterable(ordered_groups))
        groups_iter = iter(ordered_groups)
        next_group = set(next(groups_iter))
        for group in self.context_groups():
            if len(all_elements & group) > 1:
                assert False, f"{all_elements & group} in parallel, found {self.contexts}"
            next_group -= group
            if not next_group:
                try:
                    next_group = set(next(groups_iter))
                except StopIteration:
                    break


@fixture(scope="session")
def parallel_checker():
    return ParallelChecker()


@fixture(scope="session")
def event_loop():
    from asyncio import get_event_loop
    return get_event_loop()

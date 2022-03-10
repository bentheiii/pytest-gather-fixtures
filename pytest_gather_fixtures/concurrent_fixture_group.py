from __future__ import annotations

from functools import partial
from inspect import isasyncgenfunction, signature, stack
from textwrap import dedent
from traceback import format_exception
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from pytest import fixture
from pytest_asyncio import fixture as asyncio_fixture


def fix_to_generator(fix) -> Callable[..., AsyncGenerator[Any, None]]:
    if isasyncgenfunction(fix):
        return fix

    async def adapter(**kwargs):
        yield await fix(**kwargs)

    return adapter


async def handle_generator_group(generators: Iterable[Tuple[str, AsyncGenerator[Any, None]]], event_loop):
    startup_tasks = []
    for key, gen in generators:
        startup_tasks.append((key, gen, event_loop.create_task(gen.__anext__())))
    ret = SimpleNamespace()
    initialized = []
    errs = []
    for key, gen, task in startup_tasks:
        try:
            setattr(ret, key, await task)
        except Exception as e:
            errs.append(e)
        else:
            initialized.append((key, gen))

    if errs:
        # we need to teardown all successfully raised fixtures
        teardown_errs = []
        teardown_tasks = [(key, event_loop.create_task(gen.__anext__())) for (key, gen) in initialized]
        for key, task in teardown_tasks:
            try:
                await task
            except StopAsyncIteration:
                pass
            except Exception as e:
                teardown_errs.append(e)
            else:
                teardown_errs.append(RuntimeError(f"async fixture {key} should only yield once"))

        if len(errs) == 1 and not teardown_errs:
            raise errs[0]
        exc_string = (
                'multiple exceptions during startup of group:\n'
                + '\n'.join(''.join(format_exception(None, e, e.__traceback__)) for e in errs)
        )
        if teardown_errs:
            exc_string += (
                    '\nin addition to the following exceptions during teardown:\n'
                    + '\n'.join(''.join(format_exception(None, e, e.__traceback__)) for e in teardown_errs)
            )
        raise Exception(exc_string)

    yield ret
    teardown_tasks = [(key, event_loop.create_task(gen.__anext__())) for key, gen in generators]
    errs = []
    for key, task in teardown_tasks:
        try:
            await task
        except StopAsyncIteration:
            pass
        except Exception as e:
            errs.append(e)
        else:
            errs.append(RuntimeError(f"async fixture {key} should only yield once"))
    if errs:
        if len(errs) == 1:
            raise errs[0]
        raise Exception(
            'multiple exceptions during teardown of group:'
            + '\n'.join(''.join(format_exception(None, e, e.__traceback__)) for e in errs)
        )


class ChildFixture:
    def __init__(self, name: str, callback: Callable[..., AsyncGenerator[Any, None]], params: Sequence[str],
                 autouse: bool):
        self.name = name
        self.callback = callback
        self.params = params
        self.autouse = autouse

    @classmethod
    def from_function(cls, func: Callable, kwargs: Dict[str, Any], name: Optional[str]) -> 'ChildFixture':
        name = name or func.__name__
        return cls(name, fix_to_generator(func), tuple(signature(func).parameters.keys()), **kwargs)


class ConcurrentFixtureGroup:
    def __init__(self, name: str, *,
                 autouse: bool = False,
                 scope: Union[str, Callable[..., str]] = 'function',
                 autouse_children: bool = True,
                 parent_fixture_name: Optional[str] = None,
                 fixture_namespace: Optional[Dict[str, Any]] = None,
                 ):
        if fixture_namespace is None:
            fixture_namespace = stack()[1][0].f_globals
        self.__name__ = name
        self.children: List[ChildFixture] = []
        self.namespace = fixture_namespace
        self.parent_fixture_name = parent_fixture_name or '_cfg_' + self.__name__
        self.autouse_children = autouse_children
        self.fixture_params = {
            'scope': scope,
            'autouse': autouse,
        }

        self.all_params = {'request', 'event_loop'}

    def inject(self):
        self.namespace[self.parent_fixture_name] = asyncio_fixture(self._parent_func(), name=self.parent_fixture_name,
                                                                   **self.fixture_params)

    def fixture(self, func=None, autouse=None, name: str = None):
        if func is None:
            return partial(self.fixture, autouse=autouse, name=name)
        child = ChildFixture.from_function(func, dict(
            autouse=autouse if autouse is not None else self.autouse_children,
        ), name=name)
        self.children.append(child)

        self.all_params.update(child.params)
        self.inject()

        ns: Dict[str, Any] = {}
        body = dedent(f"""
                def child({self.parent_fixture_name}):
                    return {self.parent_fixture_name}.{child.name}
                """)
        exec(body, ns)
        if name is not None and name != func.__name__:
            # if the fixture needs a different name, we need to inject the new name into the namespace, same as we did
            # the parent
            self.namespace[name] = fixture(ns['child'])
            return func
        # if the fixture doesn't need a different name, we can just return the fixture, and let the decorator shadow the
        # original name
        return fixture(ns['child'])

    def _parent_func(self):
        async def inner(request, event_loop, **kwargs):
            all_fixtures = frozenset(request.fixturenames)
            generators = []
            for child in self.children:
                if child.autouse or child.name in all_fixtures:
                    args = {p: kwargs[p] for p in child.params}
                    generators.append((child.name, child.callback(**args)))

            async for v in handle_generator_group(generators, event_loop):
                yield v

        body = dedent("""
                    async def parent({all_param_names}):
                        async for v in inner({all_params_keyed}):
                            yield v
                    """).format(
            all_param_names=','.join(self.all_params),
            all_params_keyed=','.join(f'{k}={k}' for k in self.all_params)
        )

        exec_namespace = {'inner': inner}

        exec(body, exec_namespace)

        return exec_namespace['parent']

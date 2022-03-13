from __future__ import annotations

from asyncio import FIRST_COMPLETED, Task, wait
from functools import partial
from inspect import isasyncgenfunction, signature, stack
from itertools import chain
from textwrap import dedent
from traceback import format_exception
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Callable, Container, Dict, List, Optional, Set, Union

from pytest import fixture
from pytest_asyncio import fixture as asyncio_fixture

from pytest_gather_fixtures.topology import Topology


def fix_to_generator(fix) -> Callable[..., AsyncGenerator[Any, None]]:
    if isasyncgenfunction(fix):
        return fix

    async def adapter(**kwargs):
        yield await fix(**kwargs)

    return adapter


class ChildFixture:
    def __init__(self, name: str, callback: Callable[..., AsyncGenerator[Any, None]], params: Set[str],
                 dependencies: List[str], autouse: bool):
        self.name = name
        self.callback = callback
        self.params = params
        self.dependencies = dependencies
        # note that parameters can become dependencies down the line
        self.autouse = autouse

    @classmethod
    def from_function(cls, func: Callable, name: Optional[str],
                      known_dependency_names: Container[str], **kwargs) -> 'ChildFixture':
        name = name or func.__name__
        params = set()
        dependencies = []
        for param in signature(func).parameters.keys():
            if param in known_dependency_names:
                dependencies.append(param)
            else:
                params.add(param)

        return cls(name, fix_to_generator(func), params, dependencies, **kwargs)


class ConcurrentFixtureGroup:
    def __init__(self, name: str, *,
                 autouse: bool = False,
                 scope: Union[str, Callable[..., str]] = 'function',
                 parent_fixture_name: Optional[str] = None,
                 fixture_namespace: Union[Dict[str, Any], int] = 1,
                 autouse_children: bool = True,
                 ):
        if isinstance(fixture_namespace, int):
            fixture_namespace = stack()[fixture_namespace].frame.f_globals

        self.__name__ = name
        self.namespace = fixture_namespace
        self.parent_fixture_name = parent_fixture_name or '_cfg_' + self.__name__
        self.fixture_params = {
            'scope': scope,
            'autouse': autouse,
        }
        self.topology = Topology()
        self.children: Dict[str, ChildFixture] = {}
        self.autouse_children = autouse_children

        self.all_params = {'request', 'event_loop'}

    def inject(self):
        self.namespace[self.parent_fixture_name] = asyncio_fixture(self._parent_func(), name=self.parent_fixture_name,
                                                                   **self.fixture_params)

    def fixture(self, func=None, *, name: Optional[str] = None, autouse: Optional[bool] = None):
        if func is None:
            return partial(self.fixture, autouse=autouse, name=name)
        if name is None:
            name = func.__name__
        if name in self.children:
            raise ValueError(f"fixture {name} already exists")
        if name in ('event_loop', 'request'):
            raise ValueError(f"fixture {name} is reserved")

        if autouse is None:
            autouse = self.autouse_children

        child = ChildFixture.from_function(func, name=name, known_dependency_names=self.topology.keys(),
                                           autouse=autouse)
        self.topology.add_node(name)
        self.children[name] = child

        for dep in child.dependencies:
            # this new chid's dependencies
            self.topology.add_dependency(dep, name)
        for other_child_name, other_child in self.children.items():
            if other_child is child:
                continue
            if name in other_child.params:
                other_child.params.remove(name)
                other_child.dependencies.append(name)
                self.topology.add_dependency(name, other_child_name)

        self.all_params.update(child.params)
        self.all_params.discard(name)
        self.inject()

        ns: Dict[str, Any] = {}
        body = dedent(f"""
                def child({self.parent_fixture_name}):
                    return {self.parent_fixture_name}.{child.name}
                """)
        exec(body, ns)
        if name != func.__name__:
            # if the fixture needs a different name, we need to inject the new name into the namespace, same as we did
            # the parent
            self.namespace[name] = fixture(ns['child'], scope=self.fixture_params['scope'])  # type: ignore[arg-type]
            return func
        # if the fixture doesn't need a different name, we can just return the fixture, and let the decorator shadow the
        # original name
        return fixture(ns['child'], scope=self.fixture_params['scope'])  # type: ignore[arg-type]

    async def _handle_topological_generators(self, event_loop, params: Dict[str, Any], include_only: Set[str]):
        generators: Dict[str, AsyncGenerator[Any, None]] = {}
        ret = SimpleNamespace()

        startup_order = self.topology.execution(include_only)
        startup_tasks: Dict[Task, str] = {}
        pending_startups = set()
        startup_errs = []
        initialized = set()
        while startup_order:
            new_ready = startup_order.submit_ready()
            for name in new_ready:
                child = self.children[name]
                child_params = {p: params[p] for p in chain(child.params, child.dependencies)}
                generator = generators[name] = child.callback(**child_params)
                startup_task = event_loop.create_task(generator.__anext__())
                startup_tasks[startup_task] = name
                pending_startups.add(startup_task)

            (completed, pending_startups) = await wait(pending_startups, return_when=FIRST_COMPLETED)
            for task in completed:
                name = startup_tasks.pop(task)
                try:
                    result = await task
                except Exception as e:
                    startup_errs.append(e)
                    startup_order.cancel_all_unsubmitted()
                else:
                    params[name] = result
                    initialized.add(name)
                    setattr(ret, name, result)
                finally:
                    startup_order.complete(name)

        if startup_errs:
            # we need to teardown all the initialized fixtures
            teardown_order = self.topology.execution(initialized, reverse=True)
            teardown_errs = []
            pending_teardowns = set()
            teardown_tasks: Dict[Task, str] = {}
            while teardown_order:
                new_ready = teardown_order.submit_ready()
                for name in new_ready:
                    generator = generators[name]
                    teardown_task = event_loop.create_task(generator.__anext__())
                    teardown_tasks[teardown_task] = name
                    pending_teardowns.add(teardown_task)

                (completed, pending_teardowns) = await wait(pending_teardowns, return_when=FIRST_COMPLETED)
                for task in completed:
                    name = teardown_tasks.pop(task)
                    try:
                        await task
                    except StopAsyncIteration:
                        pass
                    except Exception as e:
                        teardown_errs.append(e)
                    else:
                        teardown_errs.append(RuntimeError(f"async fixture {name} should only yield once"))
                    finally:
                        teardown_order.complete(name)

            if len(startup_errs) == 1 and not teardown_errs:
                raise startup_errs[0]
            exc_string = (
                    'multiple exceptions during startup of group:\n'
                    + '\n'.join(''.join(format_exception(None, e, e.__traceback__)) for e in startup_errs)
            )
            if teardown_errs:
                exc_string += (
                        '\nin addition to the following exceptions during teardown:\n'
                        + '\n'.join(''.join(format_exception(None, e, e.__traceback__)) for e in teardown_errs)
                )
            raise Exception(exc_string)

        yield ret

        teardown_order = self.topology.execution(include_only, reverse=True)
        teardown_errs = []
        pending_teardowns = set()
        teardown_tasks = {}
        while teardown_order:
            new_ready = teardown_order.submit_ready()
            for name in new_ready:
                generator = generators[name]
                teardown_task = event_loop.create_task(generator.__anext__())
                teardown_tasks[teardown_task] = name
                pending_teardowns.add(teardown_task)

            (completed, pending_teardowns) = await wait(pending_teardowns, return_when=FIRST_COMPLETED)
            for task in completed:
                name = teardown_tasks.pop(task)
                try:
                    await task
                except StopAsyncIteration:
                    pass
                except Exception as e:
                    teardown_errs.append(e)
                else:
                    teardown_errs.append(RuntimeError(f"async fixture {name} should only yield once"))
                finally:
                    teardown_order.complete(name)

        if teardown_errs:
            if len(teardown_errs) == 1:
                raise teardown_errs[0]
            raise Exception(
                'multiple exceptions during teardown of group:'
                + '\n'.join(''.join(format_exception(None, e, e.__traceback__)) for e in teardown_errs)
            )

    def _parent_func(self):
        async def inner(request, event_loop, **kwargs):
            all_fixtures = frozenset(request.fixturenames)
            params = {
                **kwargs,
                'request': request,
                'event_loop': event_loop,
            }

            include_only = {child_name
                            for child_name, child in self.children.items()
                            if (child.autouse or child_name in all_fixtures)}

            async for v in self._handle_topological_generators(event_loop, params, include_only):
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

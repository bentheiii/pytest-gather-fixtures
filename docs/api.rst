API Refernce
===========================

.. module:: concurrent_fixture_group
    :synopsis: a group of fixtures that can be run concurrently

-------------------

.. class:: ConcurrentFixtureGroup(name: str, *, autouse: bool = False, \
        scope: ... = 'function', parent_fixture_name: str | None = None, \
        fixture_namespace: dict[str, typing.Any] | int = 1, \
        autoskip: bool = True)

    A group of fixtures that can be run concurrently. Aggregates "child fixtures" into tasks that are run in parallel.

    :param name: the name of the group
    :param autouse: whether to automatically use this fixture, equivalent to the
        `autouse <https://docs.pytest.org/en/latest/how-to/fixtures.html?#autouse-fixtures-fixtures-you-don-t-have-to-request>`_
        parameter on pytest fixtures
    :param scope: the scope of the fixture group, equivalent to the
        `scope <https://docs.pytest.org/en/latest/how-to/fixtures.html?#scope-sharing-fixtures-across-classes-modules-packages-or-session>`_
        parameter on pytest fixtures
    :param parent_fixture_name: the name of the virtual parent fixture. This name will be injected into the caller's
        global namespace. If unassigned, will choose an underscored name. See
        :ref:`abstract:Namespace Injection` for more information.
    :param fixture_namespace: the namespace to inject into the caller's global namespace. See
        :ref:`abstract:Namespace Injection` for more information. If set to an integer, will use
        the global namespace of a frame in the callstack with that number. Default is to use the caller's global
        namespace.
    :param autoskip: whether to automatically use all child fixtures, see
        :ref:`skipping_fixtures:Skipping Child Fixtures` for more information.

    .. method:: fixture(func, *, name: str|None = None, autoskip: Optional[bool] = None)
                fixture(*, name: str|None = None, autoskip: Optional[bool] = None)

        Register a fixture function to the group. Should be used as a decorator.

        :param func: the fixture function. Must be an async function that either returns a value or yields once.
        :param name: the name of the fixture. If assigned, will inject the new name into the group instance's
            ``fixture_namespace``. If unassigned no injection will take place, the fixture will be returned and replace
            the decorated function.
        :param autoskip: whether to automatically use this fixture whenever the parent is used. Defaults to the group
            instance's ``autoskip``. see :ref:`skipping_fixtures:Skipping Child Fixtures` for more information.
        :return: the decorated function if ``name`` is assigned, otherwise the fixture that should replace the function
            by decorator.

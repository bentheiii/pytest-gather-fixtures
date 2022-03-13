API Refernce
===========================

.. module:: concurrent_fixture_group
    :synopsis: a group of fixtures that can be run concurrently

-------------------

.. class:: ConcurrentFixtureGroup(name: str, *, autouse: bool = False, \
        scope: ... = 'function', parent_fixture_name: str | None = None, \
        fixture_namespace: dict[str, typing.Any] | int = 1, \
        autouse_children: bool = True)

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
    :param autouse_children: whether to automatically use all child fixtures, see
        :ref:`skipping_fixtures:skipping_child_fixtures` for more information.

    .. method:: fixture(func: ..., *, name: str|None = None, autouse: Optional[bool] = None)
                fixture(*, name: str|None = None, autouse: Optional[bool] = None)

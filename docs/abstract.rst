How It Works
=====================

Anyone familiar with pytest's internal workings will know that there is no way to execute fixtures in parallel. Even
pytest-asyncio does nothing more than wrap all the async fixtures in an event loop and acts as though is were a normal
synchronous fixture.

pytest-gather-fixtures overcomes this limitation essentially by cheating. It turns this:

.. code-block:: python

    my_group = ConcurrentFixtureGroup('my_group')

    @my_group.fixture
    async def fixture_1():
        await asyncio.sleep(1)
        return 1

    @my_group.fixture
    async def fixture_2():
        await asyncio.sleep(2)
        return 2

Into this (very simplified):

.. code-block:: python
    :emphasize-lines: 11, 12, 14, 17-18, 21-22

    @pytest_asyncio.fixture
    async def _my_group():
        async def _fixture_1():
            await asyncio.sleep(1)
            return 1

        async def _fixture_2():
            await asyncio.sleep(2)
            return 2

        fixture_1_task = asyncio.create_task(_fixture_1())
        fixture_2_task = asyncio.create_task(_fixture_2())

        return [await fixture_1_task, await fixture_2_task]

    @pytest.fixture
    def fixture_1(_my_group):
        return _my_group[0]

    @pytest.fixture
    def fixture_2(_my_group):
        return _my_group[1]

Namespace Injection
---------------------

pytest-gather-fixtures uses the call stack to inject the hidden parent fixture (the one that actually does the work,
and that the other fixtures use to extract only the fields that matter to them) into the caller's namespace.

.. code-block:: python

    my_group = ConcurrentFixtureGroup('my_group')

    @my_group.fixture
    async def fixture_1():
        await asyncio.sleep(1)
        return 1

    assert _cfg_my_group  # this name has been injected into the caller's namespace

In order to avoid conflicts, users can change the name of the injected fixture by passing a custom name to the
``parent_fixture_name`` parameter.

.. code-block:: python

    _cfg_my_group = "an occupied value that shouldn't be overridden"

    my_group = ConcurrentFixtureGroup('my_group', parent_fixture_name="some_other_name")

    @my_group.fixture
    async def fixture_1():
        await asyncio.sleep(1)
        return 1

    assert some_other_name  # this name has been injected into the caller's namespace
    assert isinstance(_cfg_my_group, str)  # the original name is preserved

External Child Dependencies
----------------------------------

Child fixture can depend on external fixtures, they are loaded as a dependencies of the parent fixture.

.. code-block:: python

    @fixture
    def my_fixture():
        return 10

    my_group = ConcurrentFixtureGroup('my_group')

    @my_group.fixture
    async def fixture_1(monkeypatch):
        await asyncio.sleep(1)
        with monkeypatch.setenv('MY_ENV_VAR', '1'):
            return 1

    @my_group.fixture
    async def fixture_2(my_fixture):
        await asyncio.sleep(2)
        return my_fixture * 10

Internal Child Dependencies
-------------------------------

Child fixtures can depend on other child fixtures, the dependant coroutines are only run when their dependencies are
finished.

.. code-block:: python

    my_group = ConcurrentFixtureGroup('my_group')

    @my_group.fixture
    async def fixture_1():
        await asyncio.sleep(1)
        return 1

    @my_group.fixture
    async def fixture_2():
        await asyncio.sleep(2)
        return 2

    @my_group.fixture
    async def fixture_3(fixture_1):
        await asyncio.sleep(2)
        return fixture_1 * 2

The following group of fixtures will be executed in parallel, but fixture_3 will only be run after fixture_1 has
completed, so the entire group will take 3 seconds to complete.

In these cases, teardown happens in the reverse order. i.e. fixture_1 will only be torn down after fixture_3 has
been torn down.
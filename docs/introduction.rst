Introduction
====================

pytest-gather-fixture is a library that builds on top of pytest-asyncio that allows you to perform asynchronous fuxtures
concurrently. It is designed to be used with independent fixtures that take a long time to set up/teardown.

.. code-block::
    :emphasize-lines: 1, 4, 6, 11

    from pytest_gather_fixture import ConcurrentFixtureGroup

      # we create a group of fixtures that can be executed concurrently
    my_group = ConcurrentFixtureGroup('my_group')

    @my_group.fixture # we register a fixture within the group
    async def my_async_fixture():
        await asyncio.sleep(1)
        return 'async_fixture'

    @my_group.fixture # we register another fixture within the group
    async def my_other_async_fixture():
        await asyncio.sleep(2)
        return 'async_fixture'

    @pytest.mark.asyncio
    async def test_async_fixture(async_fixture, my_other_async_fixture):
        # setup for this test will take only 2 seconds instead of 3
        assert async_fixture == 'async_fixture'
        assert my_other_async_fixture == 'async_fixture'

Note that pytest-gather-fixture is not a pytest plugin, but rather a library that can be used with pytest, and requires
pytest-asyncio.
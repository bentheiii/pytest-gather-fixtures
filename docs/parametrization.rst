Parameterization
========================

While fixture groups or their children cannot be parameterized directly, they can be parameterized indirectly through
real parameterized fixtures.

.. code-block::
    :emphasize-lines: 18

    @pytest.fixture(params=[1, 0.01])
    def sleep_unit(request):
        return request.param

    my_group = ConcurrentFixtureGroup('my_group')

    @my_group.fixture
    async def fixture_1(sleep_unit):
        await asyncio.sleep(1*sleep_unit)
        return 1

    @my_group.fixture
    async def fixture_2(sleep_unit):
        await asyncio.sleep(2*sleep_unit)
        return 2

    def test_1(fixture_1, fixture_2):
        # this test will twice, once with sleep_unit=1 and once with sleep_unit=0.01
        assert fixture_1 == 1
        assert fixture_2 == 2

Spooky Behaviour When Parameterizing Fixture Groups
--------------------------------------------------------

Note that when a child fixture is parameterized, all of its siblings are also parameterized in the same way.

.. code-block::
    :emphasize-lines: 17, 23, 29

    @pytest.fixture(params=[0, 1])
    def base2(request):
        return request.param

    @pytest.fixture(params=[0, 1, 2, 3, 4])
    def base5(request):
        return request.param

    @pytest.fixture(params=[0, 1, 2, 3, 4, 5, 6])
    def base7(request):
        return request.param

    my_group = ConcurrentFixtureGroup('my_group')

    @my_group.fixture
    async def fixture_1(base2):
        # this fixture will be set up 70 times!
        await asyncio.sleep(1)
        return 1

    @my_group.fixture
    async def fixture_2(base5):
        # this fixture will be set up 70 times!
        await asyncio.sleep(2)
        return 2

    @my_group.fixture
    async def fixture_3(base7):
        # this fixture will be set up 70 times!
        await asyncio.sleep(3)
        return 3

    @my_group.fixture
    async def fixture_4():
        # this fixture will be set up 70 times!
        await asyncio.sleep(3)
        return 4

    def test_1(fixture_1, fixture_2, fixture_3, fixture_4):
        # this test will run 70 times!
        assert fixture_1 == 1
        assert fixture_2 == 2
        assert fixture_3 == 3
        assert fixture_4 == 4
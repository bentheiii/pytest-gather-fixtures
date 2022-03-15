Skipping Child Fixtures
===========================================

By default, the sub-fixtures in a fixture group are all-or-nothing: if any fixture is used in a test, all fixtures in
that group will be used. This means that even if a fixture is not used in a test or any other used fixtures, it will be
used in any test that uses any fixture from that group.

.. code-block::
    :emphasize-lines: 14

    my_group = ConcurrentFixtureGroup('my_group')

    some_global_state = set()

    @my_group.fixture
    async def fixture_1():
        some_global_state.add('fixture_1')

    @my_group.fixture
    async def fixture_2():
        some_global_state.add('fixture_2')

    def test_all_or_nothing(fixture_1):
        # fixture_2 is included in this test because its sibling fixture_1 is used.
        assert some_global_state == {'fixture_1', 'fixture_2'}

This behaviour can be changed by setting the group's ``autoskip_children`` to ``True``.

.. code-block::
    :emphasize-lines: 1

    my_group = ConcurrentFixtureGroup('my_group', autoskip_children=True)

    some_global_state = set()

    @my_group.fixture
    async def fixture_1():
        some_global_state.add('fixture_1')

    @my_group.fixture
    async def fixture_2():
        some_global_state.add('fixture_2')

    def test_all_or_nothing(fixture_1):
        assert some_global_state == {'fixture_1'}

Alternatively, you can set the ``autoskip`` of the child fixtures to ``True``.

.. code-block::
    :emphasize-lines: 9

    my_group = ConcurrentFixtureGroup('my_group')

    some_global_state = set()

    @my_group.fixture
    async def fixture_1():
        some_global_state.add('fixture_1')

    @my_group.fixture(autoskip=True)
    async def fixture_2():
        some_global_state.add('fixture_2')

    def test_all_or_nothing(fixture_1):
        assert some_global_state == {'fixture_1'}

This behaviour is disabled by default, to avoid some spooky behaviour.

Spooky Behaviour With Skipping Child Fixtures
----------------------------------------------------

Note that if a child fixture is skipped, all the fixtures that that fixture uses will **not be** skipped.

.. code-block::
    :emphasize-lines: 18

    my_group = ConcurrentFixtureGroup('my_group')

    some_global_state = set()

    @fixture
    def some_fixture():
        some_global_state.add('some_fixture')

    @my_group.fixture
    async def fixture_1():
        some_global_state.add('fixture_1')

    @my_group.fixture(autoskip=False)
    async def fixture_2(some_fixture):
        some_global_state.add('fixture_2')

    def test_all_or_nothing(fixture_1):
        # fixture_2 was skipped, but it's dependant- some_fixture, was not skipped.
        assert some_global_state == {'some_fixture', 'fixture_1'}
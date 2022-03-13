from asyncio import sleep

from pytest import fixture

from pytest_gather_fixtures import ConcurrentFixtureGroup


@fixture
def fx():
    return []


@fixture
def set_fx(fx):
    fx.append(True)


Foo = ConcurrentFixtureGroup('Foo', autouse_children=False)


@Foo.fixture
async def s1(parallel_checker):
    with parallel_checker.context('1_start'):
        await sleep(0.1)
    return 1


@Foo.fixture
async def s2(parallel_checker):
    with parallel_checker.context('2_start'):
        await sleep(0.2)
    return 2


@Foo.fixture
async def s3(parallel_checker, set_fx):
    # this fixture will be skipped, but its dependant will not be skipped
    with parallel_checker.context('3_start'):
        await sleep(0.1)
    yield 3
    with parallel_checker.context('3_tear'):
        await sleep(0.1)


@Foo.fixture
async def s4(parallel_checker):
    with parallel_checker.context('4_start'):
        await sleep(0.2)
    yield 4
    with parallel_checker.context('4_tear'):
        await sleep(0.2)


def test_skip_keep_dependants(teardown_parallel_check, s1, s2, s4, parallel_checker, fx):
    assert s1 == 1
    assert s2 == 2
    assert s4 == 4
    parallel_checker.assert_concurrent(
        ['1_start', '2_start', '4_start'],
    )
    assert '3_start' not in parallel_checker.contexts
    assert fx == [True]


@fixture(scope='module')
def teardown_parallel_check(parallel_checker):
    yield
    parallel_checker.assert_concurrent(
        ['1_start', '2_start', '4_start'],
        ['4_tear'],
    )
    parallel_checker.clear()

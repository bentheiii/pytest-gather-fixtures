from asyncio import sleep

from pytest import fixture

from pytest_gather_fixtures import ConcurrentFixtureGroup

Foo = ConcurrentFixtureGroup('Foo', autoskip=True)


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
async def s3(parallel_checker):
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


def test_skip_one(teardown_parallel_check, s1, s2, s4, parallel_checker, ):
    assert s1 == 1
    assert s2 == 2
    assert s4 == 4
    parallel_checker.assert_concurrent(
        ['1_start', '2_start', '4_start'],
    )
    assert '3_start' not in parallel_checker.contexts


def test_skip_two(teardown_parallel_check, s1, s2, s3, parallel_checker, ):
    assert s1 == 1
    assert s2 == 2
    assert s3 == 3
    parallel_checker.assert_concurrent(
        ['1_start', '2_start', '4_start'],
        ['4_tear'],
        ['1_start', '2_start', '3_start'],
    )


@fixture(scope='module')
def teardown_parallel_check(parallel_checker):
    yield
    parallel_checker.assert_concurrent(
        ['1_start', '2_start', '4_start'],
        ['4_tear'],
        ['1_start', '2_start', '3_start'],
        ['3_tear'],
    )
    parallel_checker.assert_not_concurrent(['4_start', '3_start'])
    parallel_checker.clear()

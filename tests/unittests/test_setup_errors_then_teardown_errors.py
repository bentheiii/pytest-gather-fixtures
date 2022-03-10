from asyncio import sleep

from pytest import fixture, mark

from pytest_gather_fixtures import ConcurrentFixtureGroup

Foo = ConcurrentFixtureGroup('Foo')


@Foo.fixture
async def s1(parallel_checker):
    with parallel_checker.context('1_start'):
        await sleep(0.1)
    return 1


@Foo.fixture
async def s2(parallel_checker):
    with parallel_checker.context('2_start'):
        await sleep(0.1)
        raise Exception('2_start')
    return 2


@Foo.fixture
async def s3(parallel_checker):
    with parallel_checker.context('3_start'):
        await sleep(0.1)
        raise Exception('3_start')
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
        raise Exception('4_tear')


@mark.xfail(strict=True)
def test_setup_errors_then_teardown_errs(teardown_parallel_check, s1, s2, s3, s4):
    # this test will never actually run because its startup failed
    pass


@fixture()
def teardown_parallel_check(parallel_checker):
    yield
    parallel_checker.assert_concurrent(
        ['1_start', '2_start', '3_start', '4_start'],
        ['4_tear']
    )
    parallel_checker.clear()

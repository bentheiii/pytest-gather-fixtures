from asyncio import sleep

from pytest import fixture

from pytest_gather_fixtures import ConcurrentFixtureGroup


@fixture(params=[0, 1])
def b2(request):
    return request.param


@fixture(params=[0, 1, 2])
def b3(request):
    return request.param


Foo = ConcurrentFixtureGroup('Foo')


@Foo.fixture
async def s1(parallel_checker, b2):
    with parallel_checker.context('1_start'):
        await sleep(0.1)
    return 1 + b2


@Foo.fixture
async def s2(parallel_checker, b3):
    with parallel_checker.context('2_start'):
        await sleep(0.2)
    return 2 + b3


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


def test_simple(teardown_parallel_check, s1, s2, s3, s4, parallel_checker, b2, b3):
    assert s1 == 1 + b2
    assert s2 == 2 + b3
    assert s3 == 3
    assert s4 == 4


@fixture(scope='module')
def teardown_parallel_check(parallel_checker):
    yield
    parallel_checker.assert_concurrent(
        ['1_start', '2_start', '3_start', '4_start'],
        ['3_tear', '4_tear'],
        ['1_start', '2_start', '3_start', '4_start'],
        ['3_tear', '4_tear'],
        ['1_start', '2_start', '3_start', '4_start'],
        ['3_tear', '4_tear'],
        ['1_start', '2_start', '3_start', '4_start'],
        ['3_tear', '4_tear'],
        ['1_start', '2_start', '3_start', '4_start'],
        ['3_tear', '4_tear'],
        ['1_start', '2_start', '3_start', '4_start'],
        ['3_tear', '4_tear'],
    )
    parallel_checker.clear()

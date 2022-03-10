from asyncio import sleep
from inspect import iscoroutinefunction

from pytest import fixture

from pytest_gather_fixtures import ConcurrentFixtureGroup

Foo = ConcurrentFixtureGroup('Foo')


@Foo.fixture(name='sone')
async def s1(parallel_checker):
    with parallel_checker.context('1_start'):
        await sleep(0.1)
    return 1


@Foo.fixture(name='stwo')
async def s2(parallel_checker):
    with parallel_checker.context('2_start'):
        await sleep(0.2)
    return 2


@Foo.fixture(name='sthree')
async def s3(parallel_checker):
    with parallel_checker.context('3_start'):
        await sleep(0.1)
    yield 3
    with parallel_checker.context('3_tear'):
        await sleep(0.1)


@Foo.fixture(name='sfour')
async def s4(parallel_checker):
    with parallel_checker.context('4_start'):
        await sleep(0.2)
    yield 4
    with parallel_checker.context('4_tear'):
        await sleep(0.2)


def test_alias_children(teardown_parallel_check, sone, stwo, sthree, sfour, parallel_checker, ):
    assert iscoroutinefunction(s1)

    assert sone == 1
    assert stwo == 2
    assert sthree == 3
    assert sfour == 4
    parallel_checker.assert_concurrent(
        ['1_start', '2_start', '3_start', '4_start'],
    )


@fixture()
def teardown_parallel_check(parallel_checker):
    yield
    parallel_checker.assert_concurrent(
        ['1_start', '2_start', '3_start', '4_start'],
        ['3_tear', '4_tear']
    )
    parallel_checker.clear()

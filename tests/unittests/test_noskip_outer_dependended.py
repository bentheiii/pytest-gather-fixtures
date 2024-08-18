from asyncio import sleep

from pytest import fixture

from pytest_gather_fixtures import ConcurrentFixtureGroup

Foo = ConcurrentFixtureGroup("Foo", autoskip=False)


@Foo.fixture
async def s1(parallel_checker):
    with parallel_checker.context("1_start"):
        await sleep(0.1)
    return 1


@Foo.fixture
async def s2(parallel_checker):
    with parallel_checker.context("2_start"):
        await sleep(0.2)
    return 2


@Foo.fixture
async def s3(parallel_checker):
    with parallel_checker.context("3_start"):
        await sleep(0.1)
    yield 3
    with parallel_checker.context("3_tear"):
        await sleep(0.1)


@Foo.fixture
async def s4(parallel_checker):
    with parallel_checker.context("4_start"):
        await sleep(0.2)
    yield 4
    with parallel_checker.context("4_tear"):
        await sleep(0.2)


@fixture
def bar(s4):
    return s4**2


def test_skip_keeps_dependants(
    s1,
    s2,
    s3,
    bar,
    parallel_checker,
):
    assert s1 == 1
    assert s2 == 2
    assert s3 == 3
    assert bar == 16
    parallel_checker.assert_concurrent(
        ["1_start", "2_start", "3_start", "4_start"],
    )

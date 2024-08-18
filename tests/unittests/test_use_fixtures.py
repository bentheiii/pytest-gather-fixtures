from asyncio import sleep

from pytest import fixture

from pytest_gather_fixtures import ConcurrentFixtureGroup

Foo = ConcurrentFixtureGroup("Foo")


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
def s_1_2(s1, s2):
    return f"{s1} + {s2} = {s1 + s2}"


@fixture
async def s_3_1(s3, s1):
    return f"{s3} + {s1} = {s3 + s1}"


def test_use_fixtures(
    teardown_parallel_check,
    s_1_2,
    s_3_1,
    parallel_checker,
):
    assert s_1_2 == "1 + 2 = 3"
    assert s_3_1 == "3 + 1 = 4"
    parallel_checker.assert_concurrent(
        ["1_start", "2_start", "3_start", "4_start"],
    )


@fixture
def teardown_parallel_check(parallel_checker):
    yield
    parallel_checker.assert_concurrent(["1_start", "2_start", "3_start", "4_start"], ["3_tear", "4_tear"])
    parallel_checker.clear()

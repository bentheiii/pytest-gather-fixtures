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
async def s2_1(parallel_checker):
    with parallel_checker.context("2_1_start"):
        await sleep(0.01)
    yield 1
    with parallel_checker.context("2_1_tear"):
        await sleep(0.01)


@Foo.fixture
async def s2_3(parallel_checker, s2_2):
    with parallel_checker.context("2_3_start"):
        await sleep(0.01)
    yield s2_2 * 10 + 3
    with parallel_checker.context("2_3_tear"):
        await sleep(0.01)


@Foo.fixture
async def s2_2(parallel_checker, s2_1):
    with parallel_checker.context("2_2_start"):
        await sleep(0.01)
    yield s2_1 * 10 + 2
    with parallel_checker.context("2_2_tear"):
        await sleep(0.01)


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


def test_interdependant(
    teardown_parallel_check,
    s1,
    s2_1,
    s2_2,
    s2_3,
    s3,
    s4,
    parallel_checker,
):
    assert s1 == 1
    assert s2_1 == 1
    assert s2_2 == 12
    assert s2_3 == 123
    assert s3 == 3
    assert s4 == 4
    parallel_checker.assert_concurrent(
        ["1_start", "2_1_start", "3_start", "4_start"],
        ["1_start", "2_2_start", "3_start", "4_start"],
        ["1_start", "2_3_start", "3_start", "4_start"],
    )


@fixture
def teardown_parallel_check(parallel_checker):
    yield
    parallel_checker.assert_concurrent(
        ["1_start", "2_1_start", "3_start", "4_start"],
        ["1_start", "2_2_start", "3_start", "4_start"],
        ["1_start", "2_3_start", "3_start", "4_start"],
        ["2_3_tear", "3_tear", "4_tear"],
        ["2_2_tear", "3_tear", "4_tear"],
        ["2_1_tear", "3_tear", "4_tear"],
    )
    parallel_checker.assert_not_concurrent(
        [
            "2_1_start",
            "2_2_start",
            "2_3_start",
            "2_3_tear",
            "2_2_tear",
            "2_1_tear",
        ]
    )
    parallel_checker.clear()

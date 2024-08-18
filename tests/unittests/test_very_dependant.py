from asyncio import sleep

from pytest import fixture

from pytest_gather_fixtures import ConcurrentFixtureGroup

Foo = ConcurrentFixtureGroup("Foo")

r"""
S1  S2  S3
 |   \  /
 |    S4
 \   /  \
   S5   S6
"""


@Foo.fixture
async def s1(parallel_checker):
    with parallel_checker.context("1_start"):
        await sleep(0.1)
    return 1


@Foo.fixture
async def s2(parallel_checker):
    with parallel_checker.context("2_start"):
        await sleep(0.1)
    return 2


@Foo.fixture
async def s3(parallel_checker):
    with parallel_checker.context("3_start"):
        await sleep(0.1)
    return 3


@Foo.fixture
async def s4(parallel_checker, s2, s3):
    with parallel_checker.context("4_start"):
        await sleep(0.1)
    return s2 + s3 - 1


@Foo.fixture
async def s5(parallel_checker, s1, s4):
    with parallel_checker.context("5_start"):
        await sleep(0.1)
    return s1 + s4


@Foo.fixture
async def s6(parallel_checker, s4):
    with parallel_checker.context("6_start"):
        await sleep(0.1)
    return s4 * 1.5


def test_interdependant(
    teardown_parallel_check,
    s1,
    s2,
    s3,
    s4,
    s5,
    s6,
    parallel_checker,
):
    assert s1 == 1
    assert s2 == 2
    assert s3 == 3
    assert s4 == 4
    assert s5 == 5
    assert s6 == 6
    parallel_checker.assert_concurrent(
        [
            "1_start",
            "2_start",
            "3_start",
        ],
        [
            "5_start",
            "6_start",
        ],
    )


@fixture
def teardown_parallel_check(parallel_checker):
    yield
    parallel_checker.assert_not_concurrent(
        [
            "2_start",
        ],
        ["4_start"],
        [
            "5_start",
        ],
    )
    parallel_checker.assert_not_concurrent(
        [
            "1_start",
        ],
        [
            "5_start",
        ],
    )
    parallel_checker.clear()

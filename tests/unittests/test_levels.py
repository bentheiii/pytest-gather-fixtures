from asyncio import sleep

from pytest import fixture

from pytest_gather_fixtures import ConcurrentFixtureGroup

Foo = ConcurrentFixtureGroup("Foo", scope="module")


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
async def s3(parallel_checker, teardown_second_parallel_check):
    # we add the teardown fixture to make sure that the teardown is run in the correct order
    with parallel_checker.context("3_start"):
        await sleep(0.1)
    yield 3
    with parallel_checker.context("3_tear"):
        await sleep(0.1)


@Foo.fixture
async def s4(parallel_checker, teardown_second_parallel_check):
    # we add the teardown fixture to make sure that the teardown is run in the correct order
    with parallel_checker.context("4_start"):
        await sleep(0.2)
    yield 4
    with parallel_checker.context("4_tear"):
        await sleep(0.2)


Bar = ConcurrentFixtureGroup("Bar")


@Bar.fixture
async def b1(parallel_checker):
    with parallel_checker.context("b1_start"):
        await sleep(0.1)
    return 1


@Bar.fixture
async def b2(parallel_checker):
    with parallel_checker.context("b2_start"):
        await sleep(0.1)
    yield 2
    with parallel_checker.context("b2_tear"):
        await sleep(0.1)


@fixture(scope="module")
def check_1_run():
    # this is just a marker to check that test1 is run, since test2 depends on it
    return []


def test_first(teardown_first_parallel_check, s1, s2, s3, s4, b1, b2, parallel_checker, check_1_run):
    check_1_run.append(True)
    assert s1 == 1
    assert s2 == 2
    assert s3 == 3
    assert s4 == 4
    assert b1 == 1
    assert b2 == 2
    parallel_checker.assert_concurrent(
        ["1_start", "2_start", "3_start", "4_start"],
        ["b1_start", "b2_start"],
    )


@fixture
def teardown_first_parallel_check(parallel_checker):
    yield
    parallel_checker.assert_concurrent(
        ["1_start", "2_start", "3_start", "4_start"],
        ["b1_start", "b2_start"],
        ["b2_tear"],
    )


def test_second(
    s1,
    s2,
    s3,
    s4,
    b1,
    b2,
    parallel_checker,
    check_1_run,
    teardown_second_parallel_check,
):
    assert check_1_run == [True]
    assert s1 == 1
    assert s2 == 2
    assert s3 == 3
    assert s4 == 4
    assert b1 == 1
    assert b2 == 2
    parallel_checker.assert_concurrent(
        ["1_start", "2_start", "3_start", "4_start"],
        ["b1_start", "b2_start"],
        ["b2_tear"],
        ["b1_start", "b2_start"],
    )


@fixture(scope="module")
def teardown_second_parallel_check(parallel_checker):
    yield
    parallel_checker.assert_concurrent(
        ["1_start", "2_start", "3_start", "4_start"],
        ["b1_start", "b2_start"],
        ["b2_tear"],
        ["b1_start", "b2_start"],
        ["b2_tear"],
        ["3_tear", "4_tear"],
    )
    parallel_checker.clear()

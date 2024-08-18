from asyncio import sleep

from pytest import mark

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
        await sleep(0.1)
    yield 2
    with parallel_checker.context("2_tear"):
        await sleep(0.1)


@Foo.fixture
async def s3(parallel_checker):
    with parallel_checker.context("3_start"):
        await sleep(0.1)
    yield 3
    with parallel_checker.context("3_tear"):
        await sleep(0.1)
        raise Exception("3_tear")


@Foo.fixture
async def s4(parallel_checker):
    with parallel_checker.context("4_start"):
        await sleep(0.2)
    yield 4
    with parallel_checker.context("4_tear"):
        await sleep(0.2)
        raise Exception("4_tear")


@mark.xfail()
def test_teardown_errs(s1, s2, s3, s4):
    # we have no way to actually tell pytest "this test should pass, but the the teardown should fail", so this will
    # have to do
    assert s1 == 1
    assert s2 == 2
    assert s3 == 3
    assert s4 == 4

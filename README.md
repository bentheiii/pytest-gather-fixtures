# Pytest-Gather-Fixtures:  run async fixtures concurrently

[Documentation](https://pytest-gather-fixtures.readthedocs.io/en/latest/)

pytest-gather-fixtures is a library for pytest that allows you to set up and tear down fixtures in 
parallel. It's useful for when you have multiple independent fixtures that take a long time to set
up. 

```python
import asyncio
from pytest_gather_fixtures import ConcurrentFixtureGroup

my_fixture_group = ConcurrentFixtureGroup('my_fixture_group')

@my_fixture_group.fixture
async def my_fixture_1():
    await asyncio.sleep(1)

@my_fixture_group.fixture
async def my_fixture_2():
    await asyncio.sleep(1)

def test_foo(my_fixture_1, my_fixture_2):
    # setup for this test will only take 1 second
    pass
```

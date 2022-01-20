import time
from dataclasses import dataclass
from datalite3 import datalite, Primary


@datalite("test.db", auto_commit=True)
@dataclass
class TestClass2:
    id: Primary[int]
    value: int


obj = TestClass2(1, 20)


# time.sleep(4)
#
#
# obj.value = 40

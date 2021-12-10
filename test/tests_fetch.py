import unittest
from sqlite3 import Connection

from dataclasses import dataclass, asdict

from datalite3 import datalite
from datalite3.fetch import fetch_from, fetch_equals, fetch_all, fetch_if, fetch_where

# Show full diff in unittest
unittest.util._MAX_LENGTH = 2000

db: Connection = Connection(":memory:")


@datalite(db)
@dataclass
class FetchClass:
    ordinal: int
    str_: str

    def __eq__(self, other):
        return asdict(self) == asdict(other)


class DatabaseFetchCalls(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.objs = [FetchClass(1, 'a'), FetchClass(2, 'b'), FetchClass(3, 'b')]
        [obj.create_entry() for obj in cls.objs]

    def testFetchFrom(self):
        t_obj = fetch_from(FetchClass, self.objs[0].__id__)
        self.assertEqual(self.objs[0], t_obj)

    def testFetchEquals(self):
        t_obj = fetch_equals(FetchClass, 'str_', self.objs[0].str_)
        self.assertEqual(self.objs[0], t_obj)

    def testFetchAll(self):
        t_objs = fetch_all(FetchClass)
        self.assertEqual(tuple(self.objs), t_objs)

    def testFetchIf(self):
        t_objs = fetch_if(FetchClass, "str_ = \"b\"")
        self.assertEqual(tuple(self.objs[1:]), t_objs)

    def testFetchWhere(self):
        t_objs = fetch_where(FetchClass, 'str_', 'b')
        self.assertEqual(tuple(self.objs[1:]), t_objs)


if __name__ == '__main__':
    unittest.main()

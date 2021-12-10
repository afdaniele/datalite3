import unittest
from dataclasses import dataclass, asdict
from math import floor
from sqlite3 import Connection

from datalite3 import datalite
from datalite3.fetch import fetch_all, fetch_if, fetch_where

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


class DatabaseFetchPaginationCalls(unittest.TestCase):

    def setUp(self) -> None:
        self.objs = [FetchClass(i, f'{floor(i/10)}') for i in range(30)]
        [obj.create_entry() for obj in self.objs]

    def testFetchAllPagination(self):
        t_objs = fetch_all(FetchClass, 1, 10)
        self.assertEqual(tuple(self.objs[:10]), t_objs)

    def testFetchWherePagination(self):
        t_objs = fetch_where(FetchClass, 'str_', '0', 2, 5)
        self.assertEqual(tuple(self.objs[5:10]), t_objs)

    def testFetchIfPagination(self):
        t_objs = fetch_if(FetchClass, 'str_ = "0"', 1, 5)
        self.assertEqual(tuple(self.objs[:5]), t_objs)

    def tearDown(self) -> None:
        [obj.remove_entry() for obj in self.objs]


if __name__ == '__main__':
    unittest.main()

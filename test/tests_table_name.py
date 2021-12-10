import unittest
from sqlite3 import Connection

from dataclasses import dataclass

from datalite3 import datalite
from datalite3.fetch import fetch_from, fetch_equals, fetch_all, fetch_if, fetch_where

# Show full diff in unittest
unittest.util._MAX_LENGTH = 2000

db: Connection = Connection(":memory:")


# TODO: this is where we test custom table names


@datalite(db, 'NiceNameClass')
@dataclass
class UglyNameClass:
    int_: int
    str_: str


@datalite(db)
@dataclass
class NiceNameClass:
    int_: int
    str_: str


class DatabaseCustomTableName(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.objs = [UglyNameClass(1, 'a'), UglyNameClass(2, 'b'), UglyNameClass(3, 'b')]
        [obj.create_entry() for obj in cls.objs]
        for obj in cls.objs:
            obj.__class__ = NiceNameClass

    def testFetchFrom(self):
        t_obj = fetch_from(NiceNameClass, self.objs[0].__id__)
        self.assertEqual(self.objs[0], t_obj)

    def testFetchEquals(self):
        t_obj = fetch_equals(NiceNameClass, 'str_', self.objs[0].str_)
        self.assertEqual(self.objs[0], t_obj)

    def testFetchAll(self):
        t_objs = fetch_all(NiceNameClass)
        self.assertEqual(tuple(self.objs), t_objs)

    def testFetchIf(self):
        t_objs = fetch_if(NiceNameClass, "str_ = \"b\"")
        self.assertEqual(tuple(self.objs[1:]), t_objs)

    def testFetchWhere(self):
        t_objs = fetch_where(NiceNameClass, 'str_', 'b')
        self.assertEqual(tuple(self.objs[1:]), t_objs)


if __name__ == '__main__':
    unittest.main()

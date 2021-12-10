import unittest
from dataclasses import dataclass
from sqlite3 import Connection

from datalite3 import datalite
from datalite3.constraints import Unique
from datalite3.fetch import fetch_all
from datalite3.migrations import basic_migrate, _drop_table

# Show full diff in unittest
unittest.util._MAX_LENGTH = 2000

db: Connection = Connection(":memory:")


@datalite(db)
@dataclass
class Migrate1:
    ordinal: int
    conventional: str


@datalite(db)
@dataclass
class Migrate2:
    cardinal: Unique[int] = 1
    str_: str = "default"


class DatabaseMigration(unittest.TestCase):

    def setUp(self) -> None:
        self.objs = [Migrate1(i, "a") for i in range(10)]
        [obj.create_entry() for obj in self.objs]

    def testBasicMigrate(self):
        global Migrate1
        Migrate1 = Migrate2
        Migrate1.table_name = 'migrate1'
        basic_migrate(Migrate1, {'ordinal': 'cardinal'})
        t_objs = fetch_all(Migrate1)
        self.assertEqual([obj.ordinal for obj in self.objs], [obj.cardinal for obj in t_objs])
        self.assertEqual(["default" for _ in range(10)], [obj.str_ for obj in t_objs])

    def tearDown(self) -> None:
        t_objs = fetch_all(Migrate1)
        [obj.remove_entry() for obj in t_objs]
        _drop_table(Migrate1, 'migrate1')


if __name__ == '__main__':
    unittest.main()

import unittest
from dataclasses import dataclass, asdict
from sqlite3 import Connection

from datalite import datalite
from datalite.commons import connect
from datalite.fetch import fetch_from, fetch_equals, fetch_all, fetch_if, fetch_where, fetch_range

# Show full diff in unittest
from datalite.mass_actions import create_many, copy_many

unittest.util._MAX_LENGTH = 2000

db: Connection = Connection(":memory:")


@datalite(db)
@dataclass
class MassCommit:
    str_: str


class DatabaseMassInsert(unittest.TestCase):

    def setUp(self) -> None:
        self.objs = [MassCommit(f'cat   {i}') for i in range(30)]

    def testMassCreate(self):
        with connect(MassCommit) as con:
            cur = con.cursor()
            cur.execute(f'CREATE TABLE IF NOT EXISTS MASSCOMMIT (__id__, str_)')

        start_tup = fetch_all(MassCommit)
        create_many(self.objs, protect_memory=False)
        _objs = fetch_all(MassCommit)
        self.assertEqual(_objs, start_tup + tuple(self.objs))

    def testMassCopy(self):
        setattr(MassCommit, 'db_path', 'other.db')
        start_tup = fetch_all(MassCommit)
        copy_many(self.objs, 'other.db', False)
        tup = fetch_all(MassCommit)
        self.assertEqual(tup, start_tup + tuple(self.objs))

    def tearDown(self) -> None:
        [obj.remove_entry() for obj in self.objs]


if __name__ == '__main__':
    unittest.main()

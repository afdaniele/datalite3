import sqlite3
import unittest
from sqlite3 import Connection

from dataclasses import dataclass

from datalite3 import datalite
from datalite3.constraints import Primary
from datalite3.decorator import remove_all
from datalite3.fetch import fetch_all
from datalite3.mass_actions import create_many

# Show full diff in unittest
unittest.util._MAX_LENGTH = 2000

db: Connection = sqlite3.connect(":memory:")


@datalite(db)
@dataclass
class MassCommit:
    str_: Primary[str]


class DatabaseMassInsert(unittest.TestCase):

    def setUp(self) -> None:
        self.objs = [MassCommit(f'cat {i}') for i in range(3)]

    def testMassCreate(self):
        # create some initial objects
        start_len = 2
        [MassCommit(f'dog {i}').create_entry() for i in range(start_len)]
        start_tup = fetch_all(MassCommit)
        self.assertEqual(len(start_tup), start_len)
        # copy some more objects
        create_many(self.objs)
        _objs = fetch_all(MassCommit)
        self.assertEqual(_objs, start_tup + tuple(self.objs))

    def tearDown(self) -> None:
        remove_all(MassCommit)


if __name__ == '__main__':
    unittest.main()

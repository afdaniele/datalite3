import os
import unittest
from dataclasses import dataclass

from datalite import datalite
from datalite.constraints import Primary
from datalite.fetch import fetch_all
# Show full diff in unittest
from datalite.mass_actions import create_many

unittest.util._MAX_LENGTH = 2000

db: str = "mass_commit.db"


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

    # def testMassCopy(self):
    #     setattr(MassCommit, 'db_path', 'other.db')
    #     start_tup = fetch_all(MassCommit)
    #     copy_many(self.objs, 'other.db', False)
    #     tup = fetch_all(MassCommit)
    #     self.assertEqual(tup, start_tup + tuple(self.objs))

    def tearDown(self) -> None:
        os.remove(db)


if __name__ == '__main__':
    unittest.main()

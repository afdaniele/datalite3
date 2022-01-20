import unittest
from sqlite3 import Connection

from dataclasses import dataclass, asdict

from datalite3 import datalite
from test.commons import getValFromDB

# Show full diff in unittest
unittest.util._MAX_LENGTH = 2000

db: Connection = Connection(":memory:")


@datalite(db)
@dataclass
class TestClass:
    value: int = 1

    def __eq__(self, other):
        return asdict(self) == asdict(other)


@datalite(db, auto_commit=True)
@dataclass
class TestAutoCommitClass:
    value: int = 1

    def __eq__(self, other):
        return asdict(self) == asdict(other)


class DatabaseAutoCommit(unittest.TestCase):

    def test_creation_no_autocommit(self):
        TestClass()
        self.assertRaises(ValueError, getValFromDB, TestClass, 1)

    def test_creation_autocommit(self):
        local = TestAutoCommitClass()
        remote = getValFromDB(TestAutoCommitClass, local.__id__)
        self.assertEqual(local, remote)

    def test_update_no_autocommit(self):
        local = TestClass()
        local.create_entry()
        local.value = 40
        remote = getValFromDB(TestClass, local.__id__)
        self.assertNotEqual(local, remote)

    def test_update_autocommit(self):
        local = TestAutoCommitClass()
        local.value = 40
        remote = getValFromDB(TestAutoCommitClass, local.__id__)
        self.assertEqual(local, remote)


if __name__ == '__main__':
    unittest.main()

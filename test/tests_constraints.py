import unittest
from sqlite3 import Connection

from dataclasses import dataclass

from datalite3 import datalite
from datalite3.constraints import ConstraintFailedError, Primary, Unique

# Show full diff in unittest

unittest.util._MAX_LENGTH = 2000

db: Connection = Connection(":memory:")


# Unique = dataclasses.field(metadata={'attributes': ['UNIQUE']})


@datalite(db)
@dataclass
class ConstraintedClass:
    unique_str: Unique[str]


class DatabaseUniqueConstraints(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = ConstraintedClass("This string is supposed to be unique.")
        self.obj.create_entry()

    def testUniqueness(self):
        def createNew():
            obj = ConstraintedClass("This string is supposed to be unique.")
            obj.create_entry()

        self.assertRaises(ConstraintFailedError, createNew)

    def testNullness(self):
        self.assertRaises(ConstraintFailedError, lambda: ConstraintedClass(None).create_entry())

    def tearDown(self) -> None:
        self.obj.remove_entry()


@datalite(db)
@dataclass
class CustomKeyClass:
    id: Primary[int]
    value: Primary[str]
    text: str


class DatabasePrimaryConstraints(unittest.TestCase):

    def setUp(self) -> None:
        self.obj = CustomKeyClass(1, "key", "This is a free form text.")
        self.obj.create_entry()

    def testUniqueness(self):
        def createNew():
            obj = CustomKeyClass(1, "key", "This is another free form text.")
            obj.create_entry()

        self.assertRaises(ConstraintFailedError, createNew)

    def testNullness(self):
        self.assertRaises(
            ConstraintFailedError,
            lambda: CustomKeyClass(1, "key", "txt").create_entry()
        )

    def tearDown(self) -> None:
        self.obj.remove_entry()


if __name__ == '__main__':
    unittest.main()

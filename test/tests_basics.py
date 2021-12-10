import unittest
from sqlite3 import Connection

from dataclasses import dataclass, asdict

from datalite3 import datalite
# Show full diff in unittest
from test.commons import getValFromDB

unittest.util._MAX_LENGTH = 2000

db: Connection = Connection(":memory:")


@datalite(db)
@dataclass
class TestClass:
    integer_value: int = 1
    byte_value: bytes = b'a'
    float_value: float = 0.4
    str_value: str = 'a'

    def __eq__(self, other):
        return asdict(self) == asdict(other)


class DatabaseMain(unittest.TestCase):

    def setUp(self) -> None:
        self.test_object = TestClass(12, b'bytes', 0.4, 'TestValue')

    def test_creation(self):
        self.test_object.create_entry()
        self.assertEqual(self.test_object, getValFromDB(TestClass, 1))

    def test_update(self):
        self.test_object.create_entry()
        self.test_object.integer_value = 40
        self.test_object.update_entry()
        from_db = getValFromDB(TestClass, self.test_object.__id__)
        self.assertEqual(self.test_object.integer_value, from_db.integer_value)

    def test_delete(self):
        cur = db.cursor()
        cur.execute('SELECT * FROM testclass')
        objects = cur.fetchall()
        init_len = len(objects)
        self.test_object.create_entry()
        self.test_object.remove_entry()

        cur = db.cursor()
        cur.execute('SELECT * FROM testclass')
        objects = cur.fetchall()
        self.assertEqual(len(objects), init_len)


if __name__ == '__main__':
    unittest.main()

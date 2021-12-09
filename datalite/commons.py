import copy
import sqlite3 as sql
from contextlib import contextmanager
from enum import Enum
from inspect import isclass
from sqlite3 import Connection
from typing import Any, Dict, List, Tuple, Optional, Union, Type

import dataclasses

from .constraints import Unique, Primary

PythonType = type
PrimitiveType = Union[type(None), int, float, str, bytes]
Key = Union[PrimitiveType, Tuple[PrimitiveType]]
DecoratedClass = Type[dataclasses.dataclass]


class SQLType(Enum):
    NULL = "NULL"
    INTEGER = "INTEGER"
    REAL = "REAL"
    TEXT = "TEXT"
    BLOB = "BLOB"

    def __str__(self):
        return self.value


@dataclasses.dataclass
class SQLField:
    name: str
    py_type: PythonType
    sql_type: SQLType
    attributes: str = ""

    @staticmethod
    def from_dataclass_field(f: dataclasses.Field,
                             type_overload: Optional['TypesTable'] = None) -> 'SQLField':
        table = type_overload or type_table
        return SQLField(
            f.name,
            f.type,
            table[f.type]
        )


TypesTable = Dict[PythonType, SQLType]

primitive_types: TypesTable = {
    type(None): SQLType.NULL,
    int: SQLType.INTEGER,
    float: SQLType.REAL,
    str: SQLType.TEXT,
    bytes: SQLType.BLOB
}

type_table: TypesTable = copy.copy(primitive_types)
unique_types: TypesTable = {
    Unique[key]: f"{value} NOT NULL UNIQUE" for key, value in primitive_types.items()
}
primary_types: TypesTable = {
    Primary[key]: f"{value} NOT NULL" for key, value in primitive_types.items()
}
type_table.update(unique_types)
type_table.update(primary_types)


def _convert_type(type_: PythonType, type_overload: TypesTable) -> SQLType:
    """
    Given a Python type, return the str name of its
    SQLlite equivalent.
    :param type_: A Python type, or None.
    :param type_overload: A type table to overload the custom type table.
    :return: The str name of the sql type.
    >>> _convert_type(int)
    "INTEGER"
    """
    try:
        return type_overload[type_]
    except KeyError:
        raise TypeError("Requested type not in the default or overloaded type table.")


def _convert_sql_format(value: Any) -> str:
    """
    Given a Python value, convert to string representation
    of the equivalent SQL datatype.
    :param value: A value, ie: a literal, a variable etc.
    :return: The string representation of the SQL equivalent.
    >>> _convert_sql_format(1)
    "1"
    >>> _convert_sql_format("John Smith")
    '"John Smith"'
    """
    if value is None:
        return "NULL"
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bytes):
        return '"' + str(value).replace("b'", "")[:-1] + '"'
    else:
        return str(value)


def _get_table_cols(cur: sql.Cursor, table_name: str) -> List[str]:
    """
    Get the column data of a table.

    :param cur: Cursor in database.
    :param table_name: Name of the table.
    :return: the information about columns.
    """
    cur.execute(f"PRAGMA table_info({table_name});")
    return [row_info[1] for row_info in cur.fetchall()]


def _get_default(default_object: object, type_overload: TypesTable) -> str:
    """
    Check if the field's default object is filled,
    if filled return the string to be put in the,
    database.
    :param default_object: The default field of the field.
    :param type_overload: Type overload table.
    :return: The string to be put on the table statement,
    empty string if no string is necessary.
    """
    if type(default_object) in type_overload:
        return f' DEFAULT {_convert_sql_format(default_object)}'
    return ""


def _get_table_name(obj_or_class: Union[type, object]) -> str:
    class_: type = obj_or_class if isclass(obj_or_class) else type(obj_or_class)
    _assert_is_decorated(class_)
    class_: DecoratedClass = class_
    return class_.table_name


# noinspection PyDefaultArgument
def _get_primary_key(class_: type,
                     type_overload: TypesTable = type_table) -> List[SQLField]:
    class_: DecoratedClass = class_
    fields: List[dataclasses.Field] = list(dataclasses.fields(class_))
    fields = list(filter(lambda f: f.type in primary_types, fields))
    typed_fields = list(map(lambda f: SQLField(f.name, f.type, type_overload[f.type]), fields))
    return typed_fields or [SQLField("__id__", int, type_overload[int])]


def _get_key_condition(class_: type, key: Key) -> str:
    key = _validate_key(class_, key)
    key_value = [
        f"{k.name}={_convert_sql_format(v)}"
        for k, v in zip(_get_primary_key(class_, type_table), key)
    ]
    return " AND ".join(key_value)


def _get_instance_key_condition(self) -> str:
    class_: type = type(self)
    _assert_is_decorated(class_)
    key_fields = _get_primary_key(class_)
    key_values = tuple([getattr(self, f.name) for f in key_fields])
    return _get_key_condition(class_, key_values)


# noinspection PyDefaultArgument
def _get_fields(class_: type,
                type_overload: TypesTable = type_table) -> List[SQLField]:
    _assert_is_decorated(class_)
    class_: DecoratedClass = class_
    fields: List[dataclasses.Field] = list(dataclasses.fields(class_))
    fields: List[SQLField] = [
        SQLField.from_dataclass_field(f, type_overload) for f in fields
    ]
    return fields


@contextmanager
def connect(class_: type):
    _assert_is_decorated(class_)
    class_: DecoratedClass = class_

    # TODO: use a lock here to modify the class
    close: bool = False
    if class_.connection is None and isinstance(class_.db, str):
        class_.connection = Connection(class_.db)
        close = True

    try:
        yield class_.connection
    finally:
        if close:
            class_.connection.close()
            class_.connection = None


def _assert_is_decorated(class_: Union[type, type]):
    try:
        getattr(class_, '__datalite_decorated__')
    except AttributeError:
        raise TypeError(f"Given class <{class_.__name__}> is not decorated with datalite.")


# noinspection PyDefaultArgument
def _validate_key(class_: type,
                  key: Key,
                  type_overload: TypesTable = type_table) -> Key:
    # get description of primary key for the class
    primary_key = _get_primary_key(class_, type_overload)
    # make sure the key is a tuple
    if not isinstance(key, tuple):
        if len(primary_key) == 1:
            key = (key,)
        else:
            raise ValueError(f"Key must be of type <tuple>, "
                             f"received <{type(key).__name__}> instead.")
    # make sure the key size is correct
    if len(key) != len(primary_key):
        raise ValueError(f"Class <{class_.__name__}> has a key {len(primary_key)} fields long, "
                         f"a key of {len(key)} fields was given instead.")
    # make sure the field types are correct
    for i in range(len(primary_key)):
        value = key[i]
        if type(value) not in primitive_types:
            raise ValueError(f"Key must contain only primitive types. Value of type "
                             f"<{type(value).__name__}> found in position {i}.")
    # ---
    return key


# noinspection PyDefaultArgument
def _create_table(class_: type,
                  cursor: sql.Cursor,
                  type_overload: TypesTable = type_table) -> None:
    """
    Create the table for a specific dataclass given
    :param class_: A dataclass.
    :param cursor: Current cursor instance.
    :param type_overload: Overload the Python -> SQLDatatype table
    with a custom table, this is that custom table.
    :return: None.
    """
    _assert_is_decorated(class_)
    class_: DecoratedClass = class_
    # table name
    table_name: str = _get_table_name(class_)
    # get fields
    fields: List[dataclasses.Field] = list(dataclasses.fields(class_))
    # declared fields
    fields: Dict[str, str] = {
        field.name: f"{field.name} {_convert_type(field.type, type_overload)}"
                    f"{_get_default(field.default, type_overload)}" for field in fields
    }
    # add primary key fields
    primary_fields: List[SQLField] = _get_primary_key(class_, type_overload)
    default_key = len(primary_fields) == 1 and primary_fields[0].name == "__id__"
    if default_key:
        # default key
        fields["__id__"] = f"__id__ INTEGER PRIMARY KEY AUTOINCREMENT"
    # join fields
    sql_fields = ', '.join(fields.values())
    primary_fields: List[str] = list(map(lambda f: f.name, primary_fields))
    sql_primary_fields: str = ', '.join(primary_fields)
    if not default_key:
        sql_fields = sql_fields + f", PRIMARY KEY ({sql_primary_fields})"
    sql_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({sql_fields});"
    # TODO: remove
    # print(sql_query)

    cursor.execute(sql_query)

import copy

import dataclasses
import sqlite3 as sql
from enum import Enum
from typing import Any, Optional, Dict, List, Type, Tuple

from .constraints import Unique, Primary

DecoratedClass = Type[dataclasses.dataclass]
PythonType = Optional[type]
Key = Tuple[Any]


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
    def from_dataclass_field(f: dataclasses.Field) -> 'SQLField':
        return SQLField(
            f.name,
            f.type,
            type_table[f.type]
        )


primitive_types: Dict[PythonType, SQLType] = {
    type(None): SQLType.NULL,
    int: SQLType.INTEGER,
    float: SQLType.REAL,
    str: SQLType.TEXT,
    bytes: SQLType.BLOB
}

type_table: Dict[PythonType, SQLType] = copy.copy(primitive_types)
type_table.update({
    Unique[key]: f"{value} NOT NULL UNIQUE" for key, value in type_table.items()
})
type_table.update({
    Primary[key]: value for key, value in type_table.items()
})


def _convert_type(type_: PythonType, type_overload: Dict[PythonType, SQLType]) -> SQLType:
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
    return [row_info[1] for row_info in cur.fetchall()][1:]


def _get_default(default_object: object, type_overload: Dict[PythonType, SQLType]) -> str:
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


# noinspection PyDefaultArgument
def _get_primary_key(class_: DecoratedClass,
                     type_overload: Dict[PythonType, SQLType] = type_table) -> List[SQLField]:
    fields: List[dataclasses.Field] = list(dataclasses.fields(class_))
    fields = list(filter(lambda f: f.type.__class__ is Primary, fields))
    typed_fields = list(map(lambda f: SQLField(f.name, f.type, type_overload[f.type]), fields))
    return typed_fields or [SQLField("__id__", int, type_overload[int])]


def _get_key_condition(class_: DecoratedClass, key: Key):
    _validate_key(class_, key)
    key_value = [
        f"{k.name}={_convert_sql_format(v)}"
        for k, v in zip(_get_primary_key(class_, type_table), key)
    ]
    return " AND ".join(key_value)


# noinspection PyDefaultArgument
def _get_fields(class_: DecoratedClass,
                type_overload: Dict[PythonType, SQLType] = type_table) -> List[SQLField]:
    fields: List[dataclasses.Field] = list(dataclasses.fields(class_))
    fields: List[SQLField] = [
        SQLField.from_dataclass_field(f) for f in fields
    ]
    # add primary key fields
    primary_fields: List[SQLField] = _get_primary_key(class_, type_overload)
    default_key = len(primary_fields) == 1 and primary_fields[0].name == "__id__"
    if default_key:
        # default key
        fields.append(SQLField("__id__", int, SQLType.INTEGER))
    return fields


# noinspection PyDefaultArgument
def _validate_key(class_: DecoratedClass,
                  key: Key,
                  type_overload: Dict[PythonType, SQLType] = type_table):
    # make sure the key is a tuple
    if not isinstance(key, tuple):
        raise ValueError(f"Key must be of type <tuple>, received <{type(key).__name__}> instead.")
    # make sure the key size is correct
    primary_key = _get_primary_key(class_, type_overload)
    if len(key) != len(primary_key):
        raise ValueError(f"Class <{class_.__name__}> has a key {len(primary_key)} fields long, "
                         f"a key of {len(key)} fields was given instead.")
    # make sure the field types are correct
    for i in range(len(primary_key)):
        value = key[i]
        if type(value) not in primitive_types:
            raise ValueError(f"Key must contain only primitive types. Value of type "
                             f"<{type(value).__name__}> found in position {i}.")


# noinspection PyDefaultArgument
def _create_table(class_: DecoratedClass,
                  cursor: sql.Cursor,
                  type_overload: Dict[PythonType, SQLType] = type_table) -> None:
    """
    Create the table for a specific dataclass given
    :param class_: A dataclass.
    :param cursor: Current cursor instance.
    :param type_overload: Overload the Python -> SQLDatatype table
    with a custom table, this is that custom table.
    :return: None.
    """
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
    sql_query = f"CREATE TABLE IF NOT EXISTS {class_.__name__.lower()} ({sql_fields});"
    # TODO: remove
    print(sql_query)
    cursor.execute(sql_query)

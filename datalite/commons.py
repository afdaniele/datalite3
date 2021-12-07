import dataclasses
import sqlite3 as sql
from enum import Enum
from typing import Any, Optional, Dict, List, Type

from .constraints import Unique, Primary

DecoratedClass = Type[dataclasses.dataclass]
PythonType = Optional[type]


class SQLType(Enum):
    NULL: str = "NULL"
    INTEGER: str = "INTEGER"
    REAL: str = "REAL"
    TEXT: str = "TEXT"
    BLOB: str = "BLOB"


@dataclasses.dataclass
class SQLField:
    name: str
    py_type: PythonType
    sql_type: SQLType
    properties: str = ""


@dataclasses.dataclass
def PrimaryKey:
    fields: List[SQLField]


type_table: Dict[PythonType, SQLType] = {
    None: SQLType.NULL,
    int: SQLType.INTEGER,
    float: SQLType.REAL,
    str: SQLType.TEXT,
    bytes: SQLType.BLOB
}
type_table.update({
    Unique[key]: f"{value} NOT NULL UNIQUE" for key, value in type_table.items()
})
type_table.update({
    Primary[key]: f"{value}" for key, value in type_table.items()
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


def _get_primary_key(class_: DecoratedClass,
                     type_overload: Dict[PythonType, SQLType]) -> List[SQLField]:
    fields: List[dataclasses.Field] = list(dataclasses.fields(class_))
    fields = list(filter(lambda f: f.type.__class__ is Primary, fields))
    typed_fields = list(map(lambda f: SQLField(f.name, f.type, type_overload[f.type]), fields))
    return typed_fields or [SQLField("_id", int, type_overload[int], "AUTOINCREMENT")]


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
    fields.sort(key=lambda f: f.name)  # Since dictionaries *may* be unsorted.
    # declared fields
    fields: Dict[str, str] = {
        field.name: f"{field.name} {_convert_type(field.type, type_overload)}"
                    f"{_get_default(field.default, type_overload)}" for field in fields
    }
    # add primary key fields
    primary_fields: List[SQLField] = _get_primary_key(class_, type_overload)
    for field in primary_fields:
        if field.name not in fields:
            fields[field.name] = f"{field.name} {_convert_type(field.py_type, type_overload)} " \
                                 f"{field.properties}"
    # join fields
    sql_fields = ', '.join(fields)
    # sql_fields = "obj_id INTEGER PRIMARY KEY AUTOINCREMENT, " + sql_fields
    primary_fields: List[str] = list(map(lambda f: f.name, primary_fields))
    sql_primary_fields: str = ', '.join(primary_fields)
    sql_fields = sql_fields + f", PRIMARY KEY ({sql_primary_fields})"
    sql = f"CREATE TABLE IF NOT EXISTS {class_.__name__.lower()} ({sql_fields});"
    print(sql)
    cursor.execute(sql)

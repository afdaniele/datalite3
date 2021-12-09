"""
This module includes functions to insert multiple records
to a bound database at one time, with one time open and closing
of the database file.
"""
import sqlite3 as sql
from dataclasses import asdict
from typing import TypeVar, Union, List, Tuple

from .commons import _convert_sql_format, _create_table, _get_table_name, connect, _get_fields
from .constraints import ConstraintFailedError

T = TypeVar('T')


class HeterogeneousCollectionError(Exception):
    """
    :raise : if the passed collection is not homogeneous.
        ie: If a List or Tuple has elements of multiple
        types.
    """
    pass


def _check_homogeneity(objects: Union[List[T], Tuple[T]]) -> None:
    """
    Check if all of the members a Tuple or a List
    is of the same type.

    :param objects: Tuple or list to check.
    :return: If all of the members of the same type.
    """
    first = objects[0]
    class_ = first.__class__
    if not all([isinstance(obj, class_) or isinstance(first, obj.__class__) for obj in objects]):
        raise HeterogeneousCollectionError("Tuple or List is not homogeneous.")


# def _toggle_memory_protection(cur: sql.Cursor, protect_memory: bool) -> None:
#     """
#     Given a cursor to an sqlite3 connection, if memory protection is false,
#         toggle memory protections off.
#
#     :param cur: Cursor to an open SQLite3 connection.
#     :param protect_memory: Whether or not should memory be protected.
#     :return: Memory protections off.
#     """
#     if not protect_memory:
#         warn("Memory protections are turned off, "
#              "if operations are interrupted, file may get corrupt.", RuntimeWarning)
#         cur.execute("PRAGMA synchronous = OFF")
#         cur.execute("PRAGMA journal_mode = MEMORY")


def _mass_insert(objects: Union[List[T], Tuple[T]]) -> None:
    """
    Insert multiple records into an SQLite3 database.

    :param objects: Objects to insert.
    :param protect_memory: Whether or not memory
        protections are on or off.
    :return: None
    """
    _check_homogeneity(objects)
    class_ = type(objects[0])
    sql_values = []
    table_name = _get_table_name(class_)
    field_names = list(map(lambda f: f.name, _get_fields(class_)))

    for i, obj in enumerate(objects):
        values: dict = asdict(obj)
        values: str = ', '.join(_convert_sql_format(values[k]) for k in field_names)
        sql_values.append(f"({values})")

    columns: str = ', '.join(field_names)
    values_list: str = ', '.join(sql_values)
    sql_insert = f"INSERT INTO {table_name}({columns}) VALUES {values_list};"

    with connect(class_) as con:
        cur: sql.Cursor = con.cursor()
        try:
            cur.executescript(sql_insert)
        except sql.IntegrityError:
            raise ConstraintFailedError
        con.commit()


def create_many(objects: Union[List[T], Tuple[T]]) -> None:
    """
    Insert many records corresponding to objects
    in a tuple or a list.

    :param objects: A tuple or a list of objects decorated
        with datalite.
    :return: None.
    """
    if objects:
        _mass_insert(objects)
    else:
        raise ValueError("Collection is empty.")


def copy_many(objects: Union[List[T], Tuple[T]], db_name: str,
              protect_memory: bool = True) -> None:
    """
    Copy many records to another database, from
    their original database to new database, do
    not delete old records.

    :param objects: Objects to copy.
    :param db_name: Name of the new database.
    :param protect_memory: Wheter to protect memory during operation,
        Setting this to False will quicken the operation, but if the
        operation is cut short, database file will corrupt.
    :return: None
    """
    if objects:
        with sql.connect(db_name) as con:
            cur = con.cursor()
            _create_table(objects[0].__class__, cur)
            con.commit()
        _mass_insert(objects, db_name, protect_memory)
    else:
        raise ValueError("Collection is empty.")

"""
Defines the Datalite decorator that can be used to convert a dataclass to
a class bound to a sqlite3 database.
"""
import sqlite3 as sql
from sqlite3 import IntegrityError, Connection
from typing import Optional, List, Union, Type, TypeVar

from dataclasses import asdict, make_dataclass

from .commons import _convert_sql_format, _get_key_condition, _create_table, type_table, Key, \
    _get_primary_key, SQLField, TypesTable, DecoratedClass, _get_fields, \
    connect, _get_table_name, _assert_is_decorated
from .constraints import ConstraintFailedError

T = TypeVar("T")


def _get_key(self) -> Key:
    return tuple([
        getattr(self, k.name) for k in _get_primary_key(type(self))
    ])


def _create_entry(self) -> None:
    """
    Given an object, create the entry for the object. As a side-effect,
    this will set the object_id attribute of the object to the unique
    id of the entry.
    :param self: Instance of the object.
    :return: None.
    """
    # get class
    class_: DecoratedClass = type(self)
    # ---
    table_name: str = _get_table_name(self)
    field_names = list(map(lambda f: f.name, _get_fields(class_)))
    field_values = [getattr(self, f) for f in field_names]

    cols = ', '.join(field_names)
    values = ', '.join(map(_convert_sql_format, field_values))

    with connect(class_) as conn:
        cur: sql.Cursor = conn.cursor()
        try:
            cur.execute(f"INSERT INTO {table_name}({cols}) VALUES ({values});")
            # TODO: fix this
            self.__setattr__("__id__", cur.lastrowid)
            conn.commit()
        except IntegrityError:
            raise ConstraintFailedError("A constraint has failed.")


def _update_entry(self) -> None:
    """
    Given an object, update the objects entry in the bound database.
    :param self: The object.
    :return: None.
    """
    # get class
    class_: DecoratedClass = type(self)
    # ---

    with connect(class_) as conn:
        cur: sql.Cursor = conn.cursor()
        table_name: str = _get_table_name(self)
        kv_pairs = [item for item in asdict(self).items()]
        kv_pairs.sort(key=lambda item: item[0])
        kv = ', '.join(item[0] + ' = ' + _convert_sql_format(item[1]) for item in kv_pairs)
        this = _get_key_condition(type(self), _get_key(self))
        query = f"UPDATE {table_name} SET {kv} WHERE {this};"
        cur.execute(query)
        conn.commit()


def remove_all(class_: DecoratedClass):
    _assert_is_decorated(class_)
    table_name: str = _get_table_name(class_)
    # connect
    with connect(class_) as conn:
        cur: sql.Cursor = conn.cursor()
        cur.execute(f"DELETE FROM {table_name} WHERE 1")
        conn.commit()


def remove_from(class_: DecoratedClass, key: Key):
    _assert_is_decorated(class_)
    this = _get_key_condition(class_, key)
    table_name: str = _get_table_name(class_)
    # connect
    with connect(class_) as conn:
        cur: sql.Cursor = conn.cursor()
        cur.execute(f"DELETE FROM {table_name} WHERE {this}")
        conn.commit()


def _remove_entry(self) -> None:
    """
    Remove the object's record in the underlying database.
    :param self: self instance.
    :return: None.
    """
    remove_from(type(self), _get_key(self))


def decorate(dataclass_: DecoratedClass, db: Union[str, Connection],
             table_name: Optional[str] = None, *,
             type_overload: Optional[TypesTable] = None) -> Type[T]:
    """Bind a dataclass to a sqlite3 database. This adds new methods to the class, such as
    `create_entry()`, `remove_entry()` and `update_entry()`.

    :param dataclass_: Dataclass to decorate.
    :param db: Path of the database to be binded.
    :param table_name: Optional name for the table. The name of the class will be used by default.
    :param type_overload: Type overload dictionary.
    :return: The new dataclass.
    """
    # update type table
    types_table = type_table.copy()
    if type_overload is not None:
        types_table.update(type_overload)
    # add primary key fields if not present
    primary_fields: List[SQLField] = _get_primary_key(dataclass_, types_table)
    default_key = len(primary_fields) == 1 and primary_fields[0].name == "__id__"
    if default_key:
        # noinspection PyTypeChecker
        dataclass_ = make_dataclass(
            dataclass_.__name__,
            fields=[('__id__', int, None)],
            bases=(dataclass_,)
        )
    # make table name
    table_name_: str = table_name or dataclass_.__name__.lower()
    # add the path of the database to the class
    setattr(dataclass_, 'db', None if isinstance(db, Connection) else db)
    # add a connection object to the class
    setattr(dataclass_, 'connection', None if isinstance(db, str) else db)
    # add the type table for migration.
    setattr(dataclass_, 'types_table', types_table)
    # add table name
    setattr(dataclass_, 'table_name', table_name_)
    # mark class as decorated
    setattr(dataclass_, '__datalite_decorated__', True)
    # create table
    with connect(dataclass_) as conn:
        cur: sql.Cursor = conn.cursor()
        _create_table(dataclass_, cur, type_overload=types_table)
    # add methods to the class
    dataclass_.create_entry = _create_entry
    dataclass_.remove_entry = _remove_entry
    dataclass_.update_entry = _update_entry
    # ---
    return dataclass_


# NOTE: The return type is not correct but it keeps type hinting in PyCharm alive
def datalite(db: Union[str, Connection], table_name: Optional[str] = None, *,
             type_overload: Optional[TypesTable] = None) -> Type[T]:
    """Bind a dataclass to a sqlite3 database. This adds new methods to the class, such as
    `create_entry()`, `remove_entry()` and `update_entry()`.

    :param db: Path of the database to be binded.
    :param table_name: Optional name for the table. The name of the class will be used by default.
    :param type_overload: Type overload dictionary.
    :return: The new dataclass.
    """

    def _wrap(dataclass_: Type[T]) -> Type[T]:
        return decorate(dataclass_, db, table_name, type_overload=type_overload)

    return _wrap

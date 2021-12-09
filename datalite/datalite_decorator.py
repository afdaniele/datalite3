"""
Defines the Datalite decorator that can be used to convert a dataclass to
a class bound to a sqlite3 database.
"""
import sqlite3 as sql
from dataclasses import asdict, make_dataclass
from sqlite3 import IntegrityError, Connection
from typing import Optional, Callable, List, Union

from .commons import _convert_sql_format, _get_key_condition, _create_table, type_table, Key, \
    _get_primary_key, SQLField, TypesTable, DecoratedClass, _get_fields, \
    connect, _get_table_name
from .constraints import ConstraintFailedError


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
        table_name: str = self.__class__.__name__.lower()
        kv_pairs = [item for item in asdict(self).items()]
        kv_pairs.sort(key=lambda item: item[0])
        kv = ', '.join(item[0] + ' = ' + _convert_sql_format(item[1]) for item in kv_pairs)
        this = _get_key_condition(type(self), _get_key(self))
        query = f"UPDATE {table_name} SET {kv} WHERE {this};"
        cur.execute(query)
        conn.commit()


def remove_from(class_: type, key: Key):
    this = _get_key_condition(class_, key)
    # connect
    with connect(class_) as conn:
        cur: sql.Cursor = conn.cursor()
        cur.execute(f"DELETE FROM {class_.__name__.lower()} WHERE {this}")
        conn.commit()


def _remove_entry(self) -> None:
    """
    Remove the object's record in the underlying database.
    :param self: self instance.
    :return: None.
    """
    remove_from(type(self), _get_key(self))


def datalite(db: Union[str, Connection], type_overload: Optional[TypesTable] = None) -> Callable:
    """Bind a dataclass to a sqlite3 database. This adds new methods to the class, such as
    `create_entry()`, `remove_entry()` and `update_entry()`.

    :param db: Path of the database to be binded.
    :param type_overload: Type overload dictionary.
    :return: The new dataclass.
    """
    def decorator(dataclass_: type, *_, **__):
        # update type table
        types_table = type_table.copy()
        if type_overload is not None:
            types_table.update(type_overload)
        # add primary key fields if not present
        primary_fields: List[SQLField] = _get_primary_key(dataclass_, types_table)
        default_key = len(primary_fields) == 1 and primary_fields[0].name == "__id__"
        if default_key:
            dataclass_ = make_dataclass(
                dataclass_.__name__,
                fields=[('__id__', int, None)],
                bases=(dataclass_,)
            )
        # add the path of the database to the class
        setattr(dataclass_, 'db', None if isinstance(db, Connection) else db)
        # add a connection object to the class
        setattr(dataclass_, 'connection', None if isinstance(db, str) else db)
        # add the type table for migration.
        setattr(dataclass_, 'types_table', types_table)
        # mark class as decorated
        setattr(dataclass_, '__datalite_decorated__', True)
        # create table
        with connect(dataclass_) as conn:
            cur: sql.Cursor = conn.cursor()
            _create_table(dataclass_, cur, types_table)
        # add methods to the class
        dataclass_.create_entry = _create_entry
        dataclass_.remove_entry = _remove_entry
        dataclass_.update_entry = _update_entry
        # ---
        return dataclass_
    # ---
    return decorator

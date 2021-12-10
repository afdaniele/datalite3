"""
Migrations module deals with migrating data when the object
definitions change. This functions deal with Schema Migrations.
"""
import sqlite3 as sql
from typing import Dict, Tuple, List

from .commons import _create_table, _get_table_cols, DecoratedClass, _assert_is_decorated, \
    _get_table_name, connect, _get_fields, PrimitiveType

_MISSING_VALUE = object()


def _get_class_table(class_: DecoratedClass) -> Tuple[str, List[str]]:
    """
    Check if the class is a datalite class, the database exists
    and the table exists. Return database and table names.

    :param class_: A datalite class.
    :return: A tuple of (table name, list of column names).
    """
    _assert_is_decorated(class_)
    table_name: str = _get_table_name(class_)

    with connect(class_) as con:
        cur: sql.Cursor = con.cursor()
        cur.execute(f"SELECT count(*) FROM sqlite_master "
                    f"WHERE type='table' AND name='{table_name}';")
        count: int = int(cur.fetchone()[0])
        columns: List[str] = _get_table_cols(cur, table_name)
    if not count:
        raise FileExistsError(f"Table {table_name}, already exists.")
    return table_name, columns


def _copy_records(class_: DecoratedClass, table_name: str):
    """
    Copy all records from a table.

    :param class_: Decorated class.
    :param table_name: Name of the table.
    :return: A generator holding dataclass asdict representations.
    """
    with connect(class_) as con:
        cur: sql.Cursor = con.cursor()
        cur.execute(f'SELECT * FROM {table_name};')
        values = cur.fetchall()
        keys = _get_table_cols(cur, table_name)
    records = (dict(zip(keys, value)) for value in values)
    return records


def _drop_table(class_: DecoratedClass, table_name: str) -> None:
    """
    Drop a table.

    :param class_: Decorated class.
    :param table_name: Name of the table to be dropped.
    :return: None.
    """
    with connect(class_) as con:
        cur: sql.Cursor = con.cursor()
        cur.execute(f'DROP TABLE {table_name};')
        con.commit()


def _modify_records(data, col_to_del: Tuple[str], col_to_add: Tuple[str],
                    flow: Dict[str, str]) -> List[Dict[str, PrimitiveType]]:
    """
    Modify the asdict records in accordance
        with schema migration rules provided.

    :param data: Data kept as asdict in tuple.
    :param col_to_del: Column names to delete.
    :param col_to_add: Column names to add.
    :param flow: A dictionary that explain
        if the data from a deleted column
        will be transferred to a column
        to be added.
    :return: The modified data records.
    """
    records = []
    for record in data:
        record_mod = {}
        for key in record.keys():
            if key in col_to_del and key in flow:
                record_mod[flow[key]] = record[key]
            elif key in col_to_del:
                pass
            else:
                record_mod[key] = record[key]
        for key_to_add in col_to_add:
            if key_to_add not in record_mod:
                record_mod[key_to_add] = _MISSING_VALUE
        records.append(record_mod)
    return records


def _migrate_records(class_: type, data,
                     col_to_del: Tuple[str], col_to_add: Tuple[str], flow: Dict[str, str]) -> None:
    """
    Migrate the records into the modified table.

    :param class_: Class of the entries.
    :param data: Data, asdict tuple.
    :param col_to_del: Columns to be deleted.
    :param col_to_add: Columns to be added.
    :param flow: Flow dictionary stating where
        column data will be transferred.
    :return: None.
    """
    with connect(class_) as con:
        cur: sql.Cursor = con.cursor()
        _create_table(class_, cur, type_overload=getattr(class_, 'types_table'))
        con.commit()
    new_records = _modify_records(data, col_to_del, col_to_add, flow)
    for record in new_records:
        keys_to_delete = [k for k in record if record[k] is _MISSING_VALUE]
        for key in keys_to_delete:
            del record[key]
        class_(**record).create_entry()


def basic_migrate(class_: DecoratedClass, column_transfer: dict = None) -> None:
    """
    Given a class, compare its previous table,
    delete the fields that no longer exist,
    create new columns for new fields. If the
    column_flow parameter is given, migrate elements
    from previous column to the new ones.

    :param class_: Datalite class to migrate.
    :param column_transfer: A dictionary showing which
        columns will be copied to new ones.
    :return: None.
    """
    _assert_is_decorated(class_)
    field_names: List[str] = list(map(lambda f: f.name, _get_fields(class_)))
    table_name, column_names = _get_class_table(class_)
    columns_delete: Tuple[str] = tuple(col for col in column_names if col not in field_names)
    columns_add: Tuple[str] = tuple(col for col in field_names if col not in column_names)
    records = _copy_records(class_, table_name)
    _drop_table(class_, table_name)
    _migrate_records(class_, records, columns_delete, columns_add, column_transfer)

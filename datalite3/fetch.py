import sqlite3 as sql
from typing import List, Tuple, Any

from .commons import _convert_sql_format, _get_fields, connect, \
    _assert_is_decorated, Key, _get_key_condition, _validate_key, SQLField, _get_primary_key, \
    DecoratedClass, _get_table_name


def _insert_pagination(query: str, class_: DecoratedClass, page: int, element_count: int) -> str:
    """
    Insert the pagination arguments if page number is given.

    :param query: Query to insert to
    :param class_: Decorated class
    :param page: Page to get.
    :param element_count: Element count in each page.
    :return: The modified (or not) query.
    """
    if page:
        key: List[SQLField] = _get_primary_key(class_)
        fields: str = ", ".join(map(lambda f: f.name, key))
        query += f" ORDER BY {fields} LIMIT {element_count} OFFSET {(page - 1) * element_count}"
    return query + ";"


def is_fetchable(class_: type, key: Key) -> bool:
    """
    Check if a record is fetchable given its key and
    class_ type.

    :param class_: Class type of the object.
    :param key: Unique key of the object.
    :return: If the object is fetchable.
    """
    _assert_is_decorated(class_)
    key = _validate_key(class_, key)
    condition: str = _get_key_condition(class_, key)
    table_name: str = _get_table_name(class_)
    with connect(class_) as con:
        cur: sql.Cursor = con.cursor()
        try:
            cur.execute(f"SELECT 1 FROM {table_name} WHERE {condition};")
        except sql.OperationalError:
            raise KeyError(f"Table {table_name} does not exist.")
    return bool(cur.fetchall())


def fetch_equals(class_: type, field: str, value: Any, ) -> Any:
    """
    Fetch a class_ type variable from its bound db.

    :param class_: Class to fetch.
    :param field: Field to check for, by default, object id.
    :param value: Value of the field to check for.
    :return: The object whose data is taken from the database.
    """
    _assert_is_decorated(class_)
    field_names = list(map(lambda f: f.name, _get_fields(class_)))
    table_name = _get_table_name(class_)
    with connect(class_) as con:
        cur: sql.Cursor = con.cursor()
        cur.execute(f"SELECT * FROM {table_name} WHERE {field} = {_convert_sql_format(value)};")
        field_values = list(cur.fetchone())
    kwargs = dict(zip(field_names, field_values))
    obj = class_(**kwargs)
    return obj


def fetch_from(class_: type, key: Key) -> Any:
    """
    Fetch a class_ type variable from its bound dv.

    :param class_: Class to fetch from.
    :param key: Unique key of the object.
    :return: The fetched object.
    """
    _assert_is_decorated(class_)
    condition: str = _get_key_condition(class_, key)
    if not is_fetchable(class_, key):
        raise KeyError(f"An object with key {key} of type {class_.__name__} does not exist, or"
                       f"otherwise is unreachable.")
    return fetch_if(class_, condition)[0]


def _convert_record_to_object(class_: type, record: Tuple[Any]) -> Any:
    """
    Convert a given record fetched from an SQL instance to a Python Object of given class_.

    :param class_: Class type to convert the record to.
    :param record: Record to get data from.
    :return: the created object.
    """
    _assert_is_decorated(class_)
    field_names = list(map(lambda f: f.name, _get_fields(class_)))
    field_types = {f.name: f.py_type for f in _get_fields(class_)}
    kwargs = dict(zip(field_names, record))
    for key in kwargs:
        if field_types[key] == bytes:
            kwargs[key] = bytes(kwargs[key], encoding='utf-8')
    obj = class_(**kwargs)
    return obj


def fetch_if(class_: type, condition: str, page: int = 0, element_count: int = 10) -> tuple:
    """
    Fetch all class_ type variables from the bound db,
    provided they fit the given condition

    :param class_: Class type to fetch.
    :param condition: Condition to check for.
    :param page: Which page to retrieve, default all. (0 means closed).
    :param element_count: Element count in each page.
    :return: A tuple of records that fit the given condition
        of given type class_.
    """
    _assert_is_decorated(class_)
    table_name = _get_table_name(class_)
    with connect(class_) as con:
        cur: sql.Cursor = con.cursor()
        query: str = f"SELECT * FROM {table_name} WHERE {condition}"
        cur.execute(_insert_pagination(query, class_, page, element_count))
        records: list = cur.fetchall()
    return tuple(_convert_record_to_object(class_, record) for record in records)


def fetch_where(class_: type, field: str, value: Any, page: int = 0,
                element_count: int = 10) -> tuple:
    """
    Fetch all class_ type variables from the bound db,
    provided that the field of the records fit the
    given value.

    :param class_: Class of the records.
    :param field: Field to check.
    :param value: Value to check for.
    :param page: Which page to retrieve, default all. (0 means closed).
    :param element_count: Element count in each page.
    :return: A tuple of the records.
    """
    return fetch_if(class_, f"{field} = {_convert_sql_format(value)}", page, element_count)


def fetch_all(class_: type, page: int = 0, element_count: int = 10) -> tuple:
    """
    Fetchall the records in the bound database.

    :param class_: Class of the records.
    :param page: Which page to retrieve, default all. (0 means closed).
    :param element_count: Element count in each page.
    :return: All the records of type class_ in
        the bound database as a tuple.
    """
    _assert_is_decorated(class_)
    table_name: str = _get_table_name(class_)
    with connect(class_) as con:
        cur: sql.Cursor = con.cursor()
        query: str = f"SELECT * FROM {table_name}"
        try:
            cur.execute(_insert_pagination(query, class_, page, element_count))
        except sql.OperationalError:
            raise TypeError(f"No record of type {table_name}")
        records = cur.fetchall()
    return tuple(_convert_record_to_object(class_, record) for record in records)

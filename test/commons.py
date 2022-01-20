# noinspection PyProtectedMember
from datalite3.commons import _get_fields, DecoratedClass, connect, Key, _get_key_condition, \
    _get_table_name


def getValFromDB(class_: DecoratedClass, key: Key):
    condition: str = _get_key_condition(class_, key)
    table_name: str = _get_table_name(class_)
    with connect(class_) as conn:
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM {table_name} WHERE {condition}')
        field_names = list(map(lambda f: f.name, _get_fields(class_)))
        one = cur.fetchone()
        if one is None:
            raise ValueError(f"Entry with key {key} not found.")
        repr = dict(zip(field_names, one))
        test_object = class_(**repr, __commit__=False)
        return test_object

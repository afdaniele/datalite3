# noinspection PyProtectedMember
from datalite3.commons import _get_fields, DecoratedClass, connect, Key, _get_key_condition


def getValFromDB(class_: DecoratedClass, key: Key):
    condition: str = _get_key_condition(class_, key)
    with connect(class_) as conn:
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM testclass WHERE {condition}')
        field_names = list(map(lambda f: f.name, _get_fields(class_)))
        repr = dict(zip(field_names, cur.fetchone()))
        test_object = class_(**repr)
        return test_object

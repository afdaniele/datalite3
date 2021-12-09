import dataclasses


@dataclasses.dataclass
class A:
    a: int = 5


# noinspection PyUnresolvedReferences
print(A.__dataclass_fields__)

# print(type(A.__dataclass_fields__['a']))

f: dataclasses.Field = A.__dataclass_fields__['a']

# print(f)

f = dataclasses.field()

# print(f)

f.name = 'b'
f.type = float
# f.default = 6.0
f._field_type = dataclasses._FIELD

A.__dataclass_fields__['b'] = f

print(A.__dataclass_fields__)

a = A()
setattr(a, 'b', 6.0)

print(dataclasses.asdict(a))

# noinspection PyUnresolvedReferences
# A.__dataclass_fields__['b'] = dataclasses.field()
# dataclasses.Field(
#     name='a',
#     type=int,
#     default=6,
#     default_factory=dataclasses._MISSING_TYPE,
#     init=True,
#     repr=True,
#     hash=None,
#     compare=True,
#     metadata=mappingproxy({}),
#     _field_type=_FIELD
# )

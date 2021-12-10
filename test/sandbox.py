from typing import TypeVar, Union, Type

import dataclasses

T = TypeVar("T")

# UniqueInt = Annotated[int, float]
# Unique: typing_extensions.AnnotatedMeta = Annotated[T, float, T]


# @dataclasses.dataclass
# class A:
#     value: Unique[int]
#
#
# fields = dataclasses.fields(A)
#
# f = fields[0]
#
# a = A("asd")


# print(isinstance(f.type, Unique))
# print(type(f.type))
# print(f.type.__origin__ is Unique)
# print(f.type.__origin__ is Primary)
# print(f.type is Unique[int])



T1 = Union[int]
T2 = Union[Union[int]]


def Unique(type: Type[T]) -> dataclasses.Field:
    field = dataclasses.field()
    field.type = type
    return field



@dataclasses.dataclass
class B:
    a: Unique(int)
    b: Union[Union[int]]


print(dataclasses.fields(B)[0])
print(dataclasses.fields(B)[1].type.__dict__)

b = B("a", 2)

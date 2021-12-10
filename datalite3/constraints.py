"""
datalite3.constraints module introduces constraint
    types that can be used to hint field variables,
    that can be used to signal datalite decorator
    constraints in the database.
"""
from typing import TypeVar, Union, Tuple, List

T = TypeVar('T')


# TODO: starting with Python 3.9 the Annotated type is available.
#       This is a good replacement for the Generic classes used for Unique and Primary.
#       Docs says:
#            Specifically, a type T can be annotated with metadata x via the typehint
#            Annotated[T, x]. This metadata can be used for either static analysis or at runtime.
#            If a library (or tool) encounters a typehint Annotated[T, x] and has no special
#            logic for metadata x, it should ignore it and simply treat the type as T.


class ConstraintFailedError(Exception):
    """
    This exception is raised when a Constraint fails.
    """
    pass


"""
Dataclass fields hinted with this type signals
    datalite that the bound column of this
    field in the table is NOT NULL and UNIQUE.
"""
Unique = Union[T, Tuple[T]]


"""
Dataclass fields hinted with this type signals
    datalite that the bound column of this
    field in the table is part of the PRIMARY KEY.
"""
Primary = Union[T, List[T]]

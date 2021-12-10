Constraints
================

One of the most useful features provided by SQLite is the concept of
*constraints*. Constraints signal the SQL engine that the values hold in a
specific column **MUST** abide by specific constraints, these might be

* Values of this column cannot be ``NULL``. (``NOT NULL``)
* Values of this column cannot be repeated. (``UNIQUE``)
* Values of this column must fulfill a condition. (``CHECK``)
* Values of this column can be used to identify a record. (``PRIMARY``)
* Values of this column has a default value. (``DEFAULT``)

Some of these constraints are already implemented in `datalite`. With all of the set,
is planned to be implemented in the future.


Default Values
---------------

Columns can be given default values. This is done the same way you would give a
datafield a default value.

.. code-block:: python

    @datalite("mydb.db")
    @dataclass
    class Student:
        student_id: int
        name: str = "Albert Einstein"

Therefore, from now on, any ``Student`` object, whose name is not specified, will
have the default name ``"Albert Einstein"`` and if ``.create_entry()`` method is
called on them, the newly inserted record will, by default, have this value in its
corresponding column.


Unique Values
--------------

Declaring a field unique is done by a special ``TypeVar`` called ``Unique``
this uniqueness check is done in the database level, this introduces has some pros,
but also some cons.

Pushing the uniqueness check to the database level introduces a better ability to
handle concurrency for applications with large traffic, however, this check only
runs when an item is registered, which means no problem will raise in
the object creation *even if* another object of the same type with the same value
hold in the unique field exists, no error will raise. However, if another *record*
with the same value in the unique field is recorded in the bound database, upon
the invocation of the ``.create_entry()`` will raise the ``ConstraintFailedError``
exception.

Uniqueness constraint is declared thusly:

.. code-block:: python

    from datalite3 import Unique

    @datalite("mydb.db")
    @dataclass
    class Student:
        student_id: Unique[int]
        name: str = "Albert Einstein"


Hinting a field with the ``Unique[T]`` type variable will introduce two rules:

#.  The values in the column of the field in the table that represents the dataclass ``Student`` in the bound database ``mydb.db`` cannot be NULL, thus the corresponding field cannot be assigned ``None``.
#.  These same values **must** be unique for each and every record.

Failure of any of these two rules will result in a ``ConstraintFailedError`` exception.


Primary Key
-----------

In SQL, the PRIMARY KEY constraint uniquely identifies each record in a table.
Primary keys must contain UNIQUE values, and cannot contain NULL values.
A table can have only ONE primary key; and in the table, this primary key can consist of
single or multiple columns (fields).

Declaring a field as part of the primary key is done by a special ``TypeVar`` called ``Primary``.
For example, in the example of our ``Student`` class, the primary key can be the field
``student_id``, given that a student ID usually uniquely identifies a student within a given
institution.

.. code-block:: python

    from datalite3 import Primary

    @datalite("mydb.db")
    @dataclass
    class Student:
        student_id: Primary[int]
        name: str = "Albert Einstein"


Hinting a field with the ``Primary[T]`` type variable will introduce two rules:

#.  The values in a ``Primary`` column cannot be NULL, thus the corresponding field cannot be assigned ``None``.
#.  There cannot be two distinct records in the dataset with the same set of values in the primary key fields.

Failure of any of these two rules will result in a ``ConstraintFailedError`` exception.

# `datalite3`

[![PyPI version shields.io](https://img.shields.io/pypi/v/datalite3.svg)](https://pypi.python.org/pypi/datalite3/)
[![PyPI license](https://img.shields.io/pypi/l/datalite3.svg)](https://pypi.python.org/pypi/datalite3/)
[![Documentation Status](https://readthedocs.org/projects/datalite3/badge/?version=latest)](https://datalite3.readthedocs.io/en/latest/?badge=latest)

It should be noted that Datalite is not suitable for secure web applications, it really is only suitable for cases when you can trust user input.

Datalite is a simple Python
package that binds your dataclasses to a table in a sqlite3 database,
using it is extremely simple, say that you have a dataclass definition,
just add the decorator `@datalite("mydb.db")` to the top of the
definition, and the dataclass will now be bound to the file `mydb.db`

[Detailed API reference](https://datalite3.readthedocs.io/en/latest/)

## Download and Install

You can install `datalite3` simply by

```shell script
pip install datalite3
```

Or you can clone the repository and run

```shell script
python setup.py
```

Datalite has no dependencies! As it is built on Python 3.6+ standard library. Albeit, its tests require `unittest` library.

## Datalite in Action

```python
from dataclasses import dataclass
from datalite3 import datalite


@datalite(db="mydb.db")
@dataclass
class Student:
    student_id: int
    student_name: str = "John Smith"
```

This snippet will generate a table in the sqlite3 database file `mydb.db` with
table name `student` and columns `student_id`, `student_name` with SQL types
`INTEGER` and `TEXT`, respectively. The default value for `student_name` is
`John Smith`. A third column `__id__` will be automatically added to hold the
primary key for the records.

##Basic Usage

### Entry manipulation

After creating an object traditionally, given that you used the `datalite` decorator,
the object has three new methods: `.create_entry()`, `.update_entry()`
and `.remove_entry()`, you can add the object to its associated table 
using the former, and remove it using the later. You can also update a record using
the middle.

```python
student = Student(10, "Albert Einstein")
student.create_entry()  # Adds the entry to the table associated in db.db.
student.student_id = 20 # Update an object on memory.
student.update_entry()  # Update the corresponding record in the database.
student.remove_entry()  # Removes from the table.
```


## Custom primary key

If you we want to declare one or more of the fields as part of the primary key for our
records, we can just annotate them with `Primary[type]`, where `type` can be one of 
`int`, `float`, `str`, `bytes`.

```python
from dataclasses import dataclass
from datalite3 import datalite, Primary


@datalite(db="mydb.db")
@dataclass
class Student:
    student_id: Primary[int]
    student_name: str = "John Smith"
```

This snippet will generate a table in the sqlite3 database file `mydb.db` with
table name `student` and columns `student_id`, `student_name` with SQL types
`INTEGER` and `TEXT`, respectively. The column `student_id` will be also the primary
key and no `__id__` column will be added.



## Fetching Records
> :warning: **Limitation! Fetch can only fetch limited classes correctly**: int, float, bytes and str!

Finally, you may wish to recreate objects from a table that already exists, for
this purpose we have the `fetch` module, from this you can import `
fetch_from(class_, key)` as well as `is_fetchable(className, key)` 
former fetches a record from the SQL database given its unique key 
whereas the latter checks if it is fetchable (most likely to check if it exists.)

```python
>>> fetch_from(Student, 20)
Student(student_id=20, student_name='Albert Einstein')
```

We also have three helper methods:
- `fetch_all(class_)`: fetches all records of a given class. Returns a tuple of `class_` objects;
- `fetch_if(class_, condition)`: fetches all the records of type `class_` that satisfy the given 
condition. Here conditions must be written is SQL syntax;
- `fetch_equals(class_, field, value)`: fetches all the records of type `class_` that have the 
column `field` set to `value`;

#### Pagination

`datalite` also supports pagination on `fetch_if`, `fetch_all` and `fetch_where`,
you can specify `page` number and `element_count` for each page (default 10), for
these functions in order to get a subgroup of records.

Basic Decorator Operations
==========================

Creating a datalite class
-------------------------

A datalite class is a special dataclass. It is created by using a decorator ``@datalite3.datalite``,
members of this class are, from Python's perspective, just normal classes. However, they have
additional methods and attributes. ``@datalite`` decorator needs a database to be provided.
This is the database the table for the dataclass will be created in.

.. code-block:: python

    from datalite3 import datalite

    @datalite('mydb.db')
    @dataclass
    class Student:
        student_id: int = 1
        student_name: str = "John Smith"
        student_gpa: float = 3.9

Here, ``datalite`` will create a table called ``student`` in the database file ``mydb.db``, this
file will include all the fields of the dataclass as columns. Default value of these columns
are same as the default value of the dataclass.


Special Methods
---------------

Each object initialised from a dataclass decorated with the ``@dataclass`` decorator automatically
gains access to three special methods. It should be noted, due to the nature of the library, extensions
such as ``mypy`` and IDEs such as PyCharm will not be able to see these methods and may raise exceptions.

With this in mind, let us create a new object and run the methods over this objects.

.. code-block:: python

    new_student = Student(0, "Albert Einstein", 4.0)


Creating an Entry
#################

First special method is ``.create_entry()`` when called on an object of a class decorated with the
``@datalite`` decorator, this method creates an entry in the table of the bound database of the class,
in this case, table named ``student`` in the ``mydb.db``. Therefore, to create the entry of Albert Einstein
in the table:

.. code-block:: python

    new_student.create_entry()


Updating an Entry
#################

Second special method is ``.update_entry()``. If an object's attribute is changed, to update its
record in the database, this method must be called.

.. code-block:: python

    new_student.student_gpa = 5.0
    new_student.update_entry()


Deleting an Entry
#################

To delete an entry from the record, the third and last special method, ``.remove_entry()`` should
be used.

.. code-block:: python

    new_student.remove_entry()


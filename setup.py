import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="datalite3",
    version="0.1.0",
    author="Andrea F. Daniele",
    author_email="afdaniele@ttic.edu",
    description="A small package that binds dataclasses to an sqlite3 database",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/afdaniele/datalite3",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
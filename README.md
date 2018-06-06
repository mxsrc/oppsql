# oppsql
This package provides tooling for interacting with OMNeT++'s SQLite result files.
It contains a script for merging individual result databases, and a small python library to access the data.

Please note that the repository is not stable and its behavior might change without notice.

If you encounter any issues, please report them or open a PR.

## Example use

```
> mergeDBs -p results
> python
>>> import sqlalchemy as sqa
>>> import oppsql
>>> engine = sqa.create_engine('sqlite:///results/out.db')
>>> df = oppsql.get_vector(engine, {'nCars': 320, 'repetition': None}, 'collisions',
		filter_=oppsql.model.vectordata.c.value > 300, aggregate=sqa.func.avg)
>>> df.head()
  repetition  collisions
0          0  552.576250
1          1  546.687829
2          2  549.550911
3          3  553.535197
4          4  540.700926
```

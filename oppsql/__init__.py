import warnings

import pandas as pd
import sqlalchemy as sqa

from . import model as m


__all__ = ['get_unique_param', 'get_vector', 'model']


def _ignore_decimal_warning():
    regex = (
        r"^Dialect sqlite\+pysqlite does \*not\* support Decimal objects natively\, "
        "and SQLAlchemy must convert from floating point - rounding errors and other "
        "issues may occur\. Please consider storing Decimal numbers as strings or "
        "integers on this platform for lossless storage\.$")
    warnings.filterwarnings('ignore', regex, sqa.exc.SAWarning, r'^sqlalchemy\.sql\.sqltypes$')


def get_unique_param(con, name, type):
    """Get a param which is unique for the database

    Raises
    ------
    sqlalchemy.MultipleResultsFound
        If the parameter is not unique.
    """
    return type(con.execute(sqa.select([m.runparam.c.parValue])
                               .where(m.runparam.c.parName.like('%{}'.format(name)))
                               .distinct())
                   .scalar())


def get_vector(engine, by, variable, time=False, run=False, module=False, filter_=None, aggregate=None):
    """Get OMNeT++ result vectors

    Parameters
    ----------
    engine : sqlalchemy.engine.Engine
        Database connection.
    by : str or list or tuple or dict
        The attribute(s) to group results by. Depending on the type, the semantic changes
        Passing a string, list or tuple will group by the given attributes (as present in the runattr table).
        For each attribute, a column is added which contains the corresponding values.
        When given a dict, its keys are interpreted as a list/tuple. The values can be used to filter the results.
        If the value is a list/tuple, only rows containing the specified entries will be returned. If the value is
        a single value, additionally, the corresponding column is dropped.
    variable : string or list or tuple
        The variable(s) to query. If multiple values are given, a additional column containing the variable name is
        present, if only one is given the value column is renamed to the variable name.
    time : bool
        Include the values' timestamps (in seconds).
    module : bool
        Include the emitting module's name.
    filter_ : sqlalchemy expression
        A valid sqlalchemy constraint that is checked agaisnt all returned rows.
    aggregate : sqlalchemy aggregation function
        If given, results are grouped by the attributes given in `by` and the aggregated by the given
        function is applied.

    Notes
    -----
    The simulation repetion number can be included by adding 'repetition' to the attributes. If not included,
    the results of all simulation runs will be included without being able to distinguish them.

    Examples
    --------
    For all attribute-values of 'nCars' return all collisions values.
    >>> df = oppsql.get_vector(engine, 'nCars', 'collisions')
    >>> df.head()
      nCars  collisions
    0   160       150.0
    1   160       161.0
    2   160       138.0
    3   160       151.0
    4   160       155.0

    Include the repetition information.
    >>> df.head()
      nCars repetition  collisions
    0   160          4       150.0
    1   160          4       161.0
    2   160          4       138.0
    3   160          4       151.0
    4   160          4       155.0

    Only return results where nCars equals 320.
    >>> df = oppsql.get_vector(engine, {'nCars': 320, 'repetition': None}, 'collisions')
    >>> df.head()
      repetition  collisions
    0          2       484.0
    1          2       589.0
    2          2       585.0
    3          2       536.0
    4          2       570.0

    Compute the average collisions for each repetition of nCars == 320.
    >>> df = oppsql.get_vector(engine, {'nCars': 320, 'repetition': None}, 'collisions', aggregate=sqa.func.avg)
    >>> df.head()
      repetition  collisions
    0          0  314.153409
    1          1  364.458553
    2          2  412.747559
    3          3  467.429722
    4          4  366.877266

    Compute the average of collisions above 300 for each repetition of nCars == 320.
    >>> df = oppsql.get_vector(engine, {'nCars': 320, 'repetition': None}, 'collisions',
                               filter_=oppsql.model.vectordata.c.value > 300, aggregate=sqa.func.avg)
    >>> df.head()
      repetition  collisions
    0          0  552.576250
    1          1  546.687829
    2          2  549.550911
    3          3  553.535197
    4          4  540.700926
    """
    _ignore_decimal_warning()

    def simtime(simtime_raw, simtime_exponent):
        return simtime_raw * 10 ** simtime_exponent

    def attribute_filter(by, attribute):
        return by[attribute] if (type(by) == dict and attribute in by) else None

    def single_filter(by, attribute):
        f = attribute_filter(by, attribute)
        return f and type(f) != tuple

    def attribute_filter_expression(by, attribute):
        f = attribute_filter(by, attribute)
        if f:
            if single_filter(by, attribute):
                return sqa.and_(m.runattr.c.attrName == attribute,
                                m.runattr.c.attrValue == by[attribute])
            else:
                return sqa.and_(m.runattr.c.attrName == attribute,
                                m.runattr.c.attrValue.in_(by[attribute]))
        else:
            return m.runattr.c.attrName == attribute

    if type(by) == str:
        by = (by,)
    single_variable = type(variable) == str

    attribute_subqueries = {attribute: sqa.select([m.runattr.c.runId,
                                                   m.runattr.c.dbId,
                                                   m.runattr.c.attrValue if not single_filter(by, attribute) else None])
                                          .where(attribute_filter_expression(by, attribute))
                                          .alias()
                            for attribute in by}

    select = []
    select.extend(query.c.attrValue.label(attribute)
                  for attribute, query in attribute_subqueries.items()
                  if not single_filter(by, attribute))
    if time:
        select.append(sqa.func.simtime(m.vectordata.c.simtimeRaw, m.run.c.simtimeExp).label('simtime'))
    if module:
        select.append(m.vector.c.moduleName)
    if single_variable:  # rename value column to variable name
        if aggregate is not None:
            select.append(aggregate(m.vectordata.c.value).label(variable))
        else:
            select.append(m.vectordata.c.value.label(variable))
    else:  # get both vector names and values
        if aggregate is not None:
            select.extend([m.vector.c.vectorName,
                           aggregate(m.vectordata.c.value)])
        else:
            select.extend([m.vector.c.vectorName,
                           m.vectordata.c.value])

    tables = (m.run
               .join(m.vector)
               .join(m.vectordata))
    for query in attribute_subqueries.values():
        tables = tables.join(query)

    constraints = []
    if filter_ is not None:
        constraints.append(filter_)
    if single_variable:
        constraints.append(m.vector.c.vectorName == variable)
    else:
        constraints.append((m.vector.c.vectorName.in_(variable)))

    stmt = sqa.select(select).select_from(tables).where(sqa.and_(*constraints))
    if aggregate is not None:
        stmt = stmt.group_by(*(query.c.attrValue
                               for attribute, query in attribute_subqueries.items()
                               if not single_filter(by, attribute)))

    with engine.connect() as conn:
        if time:
            conn.connection.connection.create_function('simtime', 2, simtime)
        return pd.read_sql(stmt, conn)

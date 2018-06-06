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
    return type(con.execute(sqa.select([m.runparam.c.parValue])
                               .where(m.runparam.c.parName.like('%{}'.format(name)))
                               .distinct())
                   .scalar())


def get_vector(engine, by, variable, time=False, run=False, module=False, filter_=None, aggregate=None):
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

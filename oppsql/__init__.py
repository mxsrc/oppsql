import pandas as pd
import sqlalchemy as sqa

from . import model as m


__all__ = ['get_unique_param', 'get_vector', 'model']


def get_unique_param(con, name, type):
    return type(con.execute(sqa.select([m.runparam.c.parValue])
                               .where(m.runparam.c.parName.like('%{}'.format(name)))
                               .distinct())
                   .scalar())


def get_vector(engine, by, variable, time=False, run=False, module=False):
    def simtime(simtime_raw, simtime_exponent):
        return simtime_raw * 10 ** simtime_exponent

    def filter(by, attribute):
        return by[attribute] if (type(by) == dict and attribute in by) else None

    def single_filter(by, attribute):
        f = filter(by, attribute)
        return f and type(f) != tuple

    def attribute_filter_expression(by, attribute):
        f = filter(by, attribute)
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
        select.append(m.vectordata.c.value.label(variable))
    else:  # get both vector names and values
        select.extend([m.vector.c.vectorName,
                       m.vectordata.c.value])

    tables = (m.run
               .join(m.vector)
               .join(m.vectordata))
    for query in attribute_subqueries.values():
        tables = tables.join(query)

    constraints = []
    if single_variable:
        constraints.append(m.vector.c.vectorName == variable)
    else:
        constraints.append((m.vector.c.vectorName.in_(variable)))

    stmt = sqa.select(select).select_from(tables).where(sqa.and_(*constraints))

    with engine.connect() as conn:
        if time:
            conn.connection.connection.create_function('simtime', 2, simtime)
        return pd.read_sql(stmt, conn)

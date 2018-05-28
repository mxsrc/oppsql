from sqlalchemy import MetaData, Table, Column
from sqlalchemy.types import Integer, Float, Text, Numeric
from sqlalchemy.schema import ForeignKeyConstraint

metadata = MetaData()

db = Table('db', metadata,
           Column('dbId', Integer, primary_key=True),
           Column('dbName', Text, unique=True, nullable=False))

run = Table('run', metadata,
            Column('dbId', Integer, primary_key=True),
            Column('runId', Integer, primary_key=True),
            Column('runName', Text, nullable=False),
            Column('simtimeExp', Integer, nullable=False))

runattr = Table('runattr', metadata,
                Column('dbId', Integer, nullable=False),
                Column('runId', Integer,  nullable=False),
                Column('attrName', Text, nullable=False),
                Column('attrValue', Text, nullable=False),
                ForeignKeyConstraint(['runId', 'dbId'], ['run.runId', 'run.dbId'],
                                     ondelete='CASCADE', onupdate='CASCADE'))

runparam = Table('runparam', metadata,
                 Column('dbId', Integer, nullable=False),
                 Column('runId', Integer,  nullable=False),
                 Column('parName', Text, nullable=False),
                 Column('parValue', Text, nullable=False),
                 ForeignKeyConstraint(['runId', 'dbId'], ['run.runId', 'run.dbId'],
                                      ondelete='CASCADE', onupdate='CASCADE'))

scalar = Table('scalar', metadata,
               Column('dbId', Integer, primary_key=True),
               Column('scalarId', Integer, primary_key=True),
               Column('runId', Integer,  nullable=False),
               Column('moduleName', Text, nullable=False),
               Column('scalarName', Text, nullable=False),
               Column('scalarValue', Float),
               ForeignKeyConstraint(['runId', 'dbId'], ['run.runId', 'run.dbId'],
                                    ondelete='CASCADE', onupdate='CASCADE'))

scalarattr = Table('scalarattr', metadata,
                   Column('dbId', Integer, nullable=False),
                   Column('scalarId', Integer,  nullable=False),
                   Column('attrName', Text, nullable=False),
                   Column('attrValue', Text, nullable=False),
                   ForeignKeyConstraint(['scalarId', 'dbId'], ['scalar.scalarId', 'scalar.dbId'],
                                        ondelete='CASCADE', onupdate='CASCADE'))

statistic = Table('statistic', metadata,
                  Column('dbId', Integer, primary_key=True),
                  Column('statId', Integer, primary_key=True),
                  Column('runId', Integer, nullable=False),
                  Column('moduleName', Text, nullable=False),
                  Column('statName', Text, nullable=False),
                  Column('statCount', Integer, nullable=False),
                  Column('statMean', Float),
                  Column('statStddev', Float),
                  Column('statSum', Float),
                  Column('statSqrsum', Float),
                  Column('statMin', Float),
                  Column('statMax', Float),
                  Column('statWeights', Float),
                  Column('statWeightedSum', Float),
                  Column('statSqrSumWeights', Float),
                  Column('statWeightedSqrSum', Float),
                  ForeignKeyConstraint(['runId', 'dbId'], ['run.runId', 'run.dbId'],
                                       ondelete='CASCADE', onupdate='CASCADE'))

statisticattr = Table('statisticattr', metadata,
                      Column('dbId', Integer, nullable=False),
                      Column('statId', Integer, nullable=False),
                      Column('attrName', Text, nullable=False),
                      Column('attrValue', Text, nullable=False),
                      ForeignKeyConstraint(['statId', 'dbId'], ['statistic.statId', 'statistic.dbId'],
                                           ondelete='CASCADE', onupdate='CASCADE'))

histbin = Table('histbin', metadata,
                Column('dbId', Integer, nullable=False),
                Column('statId', Integer, nullable=False),
                Column('baseValue', Numeric, nullable=False),
                Column('cellValue', Integer, nullable=False),
                ForeignKeyConstraint(['statId', 'dbId'], ['statistic.statId', 'statistic.dbId'],
                                     ondelete='CASCADE', onupdate='CASCADE'))

vector = Table('vector', metadata,
               Column('dbId', Integer, primary_key=True),
               Column('vectorId', Integer, primary_key=True),
               Column('runId', Integer, nullable=False),
               Column('moduleName', Text, nullable=False),
               Column('vectorName', Text, nullable=False),
               Column('vectorCount', Integer),
               Column('vectorMin', Float),
               Column('vectorMax', Float),
               Column('vectorSum', Float),
               Column('vectorSumSqr', Float),
               Column('startEventNum', Integer),
               Column('endEventNum', Integer),
               Column('startSimtimeRaw', Integer),
               Column('endSimtimeRaw', Integer),
               ForeignKeyConstraint(['runId', 'dbId'], ['run.runId', 'run.dbId'],
                                    ondelete='CASCADE', onupdate='CASCADE'))

vectorattr = Table('vectorattr', metadata,
                   Column('dbId', Integer, nullable=False),
                   Column('vectorId', Integer, nullable=False),
                   Column('attrName', Text, nullable=False),
                   Column('attrValue', Text, nullable=False),
                   ForeignKeyConstraint(['vectorId', 'dbId'], ['vector.vectorId', 'vector.dbId'],
                                        ondelete='CASCADE', onupdate='CASCADE'))

vectordata = Table('vectordata', metadata,
                   Column('dbId', Integer, nullable=False),
                   Column('vectorId', Integer, nullable=False),
                   Column('eventNumber', Integer, nullable=False),
                   Column('simtimeRaw', Integer, nullable=False),
                   Column('value', Numeric, nullable=False),
                   ForeignKeyConstraint(['vectorId', 'dbId'], ['vector.vectorId', 'vector.dbId'],
                                        ondelete='CASCADE', onupdate='CASCADE'))

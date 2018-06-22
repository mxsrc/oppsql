from setuptools import setup

setup(
    name='oppsql',
    version='0.1',
    description='Tools for interacting with OmNET++ SQLite result files',
    author='Max Schettler',
    author_email='schettle@mail.uni-paderborn.de',
    scripts=[
        'scripts/mergeDBs',
        'scripts/opplot'
    ],
    packages=['oppsql'],
    install_requires=[
        'sqlalchemy',
        'pandas'
    ]
)

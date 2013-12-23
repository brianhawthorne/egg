from setuptools import setup

setup(
    name='egg',
    version='0.3',
    py_modules=['egg'],
    entry_points=dict(console_scripts=['egg = egg:main']),
)

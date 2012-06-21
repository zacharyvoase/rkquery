import os

from distutils.core import setup

readme_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'README.rst')
readme = open(readme_file).read()


setup(
    name='rkquery',
    version='0.0.1',
    description="Build Riak search queries safely and easily.",
    long_description=readme,
    url='https://github.com/zacharyvoase/rkquery',
    author='Zachary Voase',
    author_email='z@zacharyvoase.com',
    py_modules=['rkquery'],
)

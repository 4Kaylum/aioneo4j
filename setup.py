import io
import os
import re

from setuptools import setup


def read(*parts):
    filename = os.path.join(os.path.abspath(os.path.dirname(__file__)), *parts)
    with io.open(filename, encoding='utf-8', mode='rt') as fp:
        return fp.read()


def get_version():
    regex = r"__version__\s=\s\'(?P<version>[\d\.]+?)\'"
    path = ('aioneo4j-v4', '__init__.py')
    return re.search(regex, read(*path)).group('version')


setup(
    name='aioneo4j-v4',
    version=get_version(),
    author='4Kaylum',
    author_email='callum@voxelfox.co.uk',
    url='https://github.com/4Kaylum/aioneo4j-v4',
    description='asyncio client for neo4j v4',
    long_description=read('README.rst'),
    install_requires=[
        'aiohttp>=2.3.6',
        'async_timeout',
    ],
    packages=['aioneo4j-v4'],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords=['neo4j', 'asyncio', 'aiohttp'],
)

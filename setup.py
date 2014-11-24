import os
import sys

if sys.version_info < (2, 7):
    error = "ERROR: p100 requires Python 2.7+ ... exiting."
    print >> sys.stderr, error
    sys.exit(1)

from setuptools import setup, find_packages

console_scripts = []
extra = dict(install_requires=['reportlab', 'fitbit','pytabix', 'quicksect', 'pillow'],
            entry_points=dict(console_scripts=console_scripts), 
             zip_safe=False)
VERSION = '0.0.0'#actually set in utils.static
static = os.path.join('p100','utils','static.py')

execfile(static)

setup(
name='p100',
version=VERSION,
packages=find_packages(),
author='Andrew Magis',
author_email='Andrew.Magis@systemsbiology.org',
classifiers=[
    'Environment :: Console',
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Natural Language :: English',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Operating System :: Linux',
    'Operating System :: POSIX',
    'Topic :: Education',
    'Topic :: Scientific/Engineering',
    'Topic :: Software Development :: Libraries :: Python Modules',
],
**extra
)

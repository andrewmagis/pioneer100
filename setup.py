import os
import sys

if sys.version_info < (2, 7):
    error = "ERROR: 100i requires Python 2.7+ ... exiting."
    print >> sys.stderr, error
    sys.exit(1)

from setuptools import setup, find_packages

console_scripts = []
extra = dict(install_requires=[],
            entry_points=dict(console_scripts=console_scripts), 
             zip_safe=False)
VERSION = '0.0.0'#actually set in utils.static
static = os.path.join('100i','utils','static.py')
execfile(static)

setup(
name='100i',
version=VERSION,
packages=find_packages(),
author='Andrew Magis',
author_email='Andrew.Magis@systemsbiology.org',
url="/JohnCEarls/GPUDirac",
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

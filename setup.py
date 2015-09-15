# from distutils.core import setup
from setuptools import setup, find_packages

setup(
  name = "alluvialflow",
  packages = find_packages(),
  install_requires = [
    'matplotlib',
    'numpy',
    'pandas',
    'psycopg2',
    'sqlalchemy',
  ],
  version = "0.1.0",
  description = "Alluvial flow visualisations in Python",
  author = "Martin Dittus",
  author_email = "martin@dekstop.de",
  url = "https://github.com/dekstop/alluvialflow",
  download_url = "https://github.com/dekstop/alluvialflow/archive/master.zip",
  keywords = ["visualisation", "plot", "chart", "network", "graph", "flow"],
  classifiers = [
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU Affero General Public License (AGPL)",
    "Operating System :: OS Independent",
    "Topic :: Software Development :: Libraries :: Python Modules",
    ],
  long_description = """\
TODO
"""
)
import os
import re
from setuptools import setup, find_packages

def get_version():
    version_file = os.path.join(os.path.dirname(__file__), 'unacalc', 'main.py')
    with open(version_file, 'r') as f:
        content = f.read()
        version_match = re.search(r"^VERSION\s*=\s*['\"]([^'\"]*)['\"]", content, re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string.")

setup(
    name='unacalc',
    version=get_version(),
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "PyQt5",
        "pint",
        "numpy",
        "pyparsing",
    ],
    entry_points={
        'console_scripts': [
            'unacalc=unacalc.main:main',
        ],
    },
    author='tovam',
    author_email='tovam@proton.me',
    description="Unacalc: A Unit-Aware Calculator",
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/tovam/unacalc',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)

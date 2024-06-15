from setuptools import setup, find_packages

setup(
    name='unacalc',
    version="1.0.1",
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

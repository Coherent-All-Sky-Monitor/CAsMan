#!/usr/bin/env python3
"""
Setup script for CAsMan (CASM Assembly Manager) package.
"""

import os

from setuptools import find_packages, setup

# Read README.md for long description
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open(os.path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip()
                    and not line.startswith("#")]

setup(
    name='casman',
    version='1.0.0',
    description='CASM Assembly Manager - \
        A collection of tools to manage and visualize CASM assembly',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Pranav Sanghavi',
    author_email='pranav.sanghavi@cfa.harvard.edu',
    url='https://github.com/Coherent-All-Sky-Monitor/CAsMan',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'casman': [
            'static/fonts/*',
            'templates/*.html',
        ],
    },
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.8',
            'mypy>=0.812',
        ],
    },
    entry_points={
        'console_scripts': [
            'casman=casman.cli:main',
            'casman-parts=casman.parts:main',
            'casman-scan=casman.assembly:main',
            'casman-visualize=casman.visualization:main',
            'casman-barcode=casman.barcode_utils:main',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.11',
    ],
)

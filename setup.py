#!/usr/bin/env python3
"""
DoS Master Framework Setup Script
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

# Read requirements
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='dos-master-framework',
    version='2.0.0',
    description='Professional DoS Testing Framework for Authorized Security Testing',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='Tech Sky',
    author_email='techsky@example.com',
    url='https://github.com/TechSky/dos-master-framework',
    license='MIT',
    
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    
    install_requires=read_requirements(),
    
    entry_points={
        'console_scripts': [
            'dmf=src.ui.cli:main',
            'dmf-web=src.ui.web:main',
        ],
    },
    
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Security',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
    ],
    
    python_requires='>=3.7',
    
    keywords='dos ddos security testing penetration framework',
    
    project_urls={
        'Bug Reports': 'https://github.com/TechSky/dos-master-framework/issues',
        'Source': 'https://github.com/TechSky/dos-master-framework',
        'Documentation': 'https://github.com/TechSky/dos-master-framework/docs',
    },
    
    package_data={
        'src': ['ui/templates/*.html', 'ui/static/*'],
    },
    
    include_package_data=True,
    zip_safe=False,
)
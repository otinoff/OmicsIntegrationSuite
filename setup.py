#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт установки приложения диагональной интеграции мультимодальных биологических данных
"""

from setuptools import setup, find_packages
import os

# Чтение содержимого файла README.md
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Чтение содержимого файла requirements.txt
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="multimodal-bio-data-integration",
    version="1.0.0",
    author="Разработчик",
    author_email="developer@example.com",
    description="Платформа диагональной интеграции мультимодальных биологических данных",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/example/multimodal-bio-data-integration",
    packages=find_packages(where=".", include=["modules", "modules.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'bio-integration=main:main',
        ],
    },
    package_data={
        '': ['config/*.yaml', 'docs/*', 'LICENSE'],
    },
    include_package_data=True,
    zip_safe=False,
)
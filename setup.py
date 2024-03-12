# SPDX-FileCopyrightText: 2022 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: Apache-2.0

from setuptools import setup
import sys

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

if sys.version_info[:2] < (3, 6):
    sys.exit(
        'Python < 3.6 is not supported'
    )

setup(
    name='freertos-gdb',
    version='1.0.3',
    author='alexey.lapshin',
    author_email='alexey.lapshin@espressif.com',
    description='Python module for operating with freeRTOS-kernel objects in GDB',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache License 2.0',
    url='https://github.com/espressif/freertos-gdb',
    project_urls={
        'Bug Tracker': 'https://github.com/espressif/freertos-gdb/issues',
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    packages=['freertos_gdb'],
    python_requires='>=3.6',
)

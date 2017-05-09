#!/usr/bin/env python3

import setuptools

setup_params = dict(
    name='nwa-stdlib',
    version='0.1',
    packages=['nwastdlib'],
    install_requires=['pytz>=2016.6', 'pyyaml>=3.12'],
    extras_require={
        "mq": ['stomp.py>=4.1']
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    description='Network Automation Standard Library',
    long_description=open('README.rst').read(),
    author='SURFnet NOC',
    author_email='automation-nw@surfnet.nl',
    url='https://gitlab.surfnet.nl/SURFnetNOC/nwa-stdlib',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent'
    ]
)

if __name__ == "__main__":
    setuptools.setup(**setup_params)

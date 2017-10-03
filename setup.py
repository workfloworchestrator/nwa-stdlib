#!/usr/bin/env python3

import setuptools

setup_params = dict(
    name='nwa-stdlib',
    version='0.2',
    packages=setuptools.find_packages(exclude=["*.test", "*.test.*"]),
    install_requires=['pytz==2017.2', 'pyyaml==3.12', 'redis==2.10.6', 'hiredis==0.2.0', 'Flask==0.12.2', 'requests==2.18.4'],
    extras_require={
        "mq": ['stomp.py==4.1'],
        "api": ['connexion==1.1'],
        "redis": ['redis==2.10.5', 'hiredis==0.2.0']
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'Flask-Testing==0.6.2', 'requests-mock==1.3.0'],
    description='Network Automation Standard Library',
    long_description='Network Automation Standard Library',
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

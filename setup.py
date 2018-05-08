#!/usr/bin/env python3

import setuptools

setup_params = dict(
    name='nwastdlib',
    version='0.9.9',
    packages=setuptools.find_packages(),
    include_package_data=True,
    package_data={"nwastdlib": ["py.typed"], "nwastdlib.test.oauth": ["security_definitions.yaml"]},
    install_requires=['pytz==2018.4', 'pyyaml==3.12', 'redis==2.10.6', 'hiredis==0.2.0', 'Flask==1.0.2', 'requests==2.18.4'],
    extras_require={
        "redis": ['redis==2.10.6', 'hiredis==0.2.0']
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'Flask-Testing==0.7.1', 'requests-mock==1.4.0'],
    description='Network Automation Standard Library',
    long_description='Network Automation Standard Library',
    author='SURFNet Automation',
    author_email='automation-nw@surfnet.nl',
    url='https://gitlab.surfnet.nl/automation/nwa-stdlib',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent'
    ]
)

if __name__ == "__main__":
    setuptools.setup(**setup_params)

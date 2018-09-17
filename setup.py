#!/usr/bin/env python3

import setuptools

test_dependencies = ['pytest', 'Flask-Testing==0.7.1', 'requests-mock==1.4.0', 'fakeredis==0.10.3']
setup_params = dict(
    name='nwastdlib',
    version='0.9.19',
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=['pytz==2018.5', 'ruamel.yaml~=0.15.66', 'redis==2.10.6', 'hiredis==0.2.0', 'Flask>=1.0.2',
                      'requests==2.18.4'],
    extras_require={
        "redis": ['redis==2.10.6', 'hiredis==0.2.0'],
        "test": test_dependencies
    },
    setup_requires=['pytest-runner'],
    tests_require=test_dependencies,
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

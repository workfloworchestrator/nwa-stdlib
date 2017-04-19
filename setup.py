from setuptools import setup

setup(
    name='nwa-stdlib',
    version='0.1',
    packages=['nwastdlib'],
    description='Network Automation Standard Library',
    long_description=open('README.rst').read(),
    author='SURFnet NOC',
    author_email='noc@surfnet.nl',
    url='https://gitlab.surfnet.nl/SURFnetNOC/nwa-stdlib',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent'
    ]
)

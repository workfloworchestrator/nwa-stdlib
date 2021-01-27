from setuptools import find_packages, setup

setup(
    name="nwa-stdlib",
    version="1.1.0",
    packages=find_packages(),
    url="https://gitlab.surfnet.nl/automation/nwa-stdlib",
    classifiers=["License :: OSI Approved :: Apache2 License", "Programming Language :: Python :: 3.x"],
    license="Apache2",
    author="Automation",
    author_email="automation-nw@surfnet.nl",
    description="NWA standard library.",
    install_requires=[
        "aioredis",
        "structlog~=20.2.0",
    ],
)

from setuptools import setup, find_packages  # type: ignore

setup(
    name="PyOrchestrate",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["requests", "loguru", "zmq"],
    entry_points={
        'console_scripts': [
            'pyorchestrate=PyOrchestrate.cli:main',
        ],
    },
)

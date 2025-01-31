from setuptools import setup, find_packages

setup(
    name="PyOrchestrate",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["requests", "loguru", "zmq"],
)

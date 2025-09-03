from setuptools import setup, find_packages

setup(
    name="tradinglab-backend",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.32.3",
        "urllib3>=2.2.3",
        "certifi>=2024.8.30",
        "charset-normalizer>=3.4.0",
        "idna>=3.10",
    ],
    python_requires=">=3.11",
)

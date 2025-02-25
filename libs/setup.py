from setuptools import setup, find_packages

setup(
    name="pulpomatic-libs",
    version="0.1.0",
    package_dir={"": "src"},  # Directorio raíz de los paquetes
    packages=find_packages(where="src"),  # Buscar paquetes en src
    install_requires=[
        "requests",
        "python-dotenv",
        "pandas",
        "pytz"
    ],
    author="Pulpomatic",
    description="Librería común para los scripts de Pulpomatic",
)

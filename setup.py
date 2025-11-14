"""
Setup do HydroAI - Sistema Inteligente de Análise de Bacias Hidrográficas

Este arquivo permite instalar o HydroAI como um pacote Python
Instalação: pip install -e .
"""

from setuptools import setup, find_packages
from pathlib import Path

# Lê o arquivo README.md se existir
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# Lê o arquivo requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#')
        ]

setup(
    # Identificação básica
    name="hydroai",
    version="0.1.0",
    author="HydroAI Development Team",
    author_email="contact@hydroai.com",
    
    # Descrição
    description="Sistema inteligente e modular para análise de bacias hidrográficas",
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    # URLs
    url="https://github.com/seu-usuario/hydroai",
    project_urls={
        "Bug Tracker": "https://github.com/seu-usuario/hydroai/issues",
        "Documentation": "https://hydroai.readthedocs.io",
        "Source Code": "https://github.com/seu-usuario/hydroai",
    },
    
    # Classificação
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Hydrology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    
    # Palavras-chave
    keywords=[
        "hydrology", "watershed", "geospatial", "remote-sensing",
        "earth-engine", "mapbiomas", "lulc", "land-use", "gis",
    ],
    
    # Encontra automaticamente todos os pacotes Python
    packages=find_packages(where='.', include=['hydroai*']),
    include_package_data=True,
    
    # Requisitos
    python_requires=">=3.9",
    install_requires=requirements,
    
    # Opções extras (desenvolvimento, documentação)
    extras_require={
        'dev': [
            'pytest>=7.0',
            'black>=23.0',
            'flake8>=6.0',
        ],
    },
    
    # Ponto de entrada (comando de terminal)
    entry_points={
        'console_scripts': [
            'hydroai=main:main',
        ],
    },
    
    # Configuração final
    zip_safe=False,
)

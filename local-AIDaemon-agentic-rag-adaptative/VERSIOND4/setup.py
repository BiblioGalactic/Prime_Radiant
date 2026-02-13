#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup para WikiRAG D4
Permite instalar como paquete Python
"""

from setuptools import setup, find_packages
from pathlib import Path

# Leer README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="wikirag-d4",
    version="1.0.0",
    description="Sistema inteligente de Recuperación Aumentada por Generación (RAG) - Portable",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="WikiRAG Team",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "dataclasses-json>=0.5.14",
        "typing-extensions>=4.0.0",
        "sentence-transformers>=2.2.0",
        "scikit-learn>=1.0.0",
        "numpy>=1.22.0",
        "scipy>=1.9.0",
        "faiss-cpu>=1.7.0",
        "nltk>=3.8",
        "spacy>=3.4.0",
        "regex>=2022.10.31",
        "requests>=2.28.0",
        "aiohttp>=3.8.0",
        "pydantic>=1.10.0",
        "sqlalchemy>=2.0.0",
        "tqdm>=4.64.0",
        "click>=8.1.0",
        "colorama>=0.4.6",
        "pyyaml>=6.0",
        "python-dotenv>=0.20.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.2.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
        ],
        "llama": [
            "llama-cpp-python>=0.2.0",
        ],
        "gpu": [
            "torch>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "wikirag=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Text Processing :: Linguistic",
    ],
    keywords="rag nlp retrieval generation llm ai ml",
    project_urls={
        "Documentation": "https://github.com/wikirag/d4#readme",
        "Source": "https://github.com/wikirag/d4",
        "Bug Reports": "https://github.com/wikirag/d4/issues",
    },
    include_package_data=True,
    zip_safe=False,
)

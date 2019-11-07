#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

test_requirements = [
    "codecov",
    "flake8",
    "pytest",
    "pytest-cov",
    "pytest-raises",
]

setup_requirements = [
    "pytest-runner",
]

dev_requirements = [
    "bumpversion>=0.5.3",
    "coverage>=5.0a4",
    "flake8>=3.7.7",
    "ipython>=7.5.0",
    "m2r>=0.2.1",
    "pytest>=4.3.0",
    "pytest-cov==2.6.1",
    "pytest-raises>=0.10",
    "pytest-runner>=4.4",
    "Sphinx>=2.0.0b1",
    "sphinx_rtd_theme>=0.1.2",
    "tox>=3.5.2",
    "twine>=1.13.0",
    "wheel>=0.33.1",
]

interactive_requirements = [
    "altair",
    "jupyterlab",
    "matplotlib",
    "ipykernel"
]

requirements = [
    "pandas",
    "tifffile==0.15.1",
    "matplotlib",
    "lkaccess",
    "jupyterlab",
    "matplotlib",
]

extra_requirements = {
    "test": test_requirements,
    "setup": setup_requirements,
    "dev": dev_requirements,
    "interactive": interactive_requirements,
    "all": [
        *requirements,
        *test_requirements,
        *setup_requirements,
        *dev_requirements,
        *interactive_requirements
    ]
}

setup(
    author="Gregory R Johnson",
    author_email="gregj@alleninstitute.org",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: Allen Institute Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Pipeline tools for analyzing FOVs",
    entry_points={
        "console_scripts": [
            "my_example=fov_processing_pipeline.bin.my_example:main"
        ],
    },
    install_requires=requirements,
    license="Allen Institute Software License",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="fov_processing_pipeline",
    name="fov_processing_pipeline",
    packages=find_packages(),
    python_requires=">=3.6",
    setup_requires=setup_requirements,
    test_suite="fov_processing_pipeline/tests",
    tests_require=test_requirements,
    extras_require=extra_requirements,
    url="https://github.com/gregjohnso/fov_processing_pipeline",
    # Do not edit this string manually, always use bumpversion
    # Details in CONTRIBUTING.rst
    version="0.1.0",
    zip_safe=False,
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import pytest

import pandas as pd

from .. import wrappers


@pytest.fixture
def resources_dir() -> Path:
    return Path(__file__).parent / "resources"


@pytest.fixture
def demo_cell_data(resources_dir):
    return pd.read_csv("{}/cell_data.csv".format(resources_dir))


@pytest.fixture
def demo_cell_row(demo_cell_data):
    return demo_cell_data.iloc[0]


@pytest.fixture
def demo_fov_data(resources_dir):
    return pd.read_csv("{}/fov_data.csv".format(resources_dir))


@pytest.fixture
def demo_fov_row(demo_fov_data):
    return demo_fov_data.iloc[0]


@pytest.fixture
def row_image(demo_fov_row):
    return wrappers.row2im(demo_fov_row)[0]

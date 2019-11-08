#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import pytest

import pandas as pd


@pytest.fixture
def resources_dir() -> Path:
    return Path(__file__).parent / "resources"


@pytest.fixture
def demo_fov_data(resources_dir):
    return pd.read_csv("{}/fov_data.csv".format(resources_dir))


@pytest.fixture
def demo_fov_row(demo_fov_data):
    return demo_fov_data.iloc[0]
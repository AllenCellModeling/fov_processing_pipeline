from .. import data
import numpy as np


def test_cell_data_to_fov_data(demo_cell_data):
    fov_data = data._cell_data_to_fov_data(demo_cell_data)

    # make sure the length of the FOV dataframe is the same length as the number of unique FOVIds
    assert len(np.unique(fov_data["FOVId"])) == len(fov_data["FOVId"])


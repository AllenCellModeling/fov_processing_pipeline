from .. import wrappers
from unittest import mock


def test_row2im(demo_fov_row):
    im = wrappers.row2im(demo_fov_row)

    assert len(im.shape) == 4


def dummy_get_data(demo_cell_row, demo_fov_row):
    return demo_cell_row, demo_fov_row


def dummy_get_data2(demo_cell_row, demo_fov_row):
    return demo_cell_row, demo_fov_row


def test_save_load_data(demo_cell_row, demo_fov_row, tmp_dir):
    with mock.patch("data.get_data", side_effect=dummy_get_data):
        cell_data, fov_data = wrappers.save_load_data(tmp_dir, overwrite=True)


#     import pdb
#     pdb.set_trace()

from unittest import mock

from .. import wrappers


def test_row2im(demo_fov_row):
    im = wrappers.row2im(demo_fov_row)

    assert len(im.shape) == 4


def test_save_load_data(demo_cell_data, demo_fov_data, tmpdir):
    # with mock.patch(
    #     "fov_processing_pipeline.data.get_data", side_effect=dummy_get_data
    # ):

    with mock.patch("fov_processing_pipeline.data.get_data") as mocked_get_data:
        mocked_get_data.return_value = (demo_cell_data, demo_fov_data)
        cell_data, fov_data = wrappers.save_load_data(tmpdir, overwrite=True)


from unittest import mock
from aicsimageio import imread
import numpy as np

from .. import wrappers


def test_row2im(demo_fov_row):

    # load complete image file with channel number indicators for comparison
    im_comp = imread(demo_fov_row['SourceReadPath']).squeeze()
    im_comp = np.transpose(im_comp, [0, 2, 3, 1])

    # test default channel order and reshaping
    im, ch_list = wrappers.row2im(demo_fov_row)
    assert im.shape[0] == len(ch_list)
    assert len(im.shape) == 4
    assert len(ch_list) == 4
    assert ch_list == ['BF', 'DNA', 'Cell', 'Struct']
    assert list(im.shape[1:]) == list(im_comp.shape[1:])

    # test if brightfield channel returns the correct image (and image size)
    im, ch_list = wrappers.row2im(demo_fov_row, ['BF'])
    assert list(im_comp[demo_fov_row['ChannelNumberBrightfield'],:,:,:].flatten()) == list(im.flatten())
    assert im.shape[0] == len(ch_list)

    # test if DNA channel returns the correct image
    im, ch_list = wrappers.row2im(demo_fov_row, ['DNA'])
    assert list(im_comp[demo_fov_row['ChannelNumber405'],:,:,:].flatten()) == list(im.flatten())

    # test if cell membrane channel returns the correct image
    im, ch_list = wrappers.row2im(demo_fov_row, ['Cell'])
    assert list(im_comp[demo_fov_row['ChannelNumber638'],:,:,:].flatten()) == list(im.flatten())

    # test if structure channel returns the correct image
    im, ch_list = wrappers.row2im(demo_fov_row, ['Struct'])
    assert list(im_comp[demo_fov_row['ChannelNumberStruct'],:,:,:].flatten()) == list(im.flatten())

    # test if repeated channels work
    im, ch_list = wrappers.row2im(demo_fov_row, ['BF','BF'])
    assert im.shape[0] == len(ch_list)
    assert list(im[0,:,:,:].flatten()) == list(im[1,:,:,:].flatten())


def test_save_load_data(demo_cell_data, demo_fov_data, tmpdir): #, dummy_get_data):
    # with mock.patch(
    #     "fov_processing_pipeline.data.get_data", side_effect=dummy_get_data
    # ):

    with mock.patch("fov_processing_pipeline.data.get_data") as mocked_get_data:
        mocked_get_data.return_value = (demo_cell_data, demo_fov_data)
        cell_data, fov_data = wrappers.save_load_data(tmpdir, overwrite=True)


from unittest import mock
import pytest
import os
import numpy as np
import pandas as pd

from aicsimageio import imread

from .. import wrappers

# Because all of the functions in wrappers.py a @task decorator, they need to be run with
# wrappers.function_name(<inputs>)


def test_row2im(demo_fov_row):

    # load complete image file with channel number indicators for comparison
    im_comp = imread(demo_fov_row["SourceReadPath"]).squeeze()
    im_comp = np.transpose(im_comp, [0, 2, 3, 1])

    # test default channel order and reshaping
    im, ch_list = wrappers.row2im(demo_fov_row)
    assert im.shape[0] == len(ch_list)
    assert len(im.shape) == 4
    assert len(ch_list) == 4
    assert ch_list == ["BF", "DNA", "Cell", "Struct"]
    assert list(im.shape[1:]) == list(im_comp.shape[1:])

    # test if brightfield channel returns the correct image (and image size)
    im, ch_list = wrappers.row2im(demo_fov_row, ["BF"])
    assert list(
        im_comp[demo_fov_row["ChannelNumberBrightfield"], :, :, :].flatten()
    ) == list(im.flatten())
    assert im.shape[0] == len(ch_list)

    # test if DNA channel returns the correct image
    im, ch_list = wrappers.row2im(demo_fov_row, ["DNA"])
    assert list(im_comp[demo_fov_row["ChannelNumber405"], :, :, :].flatten()) == list(
        im.flatten()
    )

    # test if cell membrane channel returns the correct image
    im, ch_list = wrappers.row2im(demo_fov_row, ["Cell"])
    assert list(im_comp[demo_fov_row["ChannelNumber638"], :, :, :].flatten()) == list(
        im.flatten()
    )

    # test if structure channel returns the correct image
    im, ch_list = wrappers.row2im(demo_fov_row, ["Struct"])
    assert list(
        im_comp[demo_fov_row["ChannelNumberStruct"], :, :, :].flatten()
    ) == list(im.flatten())

    # test if repeated channels work
    im, ch_list = wrappers.row2im(demo_fov_row, ["BF", "BF"])
    assert im.shape[0] == len(ch_list)
    assert list(im[0, :, :, :].flatten()) == list(im[1, :, :, :].flatten())


def test_save_load_data(demo_cell_data, demo_fov_data, tmpdir):

    # with mock.patch(
    #     "fov_processing_pipeline.data.get_data", side_effect=dummy_get_data
    # ):

    with mock.patch("fov_processing_pipeline.data.quilt.get_data") as mocked_get_data:
        mocked_get_data.return_value = (demo_cell_data, demo_fov_data)
        cell_data, fov_data = wrappers.save_load_data.run(tmpdir, overwrite=True)


def test_data_splits(demo_fov_data, tmpdir):

    # Data Prep
    # the demo_fov_data is only one element, so we repeat it a few times, and rebuild the random numbers
    demo_fov_data = pd.concat([demo_fov_data] * 100, 0)
    demo_fov_data["FOVId_rng"] = np.random.rand(demo_fov_data.shape[0])

    # have two structures
    demo_fov_data["ProteinDisplayName"].iloc[0:10] = "structure_a"
    demo_fov_data["ProteinDisplayName"].iloc[10::] = "structure_b"

    u_groups = ["structure_a", "structure_b"]

    split_names = ["train", "validate", "test"]
    split_amounts = [0.8, 0.1, 0.1]

    # Test for expected behavior
    splits_dict = wrappers.data_splits.run(
        demo_fov_data,
        tmpdir,
        split_names=split_names,
        split_amounts=split_amounts,
        group_column="ProteinDisplayName",
        split_column="FOVId_rng",
    )

    assert len(splits_dict) == len(np.unique(demo_fov_data["ProteinDisplayName"]))

    inds_list = list()
    # confirm that there there is content for all split names and groups
    for u_group in u_groups:
        assert u_group in splits_dict

        for split_name in split_names:
            assert split_name in splits_dict[u_group]

            assert os.path.exists(splits_dict[u_group][split_name]["save_path"])

            inds_list.append(splits_dict[u_group][split_name]["split_inds"])

    inds_list = np.hstack(inds_list)

    assert len(inds_list) == demo_fov_data.shape[0]
    assert len(inds_list) == len(np.unique(inds_list))

    # Make sure it craps out when there is the wrong input

    # does not sum to 1
    split_amounts_wrong = [0.8, 0.1]

    with pytest.raises(AssertionError):
        splits_dict = wrappers.data_splits.run(
            demo_fov_data,
            tmpdir,
            split_names=split_names,
            split_amounts=split_amounts_wrong,
            group_column="ProteinDisplayName",
            split_column="FOVId_rng",
        )

    demo_fov_data_wrong = demo_fov_data.copy()

    # rng > 1
    demo_fov_data_wrong["FOVId_rng"].iloc[0] = 1.1

    with pytest.raises(AssertionError):
        splits_dict = wrappers.data_splits.run(
            demo_fov_data_wrong,
            tmpdir,
            split_names=split_names,
            split_amounts=split_amounts,
            group_column="ProteinDisplayName",
            split_column="FOVId_rng",
        )

    # Not existing group column
    with pytest.raises(AssertionError):
        splits_dict = wrappers.data_splits.run(
            demo_fov_data,
            tmpdir,
            split_names=split_names,
            split_amounts=split_amounts,
            group_column="this column doesnt exist",
            split_column="FOVId_rng",
        )

    # Not existing split column
    with pytest.raises(AssertionError):
        splits_dict = wrappers.data_splits.run(
            demo_fov_data,
            tmpdir,
            split_names=split_names,
            split_amounts=split_amounts,
            group_column="ProteinDisplayName",
            split_column="this column doesnt exist",
        )

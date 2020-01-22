import pytest
import numpy as np
import pandas as pd

from ..stats import z_intensity_profile, histogram_stats


def confirm_output(stats_df):
    # make sure output is a pandas dataframe
    assert isinstance(stats_df, pd.DataFrame)

    # make sure there is only a single-row dataframe
    assert stats_df.shape[0] == 1


def test_z_intensity_profile(tmpdir, demo_row_image):
    fov_stats = z_intensity_profile.im2stats(demo_row_image)

    confirm_output(fov_stats)

    # make sure there is a column for each channel
    assert fov_stats.shape[1] == demo_row_image.shape[0]

    # make sure that each entry is the same length as the Z-dimension of the image
    for k in fov_stats:
        assert len(fov_stats[k][0]) == demo_row_image.shape[3]

    # make sure we raise a value error if the image is < 4 dims
    with pytest.raises(ValueError):
        z_intensity_profile.im2stats(np.sum(demo_row_image, 0))

    # make sure we raise a value error if the image is > 4 dims
    with pytest.raises(ValueError):
        z_intensity_profile.im2stats(np.expand_dims(demo_row_image, 0))

    z_intensity_profile.plot(fov_stats, tmpdir, "test")


def test_histogram_stats(tmpdir, demo_row_image):

    fov_stats = histogram_stats.im2stats(demo_row_image, 0)

    confirm_output(fov_stats)

    # throw an error when the channel index is out of bounds
    with pytest.raises(IndexError):
        fov_stats = histogram_stats.im2stats(demo_row_image, 100)
import pytest
import numpy as np
import pandas as pd

from ..stats import z_intensity_profile


def test_z_intensity_profile(tmpdir, demo_row_image):
    fov_stats = z_intensity_profile.im2stats(demo_row_image)

    # make sure output is a pandas dataframe
    assert isinstance(fov_stats, pd.DataFrame)

    # make sure there is only a single-row dataframe
    assert fov_stats.shape[0] == 1

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

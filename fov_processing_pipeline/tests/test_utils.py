import os
from aicsimageio import writers
import numpy as np
from .. import utils


def test_im2proj(tmpdir, demo_row_image):
    im = demo_row_image

    im_proj = utils.im2proj(im)

    assert im_proj.shape[0] == 3

    assert im_proj.shape[1] == (im.shape[1] + im.shape[3])
    assert im_proj.shape[2] == (im.shape[2] + im.shape[3])

    # move this to setup/teardown later
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    # do this without throwing an error
    with writers.PngWriter(
        "{}/tmp_im.png".format(tmpdir), overwrite_file=True
    ) as writer:
        writer.save(im_proj)

    ####################
    # Test Recoloring
    ####################

    # Red image
    # 3YX image
    im = np.zeros([3, 10, 10])

    im[0] = 1

    # default output should be magenta
    im_proj = utils.im2proj(im)

    assert np.sum(im_proj[0]) > 0
    assert np.sum(im_proj[1]) == 0
    assert np.sum(im_proj[2]) > 0

    # Green image
    # 3YX image
    im = np.zeros([3, 10, 10])
    im[1] = 1

    # default output should be yellow
    im_proj = utils.im2proj(im)

    assert np.sum(im_proj[0]) > 0
    assert np.sum(im_proj[1]) > 0
    assert np.sum(im_proj[2]) == 0

    # Blue image
    # 3YX image
    im = np.zeros([3, 10, 10])
    im[2] = 1

    # default output should be cyan
    im_proj = utils.im2proj(im)

    assert np.sum(im_proj[0]) == 0
    assert np.sum(im_proj[1]) > 0
    assert np.sum(im_proj[2]) > 0


def test_rowim2proj(tmpdir, demo_row_image):
    im = demo_row_image

    im_proj = utils.rowim2proj(im)

    # move this to setup/teardown later
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    # do this without throwing an error
    with writers.PngWriter(
        "{}/tmp_rowim.png".format(tmpdir), overwrite_file=True
    ) as writer:
        writer.save(im_proj)

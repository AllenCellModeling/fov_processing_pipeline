from .. import utils
from aicsimageio import writers
import os


def test_im2proj(tmp_dir, row_image):
    im = row_image

    im_proj = utils.im2proj(im)

    assert im_proj.shape[0] == 3

    assert im_proj.shape[1] == (im.shape[1] + im.shape[3])
    assert im_proj.shape[2] == (im.shape[2] + im.shape[3])

    # move this to setup/teardown later
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # do this without throwing an error
    with writers.PngWriter(
        "{}/tmp_im.png".format(tmp_dir), overwrite_file=True
    ) as writer:
        writer.save(im_proj)


def test_rowim2proj(tmp_dir, row_image):
    im = row_image

    im_proj = utils.rowim2proj(im)

    # move this to setup/teardown later
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # do this without throwing an error
    with writers.PngWriter(
        "{}/tmp_rowim.png".format(tmp_dir), overwrite_file=True
    ) as writer:
        writer.save(im_proj)

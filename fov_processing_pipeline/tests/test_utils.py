from .. import utils
from aicsimageio import writers
import os


def test_im2proj(tmpdir, row_image):
    im = row_image

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

    # # CZYX image
    # im = np.zeros([3,10, 10, 10])
    # im[0] =


def test_rowim2proj(tmpdir, row_image):
    im = row_image

    im_proj = utils.rowim2proj(im)

    # move this to setup/teardown later
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    # do this without throwing an error
    with writers.PngWriter(
        "{}/tmp_rowim.png".format(tmpdir), overwrite_file=True
    ) as writer:
        writer.save(im_proj)


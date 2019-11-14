from .. import utils
from aicsimageio import writers
import os
import numpy as np

from fov_processing_pipeline.reports import im2bigim


def test_im2bigim(tmpdir, demo_fov_data, demo_row_image):
    im = demo_row_image

    im_proj = utils.rowim2proj(im)

    # move this to setup/teardown later
    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    im_path = "{}/tmp_rowim.png".format(tmpdir)

    with writers.PngWriter(im_path, overwrite_file=True) as writer:
        writer.save(im_proj)

    im_paths = np.array([im_path] * 25)
    im_ids = np.arange(0, 25)

    labels = np.array(["structure A"] * 10 + ["structure B"] * 15)

    bigim_dir = "{}/bigim/".format(tmpdir)
    if not os.path.exists(bigim_dir):
        os.makedirs(bigim_dir)

    im2bigim(im_paths, im_ids, labels, bigim_dir)

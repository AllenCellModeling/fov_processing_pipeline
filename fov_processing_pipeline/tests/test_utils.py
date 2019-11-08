from .. import wrappers, utils


def test_cell_data_to_fov_data(demo_fov_row):
    im = wrappers.row2im(demo_fov_row)

    im_proj = utils.im2proj(im)

    assert im_proj.shape[2] == 3

    assert im_proj.shape[0] == (im.shape[1] + im.shape[3])
    assert im_proj.shape[1] == (im.shape[2] + im.shape[3])


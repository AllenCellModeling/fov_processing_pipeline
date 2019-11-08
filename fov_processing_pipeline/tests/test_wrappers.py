from .. import wrappers


def test_row2im(demo_fov_row):
    im = wrappers.row2im(demo_fov_row)

    assert len(im.shape) == 4

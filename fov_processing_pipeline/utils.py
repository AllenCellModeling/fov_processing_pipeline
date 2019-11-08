import numpy as np
from numpy.random import Generator, PCG64
import argparse


def int2rand(id):
    # psuedorandomly deterministically convert an ID (integer) to a random number between 0 and 1
    rg = Generator(PCG64(id))
    return rg.random()


def str2bool(v):
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def im2proj(im):
    # im is a c by y by x by z image

    if len(im.shape) == 4:
        im_xy = np.max(im, 3)[0]
        im_xz = np.max(im, 1)[0].permute(0, 2, 1).flip(1)
        im_yz = np.max(im, 2)[0]

        corner = np.zeros([im.shape[0], im.shape[3], im.shape[3]]).type_as(im)

        top = np.cat([im_yz, im_xy], 2)
        bottom = np.cat([corner, im_xz], 2)

        im = np.cat([top, bottom], 1)

    im = im.cpu().detach().numpy().transpose([1, 2, 0])

    for i in range(im.shape[2]):
        im[:, :, i] = im[:, :, i] / (np.max(im[:, :, i]))

    color_transform = np.array([[1, 1, 0], [0, 1, 1], [1, 0, 1]])

    im_shape = im.shape

    im_reshape = im.reshape([np.prod(im_shape[0:2]), im_shape[2]]).T

    im_recolored = np.matmul(color_transform, im_reshape).T

    im = im_recolored.reshape(im_shape)
    im = im / np.max(im)

    im[im > 1] = 1

    return im

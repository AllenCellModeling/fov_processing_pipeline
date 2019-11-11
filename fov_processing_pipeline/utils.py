import numpy as np
from numpy.random import Generator, PCG64
import argparse
import matplotlib.pyplot as plt


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


def im2proj(im, color_transform=None):
    # im is a CYXZ numpy array
    #
    # returns a CYX max intensity project image

    if color_transform is None:
        n_channels = im.shape[0]

        if n_channels == 3:
            # do magenta-yellow-cyan instead of RGB
            color_transform = np.array([[1, 1, 0], [0, 1, 1], [1, 0, 1]]).T
        elif n_channels == 1:
            # do white
            color_transform = np.array([[1, 1, 1]])
        else:
            # pick colors from HSV
            color_transform = plt.get_cmap("jet")(np.linspace(0, 1, n_channels))[:, 0:3]

    if len(im.shape) == 4:
        im_xy = np.max(im, 3)
        im_xz = np.max(im, 1).transpose(0, 2, 1)[:, ::-1]
        im_yz = np.max(im, 2)

        corner = np.zeros([im.shape[0], im.shape[3], im.shape[3]])

        top = np.concatenate([im_xy, im_yz], 2)

        bottom = np.concatenate([im_xz, corner], 2)

        im = np.concatenate([bottom, top], 1)

    for i in range(im.shape[0]):
        im[i] = im[i] / (np.max(im[i]))

    im = im.transpose([1, 2, 0])
    im_shape = list(im.shape)

    im_reshape = im.reshape([np.prod(im_shape[0:2]), im_shape[2]]).T

    im_recolored = np.matmul(color_transform.T, im_reshape).T

    im_shape[2] = 3
    im = im_recolored.reshape(im_shape)
    im = im.transpose([2, 0, 1])

    im = im / np.max(im)

    im[im > 1] = 1

    return im


def rowim2proj(im):
    # im is a CYXZ image returned from wrappers.row2im
    #
    # returns a combined projection image

    im_fluor = im2proj(im[0:3])
    im_trans = im2proj(im[[3]], color_transform=np.array([[1, 1, 1]]))

    return np.concatenate([im_fluor, im_trans], 1)

#!/usr/bin/env python

import os
import numpy as np

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from aicsimageio import writers


def im2bigim(impaths, im_ids, labels, save_parent_dir, nwide=5, ndeep=50, verbose=True):
    font = ImageFont.truetype(
        os.path.dirname(__file__) + "/../../etc/dejavu-sans-mono/DejaVuSansMono.ttf", 12
    )

    labels = np.array([str(label) for label in labels])

    ulabels, uinds = np.unique(np.array(labels), return_inverse=True)

    for ulabel in ulabels:
        if verbose:
            print("Printing " + str(ulabel))

        label_inds = labels == ulabel

        proj_paths = np.array(impaths)[label_inds]
        inds = im_ids[label_inds]

        im_list = list()
        for proj_path, ind in zip(proj_paths, inds):
            if not os.path.exists(proj_path):
                if verbose:
                    print("Missing: " + proj_path)
                continue

            im_proj = Image.open(proj_path)
            draw = ImageDraw.Draw(im_proj)

            draw.text((20, 20), str(ind), (255, 255, 255), font=font)

            im_proj = np.asarray(im_proj)

            if len(im_list) > 0 and im_proj.shape != im_list[0].shape:
                if verbose:
                    print(proj_path + " is not the same size as the others...")
                # continue

            im_list.append(im_proj)

        #  sometimes the images come out different sizes, so we have to pad them
        imsizes = [im.shape for im in im_list]
        imsizes = np.asarray(imsizes)

        maxsize = np.max(imsizes, 0)
        padsize = np.subtract(maxsize, imsizes)

        for i in range(0, len(im_list)):
            pad = padsize[i]
            im_list[i] = np.pad(
                im_list[i], ((0, pad[0]), (0, pad[1]), (0, pad[2])), "constant"
            )

        im_list = [
            np.hstack(im_list[start : (start + nwide)])  # noqa
            for start in range(0, len(im_list), nwide)
        ]

        pad = im_list[0].shape[1] - im_list[-1].shape[1]
        im_list[-1] = np.pad(im_list[-1], ((0, 0), (0, pad), (0, 0)), "constant")

        c = 0
        for i in range(0, len(im_list), ndeep):
            im_out = np.vstack(im_list[i : (i + ndeep)]).astype("uint8")  # noqa

            im_out = im_out.transpose([2, 1, 0])

            with writers.PngWriter(
                "{}/diagnostics_{}_{}.png".format(save_parent_dir, str(ulabel), str(c)),
                overwrite_file=True,
            ) as writer:
                writer.save(im_out)

            c += 1

from aicsimageio import imread
import os
import pandas as pd
import pickle
import numpy as np

from . import data, utils
from aicsimageio import writers


def row2im(df_row):
    # take a dataframe row and returns an image in CZYX format with channels in order of
    # Brightfield, DNA, Membrane, Structure, seg_dna, seg_membrane, seg_structure
    #
    # load all channels of all z-stacks and transpose to order: c, y, x, z
    im = imread(df_row.SourceReadPath).squeeze()
    im = np.transpose(im, [0, 2, 3, 1])
    keep_channels = []
    for c in df_row.index:
        if "Channel" in c:
            keep_channels.append(df_row[c])

    return im[keep_channels, :, :, :]


def im2stats():
    # takes a FOV and returns some basic statistics
    raise NotImplementedError


def save_load_data(save_dir, trim_data=False, overwrite=False):
    # Wrapper function to retreive local copy of the pipeline4 dataframes or go retreive it
    #
    # save_dir - directory in which data is saved
    # trim_data - use a canned data subset
    # overwrite - overwrite local data

    cell_data_path = "{}/cell_data.csv".format(save_dir)
    fov_data_path = "{}/cell_data.csv".format(save_dir)

    if not os.path.exists(cell_data_path) or overwrite:
        cell_data, fov_data = data.get_data(trim_data=trim_data)

        cell_data.to_csv(cell_data_path)
        fov_data.to_csv(fov_data_path)

    else:
        cell_data = pd.read_csv(cell_data_path)
        fov_data = pd.read_csv(fov_data_path)

    return cell_data, fov_data


def process_fov_row(fov_row, stats_path, proj_path, overwrite=False):
    # Performs atomic operations on a data row that corresponds to a single FOV
    #
    # fov_row - pandas dataframe row (from data.get_data() frunction)
    # stats_path - save path for image statistics
    # proj_path - save path for projection image
    # overwrite - overwrite local data

    if os.path.exists(proj_path) and ~overwrite:
        return

    im = row2im(fov_row)
    stats = im2stats(im)

    with open("stats_path", "wb") as f:
        pickle.dump(stats, f)

    im_proj = utils.im2proj(im)

    with writers.PngWriter(proj_path) as writer:
        writer.save(im_proj)

    return

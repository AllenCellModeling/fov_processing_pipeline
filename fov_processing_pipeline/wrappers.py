from aicsimageio import imread
import os
import pandas as pd
import pickle
import numpy as np
from fov_processing_pipeline import stats

from . import data, utils


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



def im2stats(im):
    ############################################
    # For a given image, calculate some basic statistcs and return as dictionary
    # Inputs:
    #   - im: CYXZ image, numpy array
    # Returns:
    #   - results: dictionary of all calculated statics for the image
    ############################################
    nz = im.shape[3]

    # create dictionary to fill
    results = dict()

    # get intensity stats as a function of z slices for all channels
    for c in range(im.shape[0]):
        results.update(stats.z_intensity_stats(im, c))
        results.update(stats.intensity_percentiles_by_channel(im,c))

    # get structure to cell and dna cross correlations
    # stats.update(cross_correlations(im))
    
    return results



def save_load_data(save_dir, data_subset=False, overwrite=False):
    cell_data_path = "{}/cell_data.csv".format(save_dir)
    fov_data_path = "{}/cell_data.csv".format(save_dir)

    if not os.path.exists(cell_data_path) or overwrite:
        cell_data, fov_data = data.get_data(data_subset=data_subset)

        cell_data.to_csv(cell_data_path)
        fov_data.to_csv(fov_data_path)

    else:
        cell_data = pd.read_csv(cell_data_path)
        fov_data = pd.read_csv(fov_data_path)

    return cell_data, fov_data


def process_fov_row(fov_row, stats_path, proj_path, overwrite=False):
    if os.path.exists(proj_path) and ~overwrite:
        return

    im, channel_names = row2im(fov_row)
    stats = im2stats(im)

    with open("stats_path", "wb") as f:
        pickle.dump(stats, f)

    im_proj = utils.im2proj(im)
    imwrite(im_proj, proj_path)

    return

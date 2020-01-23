import os
import pickle
import warnings

import numpy as np
import pandas as pd
from aicsimageio import imread, writers
from prefect import task

from . import data, postprocess, reports, stats, utils


def row2im(df_row, ch_order=["BF", "DNA", "Cell", "Struct"]):
    # take a dataframe row and returns an image in CZYX format with channels in desired order
    # Default order is: Brightfield, DNA, Membrane, Structure
    #
    # load all channels of all z-stacks and transpose to order: c, y, x, z
    im = imread(df_row.SourceReadPath).squeeze()
    im = np.transpose(im, [0, 2, 3, 1])

    ch2ind = dict(
        {
            "BF": df_row["ChannelNumberBrightfield"],
            "DNA": df_row["ChannelNumber405"],
            "Cell": df_row["ChannelNumber638"],
            "Struct": df_row["ChannelNumberStruct"],
        }
    )
    ch_reorg = [int(ch2ind[ch]) for ch in ch_order]

    return im[ch_reorg, :, :, :], ch_order


def im2stats(im):
    ############################################
    # For a given image, calculate some basic statistcs and return as dictionary
    # Inputs:
    #   - im: CYXZ image, numpy array
    # Returns:
    #   - results: dictionary of all calculated statics for the image
    ############################################

    # create dictionary to fill
    results = list()

    # get intensity stats as a function of z slices for all channels
    for c in range(im.shape[0]):

        results.append(stats.z_intensity_stats(im, c))
        results.append(stats.intensity_percentiles_by_channel(im, c))

    results.append(stats.z_intensity_profile.im2stats(im))

    results = pd.concat(results, axis=1)

    # get structure to cell and dna cross correlations
    # stats.update(cross_correlations(im))

    return results


@task(tags=["dask-resource:cores=32"])
def save_load_data(
    save_dir, protein_list=None, n_fovs=100, overwrite=False, dataset="quilt"
):
    """
    Retreives or loads data.

    Parameters
    ----------
    save_dir: str
        save directory of results

    trim_data: bool or int
        do we trim the data or not, or how many data to we trim the dataset to

    overwrite: bool
        do we overwrite the files if they exist? (i.e. do you want to put new results in an old directory)

    dataset: str
        can be "quilt" or "labkey"

    Returns
    -------
    cell_data: pandas.DataFrame
        Dataframe where each row corresponds to a single cell

    fov_data: pandas.DataFrame
        Dataframe where each row corresponds to an FOV

    """

    cell_data_path = "{}/cell_data.csv".format(save_dir)
    fov_data_path = "{}/fov_data.csv".format(save_dir)

    if not os.path.exists(cell_data_path) or overwrite:

        if dataset == "labkey":
            cell_data, fov_data = data.labkey.get_data(
                protein_list=protein_list, n_fovs=n_fovs
            )
        elif dataset == "quilt":
            image_dir = "{}/images".format(save_dir)
            cell_data, fov_data = data.quilt.get_data(
                save_dir=image_dir,
                protein_list=protein_list,
                n_fovs=n_fovs,
                overwrite=overwrite,
            )
        else:
            raise ValueError('unrecognized dataset parameter "{}"'.format(dataset))

        cell_data.to_csv(cell_data_path)
        fov_data.to_csv(fov_data_path)

    else:
        cell_data = pd.read_csv(cell_data_path)
        fov_data = pd.read_csv(fov_data_path)

    return cell_data, fov_data


@task
def cell_data_to_summary_table(cell_data, summary_path):
    cell_line_summary_table = reports.cell_data_to_summary_table(cell_data)

    cell_line_summary_table.to_csv(summary_path)


@task
def data2stats(df, save_dir, overwrite=False, fov_flag=False):
    ############################################
    # For a given fov dataframe, calculate stats for each row's multichannel image and recompile into new stats df
    # Inputs:
    #   - df: dataframe of cell data including CYXZ images
    #   - save_dir: directory to save stats dataframe
    #   - overwrite: flag to overwrite if already exists
    #   - fov_flag: true if FOV or false is cell dataframe is input, used for setting Id's
    # Returns:
    #   - results: dataframe with image stats for all cell or all fovs in dataframe
    ############################################

    if not fov_flag:
        stats_path = "{}/cell_stats.csv".format(save_dir)
        id = "CellId"
    else:
        stats_path = "{}/fov_stats.csv".format(save_dir)
        id = "FOVId"

    if not os.path.exists(stats_path) or overwrite:
        stats_df = pd.DataFrame(
            [im2stats(row2im(df.iloc[i])) for i in range(df.shape[0])]
        )
        stats_df[id] = df[id]

        stats_df.to_csv(stats_path)

    else:
        stats_df = pd.read_csv(stats_path)

    return stats_df


@task
def load_stats(df, stats_paths):
    # consolidate stats?
    stats_list = list()
    for i, stats_path in enumerate(stats_paths):
        if os.path.exists(stats_path):
            with open(stats_path, "rb") as f:
                stats = pickle.load(f)

            stats["FOVId"] = df["FOVId"].iloc[i]
            stats["ProteinDisplayName"] = df["ProteinDisplayName"].iloc[i]
            stats_list.append(stats)
        else:
            warnings.warn("{} is missing.".format(stats_path))

    df_stats = pd.concat(stats_list, axis=0)

    return df_stats


@task
def stats2plots(df_stats: pd.DataFrame, save_dir: str):
    """
    general stats to plots function, saves results to save_dir

    Parameters
    ----------
    df_stats: pd.DataFrame
        Big dataframe of statistics determined by the combination of data2stats and load_stats

    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    u_proteins = np.unique(df_stats.ProteinDisplayName)

    for u_protein in u_proteins:
        df_stats_tmp = df_stats[u_protein == df_stats.ProteinDisplayName]

        stats.plot_im_percentiles(
            df_stats_tmp,
            save_path="{}/fov_stats_{}.png".format(save_dir, u_protein),
            title=u_protein,
        )

        stats.z_intensity_profile.plot(
            df_stats_tmp,
            "{}/z_intensity_profile".format(save_dir),
            suffix=u_protein,
            center_on_channel="z_intensity_profile_Ch1",
        )

        stats.z_intensity_profile.plot(
            df_stats_tmp,
            "{}/z_intensity_profile_uncentered".format(save_dir),
            suffix=u_protein,
        )

    # drop the non feature data

    # TODO do this in a better way... probably use well annotated anndata instead of Pandas

    stats.pca.plot(
        df_stats.drop(["FOVId", "ProteinDisplayName"], axis=1),
        save_dir,
        labels=df_stats["ProteinDisplayName"],
    )


@task
def process_fov_row(fov_row, stats_path, proj_path, overwrite=False):
    # Performs atomic operations on a data row that corresponds to a single FOV
    #
    # fov_row - pandas dataframe row (from data.get_data() frunction)
    # stats_path - save path for image statistics
    # proj_path - save path for projection image
    # overwrite - overwrite local data

    if os.path.exists(proj_path) and ~overwrite:
        return

    proj_dir = os.path.dirname(proj_path)
    if not os.path.exists(proj_dir):
        os.makedirs(proj_dir)

    stats_dir = os.path.dirname(stats_path)
    if not os.path.exists(stats_dir):
        os.makedirs(stats_dir)

    im, ch = row2im(fov_row)
    stats = im2stats(im)

    with open(stats_path, "wb") as f:
        pickle.dump(stats, f)

    im_proj = utils.rowim2proj(im, ch)

    with writers.PngWriter(proj_path) as writer:
        writer.save(im_proj)

    return


@task
def im2diagnostics(fov_data, proj_paths, save_dir, overwrite=False):

    warnings.warn("Overwrite checking currently not implemented.")

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    reports.im2bigim(proj_paths, fov_data.FOVId, fov_data.ProteinDisplayName, save_dir)


@task
def qc_stats(df_stats, save_path):
    """
    Given a stats dataframe, check for any FOV's that have their brightest average intensity for a zslice in the
    brightfield channel at the bottom of the image. This is an indicator of a slice being out of order, and we want
    to QC these out of our list. Then use interpolation to make sure all zslice data has the same # of z measurements.

    Parameters
    ----------
    df: Dataframe
        A stats dataframe, containing rows corresponding to FOVs, and having a column with the mean intensity for the
        DNA channel, for each zslice in each FOV.
    Returns
    -------
    df: Dataframe
        Same dataframe, with aberrant FOVs removed and zstacks interpolated to have the same number of z slices.
        Saved as a .pickle as well.
    """

    df_stats = postprocess.fov_qc(df_stats)
    df_stats = postprocess.zsize_qc(df_stats)
    df_stats.to_pickle(save_path)

    return df_stats

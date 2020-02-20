"""
wrappers.py: Base functions for the FOV processing pipeline called by process.py.

Most functions have an @task decoration for Prefect pipelining.

Each function performs a spcific task, and they should be listed in pipeline order. The file directory organization
should be controlled by this file (e.g. no paths other than "parent_dir" should need to be specified.)

"""

import os
import warnings
import pandas as pd
import pickle
import numpy as np

from aicsimageio import imread, writers

from prefect import task
from prefect.triggers import any_successful

from . import data, utils, stats, reports, postprocess


RAW_DIR = "raw"
QC_DIR = "qc"

USE_CURRENT_RESULTS_DEFAULT = False


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


@task
def save_load_data(
    parent_dir, protein_list=None, n_fovs=100, overwrite=False, dataset="quilt"
):
    """
    Retreives or loads data.

    Parameters
    ----------
    parent_dir: str
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

    save_dir = f"{parent_dir}/{RAW_DIR}/"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    cell_data_path = f"{save_dir}/cell_data.csv"
    fov_data_path = f"{save_dir}/fov_data.csv"

    if not os.path.exists(cell_data_path) or overwrite:

        if dataset == "labkey":
            cell_data, fov_data = data.labkey.get_data(
                protein_list=protein_list, n_fovs=n_fovs
            )
        elif dataset == "quilt":
            image_dir = f"{save_dir}/images/"
            cell_data, fov_data = data.quilt.get_data(
                save_dir=image_dir,
                protein_list=protein_list,
                n_fovs=n_fovs,
                overwrite=overwrite,
            )
        else:
            raise ValueError(f"unrecognized dataset parameter {dataset}")

        cell_data.to_csv(cell_data_path)
        fov_data.to_csv(fov_data_path)

    else:
        cell_data = pd.read_csv(cell_data_path)
        fov_data = pd.read_csv(fov_data_path)

    return cell_data, fov_data


@task
def get_save_paths(parent_dir, fov_data):
    # Sets up the save paths for all of the results

    save_dir = f"{parent_dir}/{QC_DIR}/"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    summary_path = f"{save_dir}/summary.csv"

    stats_paths = [
        f"{save_dir}/plate_{row.PlateId}/stats_{row.FOVId}.pkl"
        for i, row in fov_data.iterrows()
    ]
    proj_paths = [
        f"{save_dir}/plate_{row.PlateId}/proj_{row.FOVId}.png"
        for i, row in fov_data.iterrows()
    ]

    return summary_path, stats_paths, proj_paths


@task
def cell_data_to_summary_table(cell_data, summary_path):
    cell_line_summary_table = reports.cell_data_to_summary_table(cell_data)
    cell_line_summary_table.to_csv(summary_path)


@task
def get_data_rows(fov_data):
    return [row[1] for row in fov_data.iterrows()]


@task
def process_fov_row(fov_row, stats_path, proj_path, overwrite=False):
    # Performs atomic operations on a data row that corresponds to a single FOV
    #
    # fov_row - pandas dataframe row (from data.get_data() frunction)
    # stats_path - save path for image statistics
    # proj_path - save path for projection image
    # overwrite - overwrite local data

    if os.path.exists(proj_path) and ~overwrite:
        return True

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

    return True


@task(trigger=any_successful)
def load_stats(
    df, stats_paths, save_parent, use_current_results=USE_CURRENT_RESULTS_DEFAULT
):
    # consolidate stats?

    save_dir = f"{save_parent}/{QC_DIR}"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    save_path = f"{save_dir}/fov_stats.csv"

    if not os.path.exists(save_path) or not use_current_results:
        stats_list = list()
        for i, stats_path in enumerate(stats_paths):
            if os.path.exists(stats_path):
                with open(stats_path, "rb") as f:
                    stats = pickle.load(f)

                stats["FOVId"] = df["FOVId"].iloc[i]
                stats["FOVId_rng"] = df["FOVId_rng"].iloc[i]
                stats["ProteinDisplayName"] = df["ProteinDisplayName"].iloc[i]
                stats_list.append(stats)
            else:
                warnings.warn(f"{stats_path} is missing.")

        df_stats = pd.concat(stats_list, axis=0)
        df_stats.to_csv(save_path)

    else:
        df_stats = pd.read_csv(save_path)

    return df_stats


@task
def qc_stats(df_stats, save_parent, use_current_results=USE_CURRENT_RESULTS_DEFAULT):
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

    save_dir = f"{save_parent}/{QC_DIR}"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    save_path = f"{save_dir}/fov_stats_qc.csv"

    if not os.path.exists(save_path) or not use_current_results:

        df_stats = postprocess.fov_qc(df_stats)
        df_stats = postprocess.zsize_qc(df_stats)
        df_stats.to_csv(save_path)

    else:
        df_stats = pd.read_csv(save_path)

    return df_stats


@task
def stats2plots(df_stats: pd.DataFrame, parent_dir: str):
    """
    general stats to plots function, saves results to parent_dir

    Parameters
    ----------
    df_stats: pd.DataFrame
        Big dataframe of statistics determined by the combination of data2stats and load_stats

    """

    save_dir = f"{parent_dir}/{QC_DIR}/plots/"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    u_proteins = np.unique(df_stats.ProteinDisplayName)

    for u_protein in u_proteins:
        df_stats_tmp = df_stats[u_protein == df_stats.ProteinDisplayName]

        stats.plot_im_percentiles(
            df_stats_tmp,
            save_path=f"{save_dir}/fov_stats_{u_protein}.png",
            title=u_protein,
        )

        stats.z_intensity_profile.plot(
            df_stats_tmp,
            f"{save_dir}/z_intensity_profile",
            suffix=u_protein,
            center_on_channel="z_intensity_profile_Ch1",
        )

        stats.z_intensity_profile.plot(
            df_stats_tmp,
            f"{save_dir}/z_intensity_profile_uncentered",
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
def im2diagnostics(fov_data, proj_paths, parent_dir, overwrite=False):

    warnings.warn("Overwrite checking currently not implemented.")

    save_dir = f"{parent_dir}/{QC_DIR}/diagnostics"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    reports.im2bigim(proj_paths, fov_data.FOVId, fov_data.ProteinDisplayName, save_dir)


@task
def data_splits(
    df_stats,
    parent_dir,
    split_names=["train", "validate", "test"],
    split_amounts=[0.8, 0.1, 0.1],
    group_column="ProteinDisplayName",
    split_column="FOVId_rng",
    id_column="FOVId",
):
    """
    Given a stats dataframe, split each unique entry of `group_column` into groups based on the `split_column random
    number, and save those results in `parent_dir` with the f"{parent_dir}/{unique_group_column}_{train_or_test}.csv"

    Parameters
    ----------
    df_stats: Dataframe
        A stats dataframe with the columns corresponding to `group_column` and `split_column`

    parent_dir: str
        Save directory for splits files

    split_names: list of strs
        Names of the splits

    split_amounts: list of floats
        Fraction of data split that corresponds to split names.
        Must be same length as split names and sum to 1.

    group_column: str
        Column over which to create cohorts that we split up

    split_column: str
        Column with values that we split in. All values must be in the range of [0, 1). See: numpy.random.rand

    id_column: str
        Column corresponding to unique ids

    Returns
    -------
    splits_dict
        A dictionary corresponding to split groups, split names, and the save file
    """

    # all these assertions should probably be raise.ValueError

    save_dir = f"{parent_dir}/{QC_DIR}/data_splits/"

    # check for correct input
    assert np.sum(split_amounts) == 1
    assert isinstance(group_column, str)
    assert isinstance(split_column, str)
    assert len(split_names) == len(split_amounts)

    assert group_column in df_stats.columns
    assert split_column in df_stats.columns

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if group_column is not None:
        group = df_stats[group_column].values
    else:
        group = np.zeros(df_stats.shape[0])

    split_amounts = np.hstack([[0], split_amounts])
    split_amounts = np.cumsum(split_amounts)

    values_to_split_on = df_stats[split_column].values
    assert np.all(values_to_split_on >= 0)
    assert np.all(values_to_split_on < 1)

    splits = np.ones(df_stats.shape[0]) * -1
    for i, (lb, hb) in enumerate(zip(split_amounts[0:-1], split_amounts[1::])):
        splits[(values_to_split_on >= lb) & (values_to_split_on < hb)] = i

    assert np.max(splits) <= (len(split_names) - 1)
    assert not np.any(splits == -1)

    splits_dict = {}

    for u_group in np.unique(group):
        u_group_inds = group == u_group

        splits_dict[u_group] = {}

        for i, split_name in enumerate(split_names):
            split_inds = (splits == i) & u_group_inds

            save_path = f"{save_dir}/{u_group}_{split_name}.csv"
            df_stats.iloc[split_inds].to_csv(save_path)

            splits_dict[u_group][split_name] = {}
            splits_dict[u_group][split_name]["save_path"] = save_path

            splits_dict[u_group][split_name][id_column] = df_stats[id_column][
                split_inds
            ]

    return splits_dict

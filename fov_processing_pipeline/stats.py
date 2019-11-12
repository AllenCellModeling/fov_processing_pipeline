import numpy as np
import matplotlib.pyplot as plt
import warnings
import pandas as pd


def z_intensity_stats(im, c):
    ############################################
    # For a given channel and image, calculate stats for the intensity as a function of z slice:
    #   - Mean intensity
    #   - Standard deviation of intensity
    # Inputs:
    #   - im: CYXZ image, numpy array
    #   - c: channel number, int
    # Returns:
    #   - Dictionary containing mean and standard deviation of intensity as a function of z index
    ############################################
    nz = im.shape[3]

    meanc = np.empty(nz)
    stdc = np.empty(nz)

    for z in range(im.shape[3]):
        imc_vals = im[c, :, :, z].flatten()
        meanc[z] = np.mean(imc_vals)
        stdc[z] = np.std(imc_vals)

    clabel = "Ch" + str(c) + "_"
    zlabel = "_by_z"
    return {clabel + "mean" + zlabel: meanc, clabel + "std" + zlabel: stdc}


def intensity_percentiles_by_channel(im, c, percentile_list=[5, 25, 50, 75, 95]):
    ############################################
    # For each channel of an image, calculate the percentile intensity values in list
    # Inputs:
    #   - im: CYXZ image, numpy array
    #   - c: channel number, int
    #   - percentile_list: list of desired percentiles of channel pixel intensities, list
    # Returns:
    #   - Dictionary containing the desired percentile intensities for the desired channel
    ############################################

    imvals = im[c, :, :, :].flatten()
    results = [np.percentile(imvals, p) for p in percentile_list]
    return dict(
        {
            "Intensity_Percentiles": percentile_list,
            "Ch" + str(c) + "_Percentile_Intensities": results,
        }
    )


def plot_im_percentiles(df, fov_flag=True, save_path=None, save_flag=False, title=None):
    ############################################
    # Given a df of stats for multiple cells, plot all intensity percentile data, assuming five percentiles used in analysis
    # Inputs:
    #   - df: statistics dataframe, containing image stats from a cell data dataframe
    # Returns:
    #   - Figure displaying intensities info:
    #     for each cell, all channels have their 5th, 25th, 50th, 75th, and 95th percentile intensities plotted
    ############################################

    # get columns containing image percentile intensities
    int_pct_cols = [col for col in df.columns if "Percentile_Intensities" in col]
    n_ch = len(int_pct_cols)

    # make a fig and set the color palette
    fig = plt.figure()
    palette = ["y", "m", "b", "k"]

    # loop through cells and channels - for each
    for row_ind in range(df.shape[0]):
        for ch in range(n_ch):
            vals = df["Ch" + str(ch) + "_Percentile_Intensities"].iloc[row_ind]
            # print(vals)
            color = palette[ch]
            plt.scatter(row_ind, vals[2], color=color, marker="o")
            # print(vals[0])
            # print(vals[4])
            plt.vlines(row_ind, ymin=vals[0], ymax=vals[4], color=color)
            for p in [0, 1, 3, 4]:
                plt.hlines(vals[p], xmin=row_ind - 0.2, xmax=row_ind + 0.2, color=color)

    plt.ylabel("Intensity")
    if fov_flag:
        labels = df["FOVId"]
        plt.xlabel("FOV Id")
    else:
        labels = df["CellId"]
        plt.xlabel("Cell Id")
    plt.xticks(ticks=range(df.shape[0]), labels=labels)

    if title:
        plt.title(title)

    # plt.ylim([0.001, 50000])
    plt.yscale("log")

    if save_path:
        plt.savefig(save_path)

    return fig


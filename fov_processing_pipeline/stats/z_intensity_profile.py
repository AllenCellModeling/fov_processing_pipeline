import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

from .utils import check_input

FEATURE_NAME = "z_intensity_profile"


def im2stats(im, channel_names=None) -> pd.DataFrame:
    """
    Sums over XY positions and returns the result for each channel

    Parameters
    ----------
    im: np.array
        CYXZ image
    
    Returns
    -------
    df_stats: pd.DataFrame
        pandas dataframe containing z_profile information for each channel
    """

    channel_names = check_input(im, channel_names, ndims=4)

    stats_dict = dict()

    for ch, channel_name in zip(im, channel_names):
        stats_dict["{}_{}".format(FEATURE_NAME, channel_name)] = np.array(
            ch.sum(0).sum(0)
        )

    df_stats = pd.DataFrame.from_dict([stats_dict])

    return df_stats


def plot(
    df_stats: pd.DataFrame,
    save_dir: str,
    suffix: str,
    normalize_intensity=True,
    center_on_channel=None,
):
    """
    Plots results from im2stats by individual FOV and as a mean over FOV

    Parameters
    ----------
    df_stats: pd.DataFrame
        pandas dataframe from im2stats
    """

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if suffix:
        suffix = "_{}".format(suffix)

    template_str = "{save_dir}/{FEATURE_NAME}{prefix}{suffix}.png"

    template_dict = {
        "save_dir": save_dir,
        "prefix": None,
        "FEATURE_NAME": FEATURE_NAME,
        "suffix": suffix,
    }

    template_dict["prefix"] = "_mean"
    mean_path = template_str.format(**template_dict)

    template_dict["prefix"] = "_fov"
    fov_path = template_str.format(**template_dict)

    # make sure we only use columns that are for this feature
    columns = [c for c in df_stats.columns if c.startswith(FEATURE_NAME)]

    df_stats = df_stats[columns]

    colors = cm.jet(np.linspace(0, 1, len(columns)))

    # figure out how many points are in each plot

    x_label_suffix = ""
    if center_on_channel:
        x_label_suffix = " (centered to {})".format(center_on_channel)

    y_label_suffix = ""
    if normalize_intensity:
        y_label_suffix = " (normalized)"

    # create dataframe to store final z indices and intensities with a channel marker - this is for plotting means by channel later
    df_means = pd.DataFrame(columns=["z", "intensity", "ch"])
    plt.figure()

    label_flag = True
    for i, row in df_stats.iterrows():

        n_pts = len(row[columns[0]])

        x_pos = np.arange(0, n_pts)

        if center_on_channel:

            # max_ind = np.average(x_pos, weights=row[center_on_channel])
            max_ind = np.argmax(row[center_on_channel])

            x_pos = x_pos - max_ind

        for color, column in zip(colors, columns):
            v = row[column]

            if normalize_intensity:
                # v = v / np.sum(v)

                v = v - np.mean(v)
                v = v / np.std(v)

            if label_flag:
                label = column
            else:
                label = None

            df_tmp = pd.DataFrame({"z": x_pos, "intensity": v, "ch": column})

            df_means = df_means.append(df_tmp, ignore_index=True)
            plt.plot(x_pos, v, color=color, label=label)

        label_flag = False

    plt.legend()
    plt.xlabel("z-position{}".format(x_label_suffix))
    plt.ylabel("intensity{}".format(y_label_suffix))

    plt.savefig(fov_path)
    plt.close()

    # make plot of means for each channel
    plt.figure()
    for color, ch in zip(colors, range(len(columns))):
        df_ch = df_means[df_means["ch"].str.contains(str(ch))]
        z_vals = np.arange(min(df_ch["z"]), max(df_ch["z"]) + 1)

        # get mean and standard deviation by z index
        means = []
        stds = []
        for z in z_vals:
            means.append(np.mean(df_ch[df_ch["z"] == z]["intensity"]))
            stds.append(np.std(df_ch[df_ch["z"] == z]["intensity"]))

        # plot mean as a solid line and shade area +- standard deviation relative to mean
        plt.plot(z_vals, means, color=color, label=df_ch["ch"].iloc[0])
        y1 = [means[i] - stds[i] for i in range(len(means))]
        y2 = [means[i] + stds[i] for i in range(len(means))]
        plt.fill_between(z_vals, y1, y2, color=color, alpha=0.1)
    plt.legend()
    plt.xlabel("z-position{}".format(x_label_suffix))
    plt.ylabel("intensity{}".format(y_label_suffix))

    plt.savefig(mean_path)
    plt.close()

    return

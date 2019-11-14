import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm

from .utils import check_input

FEATURE_NAME = "_z_intensity_profile"


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
        stats_dict["{}{}".format(channel_name, FEATURE_NAME)] = np.array(
            ch.sum(0).sum(0)
        )

    df_stats = pd.DataFrame.from_dict([stats_dict])

    return df_stats


def plot(
    df_stats: pd.DataFrame,
    save_path: str,
    normalize_intensity=True,
    center_on_channel=None,
):
    """
    Plots results from im2stats

    Parameters
    ----------
    df_stats: pd.DataFrame
        pandas dataframe from im2stats
    """

    # make sure we only use columns that are for this feature
    columns = [c for c in df_stats.columns if c.endswith(FEATURE_NAME)]

    df_stats = df_stats[columns]

    colors = cm.jet(np.linspace(0, 1, len(columns)))

    # figure out how many points are in each plot

    x_label_suffix = ""
    if center_on_channel:
        x_label_suffix = " (centered to {})".format(center_on_channel)

    y_label_suffix = ""
    if normalize_intensity:
        y_label_suffix = " (normalized)"

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
                v = v/np.std(v)


            if label_flag:
                label = column
            else:
                label = None

            plt.plot(x_pos, v, color=color, label=label)

        label_flag = False

    plt.legend()
    plt.xlabel("z-position{}".format(x_label_suffix))
    plt.ylabel("intensity{}".format(y_label_suffix))

    plt.savefig(save_path)
    plt.close()

    return

import os

import pandas as pd
import numpy as np
import sklearn.preprocessing
import sklearn.decomposition
import matplotlib.pyplot as plt
from matplotlib import cm


FEATURE_NAME = "PCA"


def plot(
    df_stats: pd.DataFrame, save_dir: str, suffix: str = None, labels: np.array = None
):
    """
    Plots whatever is in df_stats in a PCA plot.

    Parameters
    ----------
    df_stats: pd.DataFrame
        pandas dataframe from im2stats

    save_dir: str
        directory in which plot is saved. File name is determined automatically

    suffix: str
        suffix to append to the file name

    """
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if suffix:
        suffix = "_{}".format(suffix)
    else:
        suffix = ""

    template_str = "{save_dir}/{FEATURE_NAME}{prefix}{suffix}.png"

    template_dict = {
        "save_dir": save_dir,
        "prefix": "prefix",
        "FEATURE_NAME": FEATURE_NAME,
        "suffix": suffix,
    }

    template_dict["prefix"] = "_PCs"
    save_path_pcs = template_str.format(**template_dict)

    template_dict["prefix"] = "_variation"
    save_path_var = template_str.format(**template_dict)

    if labels is None:
        labels = np.ones(df_stats.shape[0])

    u_labels = np.unique(labels)

    colors = cm.jet(np.linspace(0, 1, len(u_labels)))

    # take the mean of any multi-element cells in the dataframe
    pca_stats = df_stats.applymap(lambda x: np.mean(x)).values

    # z-score the data
    scaler = sklearn.preprocessing.StandardScaler().fit(pca_stats)
    pca_stats = scaler.transform(pca_stats)

    # do the pca
    pca = sklearn.decomposition.PCA()

    pca.fit(pca_stats)
    pca_stats = pca.transform(pca_stats)

    plt.figure()

    for label, color in zip(u_labels, colors):
        label_inds = labels == label

        plt.scatter(
            pca_stats[label_inds, 0], pca_stats[label_inds, 1], color=color, label=label
        )

    lgd = plt.legend(bbox_to_anchor=(1.04, 1), loc="upper left")

    plt.title("Principle components")
    plt.xlabel("PC1")
    plt.ylabel("PC2")

    plt.savefig(save_path_pcs, bbox_extra_artists=(lgd,), bbox_inches="tight")
    plt.close()

    n_components = len(pca.explained_variance_)

    plt.figure()
    plt.plot(
        np.arange(1, n_components + 1),
        np.cumsum(pca.explained_variance_) / np.sum(pca.explained_variance_),
    )
    plt.xlabel("Component #")
    plt.ylabel("Cumulative explained variance")

    plt.xticks(np.unique(np.round(np.linspace(1, n_components, 5))))
    plt.ylim([-0.05, 1.05])

    plt.savefig(save_path_var)
    plt.close()

    return

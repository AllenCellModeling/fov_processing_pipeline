#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This sample script will get deployed in the bin directory of the
users' virtualenv when the parent module is installed using pip.
"""

import argparse
import logging
import pickle
import os
import pandas as pd

from fov_processing_pipeline import data, wrappers, utils, reports


###############################################################################

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, format="[%(levelname)4s:%(lineno)4s %(asctime)s] %(message)s"
)

###############################################################################


def main():
    # Main function for the FOV processing pipeline
    #
    # This function performs the following operations
    # - loads FOV data from labkey
    # - creates a summary table of FOV data
    # - computes image statistics of each FOV
    # - creates summary plots of each FOV
    # - saves image projections for easy viewing

    p = argparse.ArgumentParser(prog="process", description="Process the FOV pipeline")
    p.add_argument(
        "-s",
        "--save_dir",
        action="store",
        default="./results/",
        help="Save directory for results",
    )
    p.add_argument(
        "--data_subset",
        type=utils.str2bool,
        default=True,
        help="Use cleaned data subset",
    )
    p.add_argument(
        "--overwrite", type=utils.str2bool, default=False, help="overwite saved results"
    )

    p = p.parse_args()

    # load  dataset
    cell_data, fov_data = wrappers.save_load_data(p.save_dir)

    #  make a summary table and save it
    reports.cell_data_to_summary_table(cell_data).to_csv(
        "{}/summary.csv".format(p.save_dir)
    )

    # make the save paths for that stats files and the projected image files
    stats_paths = [
        "{}/stats_{}.pkl".format(p.save_dir, row.FOVId)
        for i, row in fov_data.iterrows()
    ]
    proj_paths = [
        "{}/proj_{}.png".format(p.save_dir, row.FOVId) for i, row in fov_data.iterrows()
    ]

    for (i, fov_row), stats_path, proj_path in zip(
        fov_data.iterrows(), stats_paths, proj_paths
    ):
        wrappers.process_fov_row(fov_row, stats_path, proj_path, p.overwrite)

    # consolidate stats?
    # makes some plots?


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)

if __name__ == "__main__":
    main()
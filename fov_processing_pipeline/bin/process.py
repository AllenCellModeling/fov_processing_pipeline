#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This sample script will get deployed in the bin directory of the
users' virtualenv when the parent module is installed using pip.
"""

import argparse
import logging
import os

from fov_processing_pipeline import wrappers, utils, reports


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
        "--trim_data",
        type=int,
        default=10,
        help="Trim cleaned data to this number (int) of fov's per cell line.",
    )
    p.add_argument(
        "--overwrite", type=utils.str2bool, default=False, help="overwite saved results"
    )
    p.add_argument(
        "--use_current_results", type=utils.str2bool, default=False, help="dont do any processing. just make figures."
    )

    p = p.parse_args()

    if not os.path.exists(p.save_dir):
        os.makedirs(p.save_dir)

    # load  dataset
    cell_data, fov_data = wrappers.save_load_data(
        p.save_dir, trim_data=p.trim_data, overwrite=p.overwrite
    )

    #  make a summary table and save it
    reports.cell_data_to_summary_table(cell_data).to_csv(
        "{}/summary.csv".format(p.save_dir)
    )

    # make the save paths for that stats files and the projected image files
    stats_paths = [
        "{}/plate_{}/stats_{}.pkl".format(p.save_dir, row.PlateId, row.FOVId)
        for i, row in fov_data.iterrows()
    ]
    proj_paths = [
        "{}/plate_{}/proj_{}.png".format(p.save_dir, row.PlateId, row.FOVId)
        for i, row in fov_data.iterrows()
    ]

    if not p.use_current_results:
        # for every FOV, do the processing steps
        for (i, fov_row), stats_path, proj_path in zip(
            fov_data.iterrows(), stats_paths, proj_paths
        ):
            wrappers.process_fov_row(fov_row, stats_path, proj_path, p.overwrite)

    # load, qc, and save stats from each FOV
    df_stats = wrappers.load_stats(fov_data, stats_paths)
    df_stats = wrappers.qc_stats(df_stats)

    # make plots from those stats
    wrappers.stats2plots(df_stats, save_dir="{}/stats_plots".format(p.save_dir))

    # projection paths to diagnostics path
    wrappers.im2diagnostics(
        fov_data, proj_paths, diagnostics_dir="{}/diagnostics".format(p.save_dir)
    )


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)

if __name__ == "__main__":
    main()

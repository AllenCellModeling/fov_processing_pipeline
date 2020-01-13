#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
from pathlib import Path

from prefect import task, Flow, unmapped

from fov_processing_pipeline import wrappers, utils


###############################################################################

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, format="[%(levelname)4s:%(lineno)4s %(asctime)s] %(message)s"
)

###############################################################################


@task
def get_save_paths(save_dir, fov_data):
    # Sets up the save paths for all of the results
    summary_path = "{}/summary.csv".format(save_dir)

    stats_paths = [
        "{}/plate_{}/stats_{}.pkl".format(save_dir, row.PlateId, row.FOVId)
        for i, row in fov_data.iterrows()
    ]
    proj_paths = [
        "{}/plate_{}/proj_{}.png".format(save_dir, row.PlateId, row.FOVId)
        for i, row in fov_data.iterrows()
    ]

    stats_plots_dir = "{}/stats_plots".format(save_dir)
    diagnostics_dir = "{}/diagnostics".format(save_dir)

    return summary_path, stats_paths, proj_paths, stats_plots_dir, diagnostics_dir


@task
def get_data_rows(fov_data):
    return [row[1] for row in fov_data.iterrows()]


def main():
    """
    Dask/Prefect distributed command for running pipeline
    """

    p = argparse.ArgumentParser(prog="process", description="Process the FOV pipeline")
    p.add_argument(
        "-s",
        "--save_dir",
        action="store",
        default="./results/",
        help="Save directory for results",
    )
    p.add_argument(
        "--dataset",
        type=str,
        default="quilt",
        help='Which dataset to use, current can be "quilt", or "labkey"',
    )

    p.add_argument(
        "--n_fovs", type=int, default=100, help="Number of fov's per cell line to use.",
    )
    p.add_argument(
        "--overwrite", type=utils.str2bool, default=False, help="overwite saved results"
    )
    p.add_argument(
        "--use_current_results",
        type=utils.str2bool,
        default=True,
        help="Dont do any processing. just make figures. Set to True by default so you don't overwrite your stuff.",
    )
    p.add_argument(
        "--debug",
        type=utils.str2bool,
        default=False,
        help="Do debugging things (currently applies only to distributed)",
    )
    # distributed stuff
    p.add_argument(
        "--distributed",
        type=utils.str2bool,
        default=False,
        help="Use Prefect/Dask to do distributed compute.",
    )
    p.add_argument(
        "--port",
        type=int,
        default=99999,
        help="Port over which to communicate with the Dask scheduler.",
    )

    p = p.parse_args()

    save_dir = str(Path(p.save_dir).resolve())
    overwrite = p.overwrite
    use_current_results = p.use_current_results

    log.info("Saving in {}".format(save_dir))

    if not os.path.exists(p.save_dir):
        os.makedirs(p.save_dir)

    # https://github.com/AllenCellModeling/scheduler_tools/blob/master/remote_job_scheduling.md

    if p.distributed:
        from prefect.engine.executors import DaskExecutor

        executor = DaskExecutor(
            address="tcp://localhost:{PORT}".format(**{"PORT": p.port})
        )
    else:
        from prefect.engine.executors import LocalExecutor

        executor = LocalExecutor()

    # This is the main function
    with Flow("FOV_processing_pipeline") as flow:
        # for every FOV, do the processing steps

        ###########
        # load data
        ###########
        data = wrappers.save_load_data(
            save_dir, n_fovs=p.n_fovs, overwrite=overwrite, dataset=p.dataset
        )

        # we have to unpack this way because of Prefect-reasons
        cell_data = data[0]
        fov_data = data[1]

        ###########
        # get all of the save paths
        ###########
        paths = get_save_paths(save_dir, fov_data)

        # we have to unpack this way because of Prefect-reasons
        summary_path = paths[0]
        stats_paths = paths[1]
        proj_paths = paths[2]
        stats_plots_dir = paths[3]
        diagnostics_dir = paths[4]

        ###########
        # Summary Table
        ###########
        wrappers.cell_data_to_summary_table(cell_data, summary_path)

        ###########
        # The per-fov map step
        ###########
        fov_rows = get_data_rows(fov_data)

        if not use_current_results:
            process_fov_row_map = wrappers.process_fov_row.map(
                fov_row=fov_rows,
                stats_path=stats_paths,
                proj_path=proj_paths,
                overwrite=unmapped(overwrite),
            )
            upstream_tasks = [process_fov_row_map]
        else:
            upstream_tasks = None

        ###########
        # Load relevant data as a reduce step
        ###########
        df_stats = wrappers.load_stats(
            fov_data, stats_paths, upstream_tasks=upstream_tasks
        )

        ###########
        # QC data based on previous thresholds, etc
        ###########
        df_stats = wrappers.qc_stats(df_stats, "{}/fov_stats_qc.pkl".format(p.save_dir))

        ###########
        # Make Plots
        ###########
        wrappers.stats2plots(
            df_stats, save_dir=stats_plots_dir, upstream_tasks=[df_stats]
        )

        ###########
        # Make diagnostic images
        ###########
        wrappers.im2diagnostics(
            fov_data, proj_paths, save_dir=diagnostics_dir, upstream_tasks=[df_stats]
        )

    state = flow.run(executor=executor)

    df_stats = state.result[flow.get_tasks(name="load_stats")[0]].result

    log.info("Done!")

    return


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)


if __name__ == "__main__":
    main()

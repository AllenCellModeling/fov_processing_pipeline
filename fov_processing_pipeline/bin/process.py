#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
from pathlib import Path

from prefect import Flow, unmapped

from fov_processing_pipeline import wrappers, utils


###############################################################################

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, format="[%(levelname)4s:%(lineno)4s %(asctime)s] %(message)s"
)

###############################################################################


def process(
    save_dir: Path,
    overwrite: bool,
    use_current_results: bool,
    n_fovs: int = 100,
    distributed: bool = False,
    port: int = 99999,
    dataset: str = "quilt",
):
    """
    Dask/Prefect distributed command for running pipeline
    """

    save_dir = str(save_dir.resolve())

    log.info("Saving in {}".format(save_dir))

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # https://github.com/AllenCellModeling/scheduler_tools/blob/master/remote_job_scheduling.md

    if distributed:
        from prefect.engine.executors import DaskExecutor

        executor = DaskExecutor(
            address="tcp://localhost:{PORT}".format(**{"PORT": port})
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
            save_dir, n_fovs=n_fovs, overwrite=overwrite, dataset=dataset
        )

        # we have to unpack this way because of Prefect-reasons
        cell_data = data[0]
        fov_data = data[1]

        ###########
        # get all of the save paths
        ###########
        paths = wrappers.get_save_paths(save_dir, fov_data)

        # we have to unpack this way because of Prefect-reasons
        summary_path = paths[0]
        stats_paths = paths[1]
        proj_paths = paths[2]

        ###########
        # Summary Table
        ###########
        wrappers.cell_data_to_summary_table(cell_data, summary_path)

        ###########
        # The per-fov map step
        ###########
        fov_rows = wrappers.get_data_rows(fov_data)

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
        df_stats = wrappers.qc_stats(df_stats, save_dir)

        ###########
        # Make Plots
        ###########
        wrappers.stats2plots(df_stats, parent_dir=save_dir, upstream_tasks=[df_stats])

        ###########
        # Make diagnostic images
        ###########
        wrappers.im2diagnostics(
            fov_data, proj_paths, parent_dir=save_dir, upstream_tasks=[df_stats]
        )

        ###########
        # Do data splits for the data that survived QC
        ###########
        splits_dict = wrappers.data_splits(
            df_stats, parent_dir=save_dir, upstream_tasks=[df_stats]
        )

    state = flow.run(executor=executor)

    df_stats = state.result[flow.get_tasks(name="load_stats")[0]].result
    splits_dict = state.result[flow.get_tasks(name="data_splits")[0]].result

    log.info("Done!")

    return df_stats, splits_dict


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)


def main():

    p = argparse.ArgumentParser(prog="process", description="Process the FOV pipeline")
    p.add_argument(
        "-s",
        "--save_dir",
        action="store",
        default=Path("./results/"),
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
        default=False,
        help="Dont do any processing. just make figures. Set to True by default so you don't overwrite your stuff.",
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

    args = p.parse_args()

    process(**vars(args))


if __name__ == "__main__":
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import os
from pathlib import Path

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
        type=utils.str2bool,
        default=True,
        help="Use cleaned data subset",
    )
    p.add_argument(
        "--overwrite", type=utils.str2bool, default=False, help="overwite saved results"
    )
    p.add_argument(
        "--use_current_results",
        type=utils.str2bool,
        default=False,
        help="dont do any processing. just make figures.",
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
        help="Use Dask to do distributed compute.",
    )

    p.add_argument(
        "--port",
        type=int,
        default=99999,
        help="Port over which to communicate with the Dask scheduler.",
    )

    p = p.parse_args()

    save_dir = str(Path(p.save_dir).resolve())

    log.info("Saving in {}".format(save_dir))

    if not os.path.exists(p.save_dir):
        os.makedirs(p.save_dir)

    if p.distributed:
        process_distributed(
            save_dir=save_dir,
            trim_data=p.trim_data,
            overwrite=p.overwrite,
            use_current_results=p.use_current_results,
            port=p.port,
            debug=p.debug,
        )

    else:
        process(
            save_dir=save_dir,
            trim_data=p.trim_data,
            overwrite=p.overwrite,
            use_current_results=p.use_current_results,
        )


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


def process(
    save_dir="./results/", trim_data=True, overwrite=False, use_current_results=False
):
    """
    Main single-thread command for running pipeline

    Parameters
    ----------
    save_dir: str = "./results/"

        Save directory of all results

    trim_data: bool = True
        Use a trimmed subset of data

    overwrite: bool = False
        Overwrite currently existing results

    use_current_results: bool = False
        Don't worry about doing any processing, just rebuild the output plots
    """

    # load  dataset
    cell_data, fov_data = wrappers.save_load_data(
        save_dir, trim_data=trim_data, overwrite=overwrite
    )

    (
        summary_path,
        stats_paths,
        proj_paths,
        stats_plots_dir,
        diagnostics_dir,
    ) = get_save_paths(save_dir, fov_data)

    #  make a summary table and save it
    reports.cell_data_to_summary_table(cell_data).to_csv(summary_path)

    if not use_current_results:
        # for every FOV, do the processing steps
        for (i, fov_row), stats_path, proj_path in zip(
            fov_data.iterrows(), stats_paths, proj_paths
        ):
            wrappers.process_fov_row(fov_row, stats_path, proj_path, overwrite)

    # load stats from each FOV
    df_stats = wrappers.load_stats(fov_data, stats_paths)

    # make plots from those stats
    wrappers.stats2plots(df_stats, save_dir=stats_plots_dir)

    # projection paths to diagnostics path
    wrappers.im2diagnostics(fov_data, proj_paths, save_dir=diagnostics_dir)


def process_distributed(
    save_dir="./results/",
    trim_data=True,
    overwrite=False,
    use_current_results=False,
    port=99999,
    debug=False,
):
    """
    Dask/Prefect distributed command for running pipeline

    Parameters
    ----------
    save_dir: str = "./results/"

        Save directory of all results

    trim_data: bool = True
        Use a trimmed subset of data

    overwrite: bool = False
        Overwrite currently existing results

    use_current_results: bool = False
        Don't worry about doing any processing, just rebuild the output plots

    port: int = 99999
        Port over which to communicate to the Dask scheduler
    """
    # https://github.com/AllenCellModeling/scheduler_tools/blob/master/remote_job_scheduling.md

    from prefect import task, Flow
    from prefect.triggers import any_successful

    if debug:
        from prefect.engine.executors import LocalExecutor

        executor = LocalExecutor()
    else:
        from prefect.engine.executors import DaskExecutor

        executor = DaskExecutor(
            address="tcp://localhost:{PORT}".format(**{"PORT": port})
        )

    @task(name="save_load_data_fn")
    def save_load_data(save_dir, trim_data, overwrite):
        cell_data, fov_data = wrappers.save_load_data(
            save_dir, trim_data=trim_data, overwrite=overwrite
        )
        return cell_data, fov_data

    @task(name="get_save_paths_fn")
    def get_save_paths_(save_dir, fov_data):
        (
            summary_path,
            stats_paths,
            proj_paths,
            stats_plots_dir,
            diagnostics_dir,
        ) = get_save_paths(save_dir, fov_data)
        return summary_path, stats_paths, proj_paths, stats_plots_dir, diagnostics_dir

    @task(name="cell_data_to_summary_table_fn")
    def cell_data_to_summary_table(cell_data, summary_path):
        reports.cell_data_to_summary_table(cell_data).to_csv(summary_path)

    @task(name="get_data_rows")
    def get_data_rows(fov_data):
        return [row[1] for row in fov_data.iterrows()]

    @task
    def process_fov_row(fov_row, stats_path, proj_path, overwrite):
        wrappers.process_fov_row(fov_row, stats_path, proj_path, overwrite)

    @task(name="load_stats_fn", trigger=any_successful)
    def load_stats(fov_data, stats_paths):
        df_stats = wrappers.load_stats(fov_data, stats_paths)
        return df_stats

    @task(name="stats2plots_fn")
    def stats2plots(df_stats, save_dir):
        wrappers.stats2plots(df_stats, save_dir=save_dir)

    @task(name="im2diagnostics_fn")
    def im2diagnostics(fov_data, proj_paths, save_dir):
        wrappers.im2diagnostics(fov_data, proj_paths, save_dir=save_dir)

    with Flow("FOV_processing_pipeline") as flow:
        # for every FOV, do the processing steps
        data = save_load_data(save_dir, trim_data, overwrite)

        cell_data = data[0]
        fov_data = data[1]

        paths = get_save_paths_(save_dir, fov_data)

        summary_path = paths[0]
        stats_paths = paths[1]
        proj_paths = paths[2]
        stats_plots_dir = paths[3]
        diagnostics_dir = paths[4]

        cell_data_to_summary_table(cell_data, summary_path)

        fov_rows = get_data_rows(fov_data)

        if not use_current_results:
            process_fov_row_map = process_fov_row.map(
                fov_row=fov_rows,
                stats_path=stats_paths,
                proj_path=proj_paths,
                overwrite=overwrite,
            )
            upstream_tasks = [process_fov_row_map]
        else:
            upstream_tasks = None

        # load stats from each FOV
        df_stats = load_stats(fov_data, stats_paths, upstream_tasks=upstream_tasks)

        stats2plots(df_stats, save_dir=stats_plots_dir, upstream_tasks=[df_stats])
        im2diagnostics(
            fov_data, proj_paths, save_dir=diagnostics_dir, upstream_tasks=[df_stats]
        )

    state = flow.run(executor=executor)

    df_stats = state.result[flow.get_tasks(name="load_stats_fn")[0]].result

    # # make plots from those stats
    # wrappers.stats2plots(df_stats, save_dir=stats_plots_dir)

    # # projection paths to diagnostics path
    # wrappers.im2diagnostics(fov_data, proj_paths, save_dir=diagnostics_dir)

    log.info("Done!")

    return


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)


if __name__ == "__main__":
    main()

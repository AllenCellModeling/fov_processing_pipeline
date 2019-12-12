#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import socket
import time

from dask_jobqueue import SLURMCluster
import dask
import dask.distributed

###############################################################################

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO, format="[%(levelname)4s:%(lineno)4s %(asctime)s] %(message)s"
)

###############################################################################


def main():
    # Distributed host for

    p = argparse.ArgumentParser(prog="process", description="Process the FOV pipeline")

    p.add_argument(
        "--min_jobs", type=int, default=300, help="Minimum number of jobs to use",
    )

    p.add_argument(
        "--max_jobs", type=int, default=300, help="Maximum number of jobs to use",
    )
    p.add_argument(
        "--walltime", type=int, default=5, help="Walltime in hours",
    )
    p.add_argument(
        "--up_time", type=int, default=10, help="up time for the scheduler in hours",
    )

    args = p.parse_args()

    cluster = SLURMCluster(
        cores=2,
        memory="16GB",
        walltime="{}:00:00".format(args.walltime),
        queue="aics_cpu_general",
    )

    cluster.adapt(minimum_jobs=args.min_jobs, maximum_jobs=args.max_jobs)
    client = dask.distributed.Client(cluster)  # noqa

    connection_info = {}
    connection_info["HOSTNAME"] = socket.gethostname()
    connection_info["PORT"] = cluster.scheduler_info["address"].split(":")[-1]
    connection_info["DASHBOARD_PORT"] = cluster.scheduler_info["services"]["dashboard"]

    connection_str = (
        "ssh -A -J slurm-master -L {PORT}:{HOSTNAME}:{PORT} -L "
        "{DASHBOARD_PORT}:{HOSTNAME}:{DASHBOARD_PORT} {HOSTNAME}".format(
            **connection_info
        )
    )

    log.info(
        "In a new terimal the machine that you run the pipeline on, copy and paste the following string to forward ports to this server:"
    )
    log.info(connection_str)
    log.info(" ")
    log.info("Then use the following command to kick off your FPP jobs:")
    log.info("fpp_process --distributed 1 --port {PORT}".format(**connection_info))
    log.info(" ")
    log.info("You can see the dashboard on:")
    log.info("localhost:{PORT}".format(**connection_info))
    log.info(" ")
    log.info("Command + C will teardown the server.")

    try:
        time.sleep(args.up_time * 60 * 60)
    except KeyboardInterrupt:
        log.info("Tearing down scheduler.")
        cluster.close()


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)


if __name__ == "__main__":
    main()

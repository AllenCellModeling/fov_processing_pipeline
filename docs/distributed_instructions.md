# Remote Job Scheduling with Dask and Prefect

We are working on a better, easier, and faster implementation to set all of this up. For now, follow the steps below:

##  Run the Dask scheduler on the SLURM cluster
0. You have installed this package on the SLURM cluster (and children nodes).

1. From a terminal, connect to a CPU node on the SLURM cluster and spawn a Dask scheduler:
```bash
ssh slurm-master
```
(optional) Start a screen session
```bash
screen -S dask-scheduler
```
Get an interactive session:
```bash
srun -c 8 -p aics_cpu_general --pty bash
```

Activate your conda env if you have to, then start the scheduler:
```bash
fpp_scheduler
```
You can see all the options with 
```bash
fpp_scheduler -h
```

this should spit out some information for port forwarding, and executing the code on your main machine, and so forth:
```bash
[INFO:  67 2019-12-12 11:20:14,150] In a new terimal the machine that you run the pipeline on, copy and paste the following string to forward ports to this server:
[INFO:  69 2019-12-12 11:20:14,151] ssh -A -J slurm-master -L 44843:n86:44843 -L 8787:n86:8787 n86
[INFO:  70 2019-12-12 11:20:14,151]
[INFO:  71 2019-12-12 11:20:14,151] Then use the following command to kick off your FPP jobs:
[INFO:  72 2019-12-12 11:20:14,151] fpp_process --distributed 1 --port 44843
[INFO:  73 2019-12-12 11:20:14,151]
[INFO:  74 2019-12-12 11:20:14,151] You can see the dashboard on:
[INFO:  75 2019-12-12 11:20:14,151] localhost:44843
[INFO:  76 2019-12-12 11:20:14,151]
[INFO:  77 2019-12-12 11:20:14,151] Command + C will teardown the server.
```


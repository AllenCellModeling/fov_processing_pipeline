# FOV Processing Pipeline

[![Build Status](https://github.com/AllenCellModeling/fov_processing_pipeline/workflows/Build%20Master/badge.svg)](https://github.com/AllenCellModeling/fov_processing_pipeline/actions)
[![Documentation](https://github.com/AllenCellModeling/fov_processing_pipeline/workflows/Documentation/badge.svg)](https://gregjohnso.github.io/fov_processing_pipeline)
[![Code Coverage](https://codecov.io/gh/AllenCellModeling/fov_processing_pipeline/branch/master/graph/badge.svg)](https://codecov.io/gh/AllenCellModeling/fov_processing_pipeline)

Pipeline tools for high-throughput analysis of AICS Pipeline FOVs

---

## Features
It's a jupyter notebook for Pipeline 4 Data!
The notebook desmonstrates a proof of concept for...
* Accessing files via labkey
* Access FOV-level and Cell-level images and metadata
* Make some simple plots for data exploration

For more information see [this presentation](https://docs.google.com/presentation/d/13nFQ0KDxBti7Vgont6fcrv0gaE3NaGr-Deb-aNl2xLY/edit?usp=sharing)


## If installing *somewhere other than AICS compute-cluster infrastructure* (e.g. your local machine)
... you will need:

**AICS certificates** to be able to install the required package `lkaccess`. Instructions to setup certs on an macOS machine are as follows:

- Visit http://confluence.corp.alleninstitute.org/display/SF/Certs+on+OS+X
- Download the three .crt files, open each and keychain to System and hit 'Add' to trust
- Download `pip_conf_setup.sh` to project directory
- Install wget: `brew install wget`
- Run the downloaded setup file: `sudo bash pip_conf_setup.sh`

## Installation
**(Optional)** Make a conda environment
```
conda create --name fov_processing_pipeline python=3.7  
conda activate fov_processing_pipeline
```

**Clone the Repo**
```
git clone https://github.com/AllenCellModeling/fov_processing_pipeline.git
cd fov_processing_pipeline
```

**Install**  

```
pip install .
```
or install for development
```
pip install -e .[dev]
```

## If running locally (e.g. macOS)
(do this after the installation)  
Note: Image loading with the remotely mounting the data repository will be much slower than running from AICS compute infrastructure.

**mount the remote data repository**, which can be done on macOS with 

```
mount_smbfs //<YOUR_USERNAME>@allen/programs/allencell/data ./data/
```

To unmount when you're all done:

```
umount ./data/
```

## Running the notebook
```
jupyter notebook accessing_and_exploring_data.ipynb
```
This should start a web browser with the notebook.

## Documentation
For full package documentation please visit [AllenCellModeling.github.io/fov_processing_pipeline](https://AllenCellModeling.github.io/fov_processing_pipeline).

## Development
See [CONTRIBUTING.md](CONTRIBUTING.md) for information related to developing the code.

***Free software: Allen Institute Software License***


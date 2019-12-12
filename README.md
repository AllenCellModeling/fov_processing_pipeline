# FOV Processing Pipeline


<!--
[![Documentation](https://github.com/AllenCellModeling/fov_processing_pipeline/workflows/Documentation/badge.svg)](https://gregjohnso.github.io/fov_processing_pipeline)
-->
[![Build Status](https://github.com/AllenCellModeling/fov_processing_pipeline/workflows/Build%20Master/badge.svg)](https://github.com/AllenCellModeling/fov_processing_pipeline/actions)
[![Code Coverage](https://codecov.io/gh/AllenCellModeling/fov_processing_pipeline/branch/master/graph/badge.svg)](https://codecov.io/gh/AllenCellModeling/fov_processing_pipeline)

Pipeline tools for high-throughput analysis of AICS Pipeline FOVs

---

## Features
It's a data pipeline Pipeline 4 Data!
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
pip install .[dev]
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

## Quality Control
This pipeline include a couple simple protocols for quality control of FOV data.
* Number of z-slices in z-stacks
Not all FOV's have the same number of z-slices (or xy images) in their z-stacks. This can impact the user's ability to perform some statistical analysis on the data, such as PCA. To correct for this, the pipeline finds the most common number of z-slices, and interpolates z-stacks with more or less z-slices into a new z-stack with the same number of z-slices.
* Out-of-order z-slices
Through our data exploration using this pipeline, we discovered that some z-stacks have a z-slice from the middle of the z-stack misplced to the bottom of the z-stack. To address this, the QC processing of this pipeline removes those FOV's from the FOV dataset (i.e. it is not included in the FOV summary table used to all image analysis).

## Diagnostics and Analysis
This pipeline includes some basic image diagnostic and analysis tools to get the user started with exploring the data.
* Diagnostic images: For a quick view of FOV z-stacks, an image of the maximum project along the xy- xz- and yz- axes are rendered in a single image for each z-stacks, including all channels in different colors
* Channel intensity by z-depth: To display how structure varies across height within a z-stack, and average intensity profile as a function of z is generated for each channel, for each structure; that is, for all FOV's with the same labeled structure, the brightfield, DNA, cell membrane, and structure intensity is averaged across all FOVs at each z-height, and plotted. These intensity profiles may be plotted against the actual z-height, or can be centered relative to the maximum position of the DNA


## Documentation
For full package documentation please visit [AllenCellModeling.github.io/fov_processing_pipeline](https://AllenCellModeling.github.io/fov_processing_pipeline).

## Development
See [CONTRIBUTING.md](CONTRIBUTING.md) for information related to developing the code.

***Free software: Allen Institute Software License***


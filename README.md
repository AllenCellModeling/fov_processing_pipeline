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
* Perform simple quality control tests
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

## Quick start
To run the entire pipeline with default settings, start by following the above instructions for installation, environment setup and mounting the data. Then navigate to the repository in a terminal and simply run

```
fpp_process
```

to run the pipeline. This will include creation of FOV summary table, quality control, diagnostic image production and creation of some basic plots of z-intensity profiles of FOV channels for all structures. This runs the pipeline in the default configuration, which trims the data to only 10 FOVs per cell line, and includes only the following cell lines:
- Nuclear lamin (Lamin B1)
- Nucleolus DFC (Fibrillarin)
- Nucleolus GC (Nucleophosmin)
- Gogli (Sialytransferase 1)
- ER (Sec61 beta)
- Alpha actinin (Alpha actinin 1)
- Actomyosin bundles (Non-muscle myosin heavy chain IIB)
- Alpha tubulin

Flags can be used to overwrite existing results if you have previously run the pipeline, or to generate new plots without regenerating the data, using (respectively):
```
--overwrite
--use_current_results
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

## To do
* **Source data from Quilt rather than LabKey** <br>
The current dataset on LbaKey is not accessible to external users. Additionally, the dataset can be updated at any time without the user opting into or being aware of changes. For these reasons, this pipeline would benefit from moving to data storage through Quilt. Quilt data is accesible to anyone, regardless of affiliation within the institute, and datasets on Quilt are versioned, preventing issues with database changes breaking the pipeline without the pipeline maintainers being aware.
* **Store results such as summary statistics with AnnData rather than Pandas dataframes** <br>
The data type and process for producing statistics calculated from this pipeline require flexibility and annotations. The current formatting in Pandas is rigid in the types of data that can be added and does not carry any annotations with it. This can results in column names which are simultaneously lengthy and incomplete/inadequate to describe the stored statistics. This pipeline would be improved by implementing a tool like this to better document all stored statisticas/results/summaries in tables.


***Free software: Allen Institute Software License***


import os

import quilt3

from . import utils as data_utils

def get_data(save_dir=None, n_fovs=100, protein_list=None, overwrite=False, use_current_results=False):
    """
    Function to pull data from quilt3 and return pandas dataframes containing per-fov and per-cell info

    Parameters
    ----------
    save_dir: str
        save directory of images and metadata

    n_fovs: int
        Number of images per protein to retain

    protein_list:
        Protein names to retain

    overwrite: bool
        do we overwrite the files if they exist? (i.e. do you want to put new results in an old directory)

    use_current_results: bool
        do we skip downloading data, and just use whatever data already present on disc
    
    Returns
    -------
    cell_data: pandas.DataFrame
        Dataframe where each row corresponds to a single cell

    fov_data: pandas.DataFrame
        Dataframe where each row corresponds to an FOV
    """

    aics_pipeline = quilt3.Package.browse(
        "aics/pipeline_integrated_cell", registry="s3://allencell"
    )

    metadata_fn = aics_pipeline["metadata.csv"]

    cell_data = metadata_fn() # noqa

    cell_data, fov_data = data_utils.clean_cell_data(cell_data, protein_list=protein_list, n_fovs=n_fovs)

    if save_dir is not None:

        image_source_paths = fov_data["SourceReadPath"]

        image_target_paths = [
            "{}/{}".format(save_dir, image_source_path) for image_source_path in image_source_paths
        ]

        if not use_current_results:
            for image_source_path, image_target_path in zip(image_source_paths, image_target_paths):
                if os.path.exists(image_target_path) and not overwrite:
                    continue

                # We only do this because T4 hates our filesystem. It probably wont affect you.
                try:
                    aics_pipeline[image_source_path].fetch(image_target_path)
                except OSError:
                    pass

    return cell_data, fov_data

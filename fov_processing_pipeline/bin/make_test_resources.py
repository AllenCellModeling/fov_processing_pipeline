from fov_processing_pipeline import data
import aicsimageio
from aicsimageio import writers
import numpy as np

cell_data_parent, fov_data_parent = data.get_data()

save_dir = "./fov_processing_pipeline/tests/resources"

cell_data = cell_data_parent.iloc[0:2]

im_columns = [column for column in cell_data.columns if "ReadPath" in column]

im = aicsimageio.imread(cell_data["MembraneSegmentationReadPath"][0])

region = np.any(
    np.stack([im == cell_data["CellId"][0], im == cell_data["CellId"][1]], 0), 0
)

region_bounds = np.where(region)
region_bounds = [
    [np.min(region_bound), np.max(region_bound)] for region_bound in region_bounds
]


im_save_paths = ["{}/{}.tiff".format(save_dir, im_column) for im_column in im_columns]

for im_column, im_save_path in zip(im_columns, im_save_paths):
    im = aicsimageio.imread(cell_data[im_column][0])

    region_slice = tuple(
        [slice(0, im.shape[0]), slice(0, im.shape[1]), slice(0, im.shape[2])]
        + [
            slice(np.clip(a - 5, 0, im_dim), np.clip(b + 5, 0, im_dim))
            for (a, b), im_dim in zip(region_bounds[3:], im.shape[3:])
        ]
    )

    im_sub = im[region_slice][0]

    with writers.OmeTiffWriter(im_save_path) as writer:
        writer.save(im_sub, dimension_order="TCZYX")

    cell_data[im_column] = im_save_path

cell_data.to_csv("{}/cell_data.csv".format(save_dir))

fov_data = data._cell_data_to_fov_data(cell_data)

fov_data.to_csv("{}/fov_data.csv".format(save_dir))

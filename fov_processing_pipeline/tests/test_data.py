from .. import data
import numpy as np
import pandas as pd


def test_cell_data_to_fov_data(demo_cell_data):
    fov_data = data._cell_data_to_fov_data(demo_cell_data)

    # make sure the length of the FOV dataframe is the same length as the number of unique FOVIds
    assert len(np.unique(fov_data["FOVId"])) == len(fov_data["FOVId"])


def test_trim_data(demo_fov_data):

    protein_list = [
            "Sec61 beta",  # er
            "Fibrillarin",  # nucleolus, DFC
            "Nucleophosmin",  # nucleolus, GC
            "Sialyltransferase 1",  # golgi,
            "Alpha-actinin-1",  # alpha actinin
            "Non-muscle myosin heavy chain IIB",  # actomyosin bundles
            "Lamin B1",  # nuclear lamin
            "Alpha-tubulin",
        ]
    demo_multi_fov_data = pd.concat([demo_fov_data for i in range(len(protein_list)*2)])
    demo_multi_fov_data["ProteinDisplayName"] = protein_list*2
    demo_multi_fov_data["FOVId_rng"] = range(len(protein_list)*2)

    # check that trimming to one cell line works
    trim_df = data.trim_data(demo_multi_fov_data, ["Fibrillarin"])
    assert len(pd.unique(trim_df["ProteinDisplayName"])) == 1

    # check that trimming to a smaller number of fovs works
    trim_df = data.trim_data(demo_multi_fov_data, ["Fibrillarin"], 1)
    assert trim_df.shape[0] == 1

    # check that trimming to a cell line list that is the same as the existing list does nothing
    trim_df = data.trim_data(demo_multi_fov_data, protein_list)
    assert trim_df.shape[0] == demo_multi_fov_data.shape[0]

    # check that trimming to a cell line not in the list leaves nothing
    trim_df = data.trim_data(demo_multi_fov_data, ["Nonexistent protein name"])
    assert trim_df.shape[0] == 0


def test_trim_data_by_cellline_fov(demo_fov_data):

    protein_list = [
            "Sec61 beta",  # er
            "Fibrillarin",  # nucleolus, DFC
            "Nucleophosmin",  # nucleolus, GC
            "Sialyltransferase 1",  # golgi,
            "Alpha-actinin-1",  # alpha actinin
            "Non-muscle myosin heavy chain IIB",  # actomyosin bundles
            "Lamin B1",  # nuclear lamin
            "Alpha-tubulin",
        ]
    demo_multi_fov_data = pd.concat([demo_fov_data for i in range(len(protein_list)*2)])
    demo_multi_fov_data["ProteinDisplayName"] = protein_list*2
    demo_multi_fov_data["CellLine"] = demo_multi_fov_data["ProteinDisplayName"]
    demo_multi_fov_data["FOVId_rng"] = range(len(protein_list)*2)

    # check that trimming to a smaller number of fovs works
    trim_df = data.trim_data_by_cellline_fov_count(demo_multi_fov_data, 1)
    assert trim_df.shape[0] == len(protein_list)

    # check that trimming to a larger number of fovs leaves it untouched
    trim_df = data.trim_data_by_cellline_fov_count(demo_multi_fov_data, 5)
    assert trim_df.shape[0] == demo_multi_fov_data.shape[0]

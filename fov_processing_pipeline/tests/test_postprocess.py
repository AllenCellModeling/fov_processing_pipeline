from .. import postprocess


# make sure only fov's passing zstack order QC are present
def test_fov_qc(demo_df_stats):
    qcdf = postprocess.fov_qc(demo_df_stats)
    print(len(qcdf[~qcdf["QC"]]))
    assert len(qcdf[~qcdf["QC"]]) == 0


# make sure all FOV Ch0 zslice mean intensity lists are the same length
def test_zsize_qc(demo_df_stats):
    qcdf = postprocess.zsize_qc(demo_df_stats)
    lengths = list()
    for i in range(qcdf.shape[0]):
        lengths.append(len(qcdf.iloc[i]["Ch0_mean_by_z"]))
    assert len(set(lengths)) == 1

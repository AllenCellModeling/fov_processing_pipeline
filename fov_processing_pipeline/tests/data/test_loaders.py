import os
import pytest
import warnings

from ...data import quilt, labkey

REQUIRED_COLUMNS = ["ProteinDisplayName", "SourceReadPath", "FOVId", "CellLine"]

REQUIRED_COLUMNS_CELL = ["CellId"]


@pytest.mark.parametrize("data_loader", [quilt, labkey])
def test_get_data(tmpdir, data_loader):

    # If we're somewhere other than AICS infrastructure, labkey access doesn't work, so we just pass
    if "CI" in os.environ and os.environ["CI"] and data_loader == labkey:
        warnings.warn(
            "Ignoring this test as it works only on AICS specific infrastructure"
        )
        assert True
        return

    cell_data, fov_data = data_loader.get_data(n_fovs=0)

    assert cell_data.shape[0] == 0
    assert fov_data.shape[0] == 0

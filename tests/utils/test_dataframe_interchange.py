from datetime import datetime
import pandas as pd
import pytest
import sys
import os

try:
    import pyarrow as pa
except ImportError:
    pa = None

from altair.utils.data import to_values


def windows_has_tzdata():
    """
    From PyArrow: python/pyarrow/tests/util.py

    This is the default location where tz.cpp will look for (until we make
    this configurable at run-time)
    """
    tzdata_path = os.path.expandvars(r"%USERPROFILE%\Downloads\tzdata")
    return os.path.exists(tzdata_path)


# Skip test on Windows when the tz database is not configured.
# See https://github.com/altair-viz/altair/issues/3050.
@pytest.mark.skipif(
    sys.platform == "win32" and not windows_has_tzdata(),
    reason="Timezone database is not installed on Windows",
)
@pytest.mark.skipif(pa is None, reason="pyarrow not installed")
def test_arrow_timestamp_conversion():
    """Test that arrow timestamp values are converted to ISO-8601 strings"""
    data = {
        "date": [datetime(2004, 8, 1), datetime(2004, 9, 1), None],
        "value": [102, 129, 139],
    }
    pa_table = pa.table(data)

    values = to_values(pa_table)
    expected_values = {
        "values": [
            {"date": "2004-08-01T00:00:00.000000", "value": 102},
            {"date": "2004-09-01T00:00:00.000000", "value": 129},
            {"date": None, "value": 139},
        ]
    }
    assert values == expected_values


@pytest.mark.skipif(pa is None, reason="pyarrow not installed")
def test_duration_raises():
    td = pd.timedelta_range(0, periods=3, freq="h")
    df = pd.DataFrame(td).reset_index()
    df.columns = ["id", "timedelta"]
    pa_table = pa.table(df)
    with pytest.raises(ValueError) as e:
        to_values(pa_table)

    # Check that exception mentions the duration[ns] type,
    # which is what the pandas timedelta is converted into
    assert "duration[ns]" in e.value.args[0]

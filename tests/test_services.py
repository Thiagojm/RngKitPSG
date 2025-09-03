import os
import pandas as pd

from rngkit.services import filenames as fn
from rngkit.services import storage as st


def test_filenames_roundtrip():
    stem = fn.format_capture_name("bitb", 2048, 1, 2)
    assert "bitb" in stem and "_s2048_" in stem and "_i1" in stem and stem.endswith("_f2")
    assert fn.parse_bits(stem) == 2048
    assert fn.parse_interval(stem) == 1


def test_storage_zscore(tmp_path):
    # create a small csv
    p = tmp_path / "sample.csv"
    p.write_text("20240101T00:00:00,100\n20240101T00:00:01,110\n")
    df = st.read_csv_counts(str(p))
    out = st.add_zscore(df.copy(), 200)
    assert "z_test" in out.columns
    # write excel
    xlsx = st.write_excel_with_chart(out, str(p), 200, 1)
    assert os.path.exists(xlsx)



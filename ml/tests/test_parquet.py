import pandas as pd
import pytest

from ml.data.parquet import (
    convert_csv_directory,
    convert_csv_to_parquet,
    read_parquet,
)


def test_convert_csv_to_parquet_and_read_selected_columns(tmp_path):
    source = tmp_path / "flows.csv"
    source.write_text("Flow Duration,Label\n12,BENIGN\n34,Attack\n")
    destination = tmp_path / "parquet" / "flows.parquet"

    result = convert_csv_to_parquet(source, destination, block_size=64)

    assert result == destination
    pd.testing.assert_frame_equal(
        read_parquet(result, columns=["Label"]),
        pd.DataFrame({"Label": ["BENIGN", "Attack"]}),
    )


def test_convert_csv_directory_preserves_nested_paths(tmp_path):
    source = tmp_path / "raw"
    csv_file = source / "dataset" / "flows.csv"
    csv_file.parent.mkdir(parents=True)
    csv_file.write_text("value\n1\n")

    converted = convert_csv_directory(source, tmp_path / "processed")

    assert converted == [tmp_path / "processed" / "dataset" / "flows.parquet"]
    assert read_parquet(tmp_path / "processed" / "dataset")["value"].tolist() == [1]


def test_convert_csv_to_parquet_rejects_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError, match="CSV file not found"):
        convert_csv_to_parquet(tmp_path / "missing.csv", tmp_path / "output.parquet")


def test_convert_csv_to_parquet_accepts_scientific_notation_after_integers(tmp_path):
    source = tmp_path / "flows.csv"
    source.write_text("value\n" + "1\n" * 80 + "1.31E+07\n")
    destination = tmp_path / "flows.parquet"

    convert_csv_to_parquet(source, destination, block_size=64)

    assert read_parquet(destination)["value"].iloc[-1] == 13_100_000.0


def test_convert_csv_to_parquet_replaces_malformed_utf8(tmp_path):
    source = tmp_path / "flows.csv"
    source.write_bytes(b"Label\nWeb Attack \x96 Brute Force\n")
    destination = tmp_path / "flows.parquet"

    convert_csv_to_parquet(source, destination)

    assert read_parquet(destination)["Label"].tolist() == [
        "Web Attack \N{REPLACEMENT CHARACTER} Brute Force"
    ]


def test_convert_csv_directory_rejects_destination_inside_source(tmp_path):
    source = tmp_path / "raw"
    source.mkdir()

    with pytest.raises(ValueError, match="outside the CSV source"):
        convert_csv_directory(source, source / "parquet")


def test_convert_csv_directory_rejects_empty_source(tmp_path):
    source = tmp_path / "raw"
    source.mkdir()

    with pytest.raises(FileNotFoundError, match="No CSV files found"):
        convert_csv_directory(source, tmp_path / "processed")

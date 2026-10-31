"""Convert CICIDS2017 CSV files to Parquet and read the results for analysis."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Sequence

import pandas as pd
import pyarrow as arrow
import pyarrow.csv as csv
import pyarrow.parquet as parquet

DATA_DIR = Path(__file__).resolve().parent


def convert_csv_to_parquet(
    source: str | Path,
    destination: str | Path,
    *,
    compression: str = "snappy",
    block_size: int = 1 << 20,
) -> Path:
    """Convert one CSV to Parquet in bounded-memory batches."""
    source_path = Path(source)
    destination_path = Path(destination)

    if not source_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {source_path}")
    if source_path.resolve() == destination_path.resolve():
        raise ValueError("The Parquet destination must not be the source CSV.")
    if block_size <= 0:
        raise ValueError("block_size must be greater than zero.")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=destination_path.parent,
        suffix=".parquet",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)

    try:
        read_options = csv.ReadOptions(block_size=block_size)
        reader = csv.open_csv(source_path, read_options=read_options)
        # CICIDS columns can contain scientific notation after integer-looking
        # values, so normalize inferred integer columns before streaming batches.
        column_types = {
            field.name: arrow.float64()
            for field in reader.schema
            if arrow.types.is_integer(field.type)
        }
        reader = csv.open_csv(
            source_path,
            read_options=read_options,
            convert_options=csv.ConvertOptions(
                check_utf8=False,
                column_types=column_types,
            ),
        )
        with parquet.ParquetWriter(
            temporary_path,
            reader.schema,
            compression=compression,
        ) as writer:
            for batch in reader:
                columns = []
                for column in batch.columns:
                    if arrow.types.is_string(column.type):
                        values = column.cast(arrow.binary()).to_pylist()
                        column = arrow.array(
                            [
                                value.decode("utf-8", errors="replace")
                                if value is not None
                                else None
                                for value in values
                            ],
                            type=arrow.string(),
                        )
                    columns.append(column)
                batch = arrow.RecordBatch.from_arrays(columns, schema=batch.schema)
                writer.write_batch(batch)
        temporary_path.replace(destination_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    return destination_path


def convert_csv_directory(
    source: str | Path,
    destination: str | Path,
    *,
    compression: str = "snappy",
    block_size: int = 1 << 20,
) -> list[Path]:
    """Convert all CSV files recursively, preserving their directory structure."""
    source_dir = Path(source)
    destination_dir = Path(destination)

    if not source_dir.is_dir():
        raise NotADirectoryError(f"CSV source directory not found: {source_dir}")
    if destination_dir.resolve().is_relative_to(source_dir.resolve()):
        raise ValueError("The Parquet destination must be outside the CSV source.")

    csv_files = sorted(source_dir.rglob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {source_dir}")

    converted_files = []
    for csv_file in csv_files:
        relative_path = csv_file.relative_to(source_dir).with_suffix(".parquet")
        converted_files.append(
            convert_csv_to_parquet(
                csv_file,
                destination_dir / relative_path,
                compression=compression,
                block_size=block_size,
            )
        )

    return converted_files


def read_parquet(
    path: str | Path,
    *,
    columns: Sequence[str] | None = None,
    filters: list[tuple[str, str, object]] | None = None,
) -> pd.DataFrame:
    """Read a Parquet file or dataset into a pandas DataFrame."""
    return pd.read_parquet(
        path,
        engine="pyarrow",
        columns=columns,
        filters=filters,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert CICIDS2017 CSV files to Parquet."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DATA_DIR / "raw",
        help="CSV file tree to convert (default: ml/data/raw).",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=DATA_DIR / "processed" / "parquet",
        help="Output directory (default: ml/data/processed/parquet).",
    )
    parser.add_argument(
        "--compression",
        choices=("snappy", "gzip", "brotli", "lz4", "zstd", "uncompressed"),
        default="snappy",
        help="Parquet compression codec (default: snappy).",
    )
    parser.add_argument(
        "--block-size",
        type=int,
        default=1 << 20,
        help="CSV input block size in bytes (default: 1048576).",
    )
    args = parser.parse_args(argv)

    converted_files = convert_csv_directory(
        args.source,
        args.destination,
        compression=args.compression,
        block_size=args.block_size,
    )
    for converted_file in converted_files:
        print(converted_file)
    print(f"Converted {len(converted_files)} CSV file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

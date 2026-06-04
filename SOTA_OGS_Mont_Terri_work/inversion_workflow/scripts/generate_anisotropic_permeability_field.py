#!/usr/bin/env python3
"""Generate a reproducible anisotropic permeability tensor field on an OGS VTU mesh."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import meshio
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Write a 2D anisotropic permeability tensor field as OGS MeshElement "
            "cell data. The tensor component order is k_xx k_xy k_yx k_yy."
        )
    )
    parser.add_argument("--config", type=Path, help="Optional JSON config file.")
    parser.add_argument("--input", type=Path, help="Input VTU mesh.")
    parser.add_argument("--output", type=Path, help="Output VTU mesh.")
    parser.add_argument("--field-name", default="k_i_rd", help="Output tensor field name.")
    parser.add_argument("--seed", type=int, default=20260528)
    parser.add_argument("--theta-deg", type=float, default=144.0)
    parser.add_argument("--anisotropy-ratio", type=float, default=2.5)
    parser.add_argument("--mean-k-ref", type=float, default=6.32e-20)
    parser.add_argument("--log-sigma", type=float, default=0.5)
    parser.add_argument("--corr-length", type=float, default=0.6)
    parser.add_argument("--n-features", type=int, default=96)
    parser.add_argument("--min-k", type=float, default=1.0e-22)
    parser.add_argument("--max-k", type=float, default=1.0e-13)
    parser.add_argument(
        "--porosity",
        type=float,
        default=None,
        help="Optional constant porosity field to write as n_rd.",
    )
    args = parser.parse_args()

    if args.config:
        data = json.loads(args.config.read_text(encoding="utf-8"))
        key_map = {
            "input_mesh": "input",
            "output_mesh": "output",
            "field_name": "field_name",
            "seed": "seed",
            "theta_deg": "theta_deg",
            "anisotropy_ratio": "anisotropy_ratio",
            "mean_k_ref": "mean_k_ref",
            "log_sigma": "log_sigma",
            "corr_length": "corr_length",
            "n_features": "n_features",
            "min_k": "min_k",
            "max_k": "max_k",
            "porosity": "porosity",
        }
        for json_key, arg_key in key_map.items():
            if json_key in data and getattr(args, arg_key) is None:
                setattr(args, arg_key, data[json_key])
            elif json_key in data and arg_key not in {"input", "output"}:
                default = parser.get_default(arg_key)
                if getattr(args, arg_key) == default:
                    setattr(args, arg_key, data[json_key])

    if args.input is None or args.output is None:
        raise SystemExit("--input and --output are required, either directly or via --config")

    args.input = Path(args.input)
    args.output = Path(args.output)
    return args


def block_centroids(points: np.ndarray, cell_block: meshio.CellBlock) -> np.ndarray:
    return points[cell_block.data].mean(axis=1)


def correlated_standard_field(
    xy: np.ndarray,
    rng: np.random.Generator,
    corr_length: float,
    n_features: int,
) -> np.ndarray:
    if n_features < 1:
        raise ValueError("n_features must be positive")
    if corr_length <= 0:
        raise ValueError("corr_length must be positive")

    centered = xy - xy.mean(axis=0, keepdims=True)
    omega = rng.normal(scale=1.0 / corr_length, size=(n_features, 2))
    phase = rng.uniform(0.0, 2.0 * math.pi, size=n_features)
    weights = rng.normal(size=n_features)
    values = np.cos(centered @ omega.T + phase) @ weights
    values -= values.mean()
    std = values.std()
    if std == 0:
        return values
    return values / std


def tensor_components(k_perp: np.ndarray, ratio: float, theta_deg: float) -> np.ndarray:
    if ratio <= 0:
        raise ValueError("anisotropy ratio must be positive")

    theta = math.radians(theta_deg)
    e_parallel = np.array([math.cos(theta), math.sin(theta)])
    e_perp = np.array([-math.sin(theta), math.cos(theta)])
    k_parallel = ratio * k_perp

    tensors = (
        k_parallel[:, None, None] * np.outer(e_parallel, e_parallel)
        + k_perp[:, None, None] * np.outer(e_perp, e_perp)
    )
    return tensors.reshape((-1, 4))


def main() -> None:
    args = parse_args()
    rng = np.random.default_rng(args.seed)
    mesh = meshio.read(args.input)

    cell_data: dict[str, list[Any]] = {
        name: [np.array(block_values) for block_values in values]
        for name, values in mesh.cell_data.items()
    }

    tensor_blocks = []
    k_mag_blocks = []
    ratio_blocks = []
    theta_blocks = []
    porosity_blocks = [] if args.porosity is not None else None

    for block in mesh.cells:
        centroids = block_centroids(mesh.points, block)
        xy = centroids[:, :2]
        z = correlated_standard_field(xy, rng, args.corr_length, args.n_features)
        k_ref = args.mean_k_ref * np.exp(args.log_sigma * z)
        k_ref = np.clip(k_ref, args.min_k, args.max_k)

        # k_ref is the geometric mean sqrt(k_parallel * k_perp).
        k_perp = k_ref / math.sqrt(args.anisotropy_ratio)
        tensor_blocks.append(tensor_components(k_perp, args.anisotropy_ratio, args.theta_deg))
        k_mag_blocks.append(k_ref.reshape((-1, 1)))
        ratio_blocks.append(np.full((len(k_ref), 1), args.anisotropy_ratio))
        theta_blocks.append(np.full((len(k_ref), 1), args.theta_deg))
        if porosity_blocks is not None:
            porosity_blocks.append(np.full((len(k_ref), 1), args.porosity))

    cell_data[args.field_name] = tensor_blocks
    cell_data["k_mag_rd"] = k_mag_blocks
    cell_data["k_anisotropy_ratio_rd"] = ratio_blocks
    cell_data["k_theta_deg_rd"] = theta_blocks
    if porosity_blocks is not None:
        cell_data["n_rd"] = porosity_blocks

    args.output.parent.mkdir(parents=True, exist_ok=True)
    meshio.write_points_cells(
        args.output,
        mesh.points,
        mesh.cells,
        point_data=mesh.point_data,
        cell_data=cell_data,
        field_data=mesh.field_data,
    )

    flat_k = np.vstack(k_mag_blocks).ravel()
    print(f"wrote {args.output}")
    print(f"{args.field_name}: tensor components k_xx k_xy k_yx k_yy")
    print(f"k_mag_rd range: {flat_k.min():.6e} .. {flat_k.max():.6e} m^2")
    print(f"theta_deg: {args.theta_deg:g}; anisotropy_ratio: {args.anisotropy_ratio:g}")


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Synthetic Thermogram Dataset Generator.

Generates systematic LFMT thermogram sequences across defect configurations
and saves standardized NPZ tensors, metadata JSON, and ground-truth mask NPY files.
"""

import argparse
from pathlib import Path
from rich.console import Console
from rich.progress import Progress

from lfmt.config import load_config
from lfmt.simulation import get_simulation_backend
from lfmt.camera import VirtualIRCamera
from lfmt.noise import apply_noise_pipeline


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic LFMT dataset.")
    parser.add_argument("--config", type=str, default="configs/quick.yaml", help="Base config YAML")
    parser.add_argument("--out-dir", type=str, default="data/generated", help="Dataset destination folder")
    parser.add_argument("--quick", action="store_true", help="Quick mode (2 diameters, 2 depths, clean + 25dB)")
    args = parser.parse_args()

    console = Console()
    console.print("[bold cyan]LFMT Dataset Generator[/bold cyan]")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.quick:
        diameters = [6.0, 10.0]
        depths = [0.4, 0.8]
        noises = [None, 25.0]
    else:
        diameters = [4.0, 6.0, 8.0, 10.0, 12.0]
        depths = [0.2, 0.4, 0.6, 0.8, 1.0]
        noises = [None, 30.0, 25.0, 20.0]

    base_cfg = load_config(args.config)
    total_cases = len(diameters) * len(depths) * len(noises)
    console.print(f"Generating {total_cases} synthetic test cases...")

    case_idx = 1
    backend = get_simulation_backend(base_cfg.simulation.backend)
    camera = VirtualIRCamera(base_cfg.camera)

    with Progress() as progress:
        task = progress.add_task("[green]Generating dataset...", total=total_cases)

        for d in diameters:
            for z in depths:
                # Configure simulation case
                cfg = load_config(args.config)
                cfg.geometry.inclusion.diameter_mm = float(d)
                cfg.geometry.inclusion.depth_mm = float(z)

                sim_res = backend.run(cfg)
                capture_clean = camera.capture(sim_res)

                for n_snr in noises:
                    case_id = f"case_{case_idx:04d}"
                    case_cfg = load_config(args.config)
                    case_cfg.geometry.inclusion.diameter_mm = float(d)
                    case_cfg.geometry.inclusion.depth_mm = float(z)
                    case_cfg.noise.snr_db = n_snr

                    noisy_tensor = apply_noise_pipeline(capture_clean.thermograms, case_cfg.noise)
                    capture_noisy = capture_clean
                    capture_noisy.thermograms = noisy_tensor

                    case_dir = capture_noisy.save_case(out_dir, case_id=case_id)
                    case_idx += 1
                    progress.update(task, advance=1)

    console.print(f"[bold green]Dataset successfully generated in: {out_dir}[/bold green]")


if __name__ == "__main__":
    main()

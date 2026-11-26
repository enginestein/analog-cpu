"""Command-line entry point: ``python -m analog_cpu``."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from . import __version__
from .verify import DEFAULT_ROOT, summarize, verify_all


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m analog_cpu",
        description="Check Qucs-S CMOS gate simulations against truth tables.",
    )
    parser.add_argument(
        "--root",
        default=str(DEFAULT_ROOT),
        help="directory containing CMOS_*.dat.ngspice (default: repository root)",
    )
    parser.add_argument("--vdd", type=float, default=5.0, help="supply voltage in volts")
    parser.add_argument(
        "--min-samples",
        type=int,
        default=8,
        help="minimum samples in a stable input window (default: 8)",
    )
    parser.add_argument(
        "--tail-fraction",
        type=float,
        default=0.3,
        help="fraction of each stable window used to vote on the output",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail on known issues and on incomplete stimulus coverage",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)

    reports = verify_all(
        args.root,
        vdd=args.vdd,
        min_samples=args.min_samples,
        tail_fraction=args.tail_fraction,
    )

    if args.json:
        payload = {
            "strict": args.strict,
            "reports": [asdict(report) for report in reports],
            "ok": all(
                report.ok
                if not args.strict
                else report.status == "pass"
                for report in reports
            ),
        }
        print(json.dumps(payload, indent=2))
        return 0 if payload["ok"] else 1

    return 0 if summarize(reports, strict=args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())

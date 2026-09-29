"""
Automated Route Smoke Test for LFMT Web Portal.
Tests all application routes against a specified BASE_URL (Local or Hosted Vercel).
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
import urllib.error

ROUTES = [
    "/",
    "/simulate",
    "/conference",
    "/explorer",
    "/thermograms",
    "/results",
    "/results/depth",
    "/results/diameter",
    "/results/noise",
    "/sensitivity",
    "/validation",
    "/methodology",
    "/materials",
    "/about",
    "/qr",
]


def test_routes(base_url: str) -> bool:
    base_url = base_url.rstrip("/")
    print(f"==================================================")
    print(f"Testing LFMT Web Portal Routes against: {base_url}")
    print(f"==================================================")

    all_passed = True
    for route in ROUTES:
        url = f"{base_url}{route}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "LFMT-Route-Verifier/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = resp.getcode()
                if code == 200:
                    print(f"  [PASS] {code} {route}")
                else:
                    print(f"  [WARN] {code} {route}")
                    all_passed = False
        except urllib.error.HTTPError as e:
            print(f"  [FAIL] {e.code} {route} - {e.reason}")
            all_passed = False
        except Exception as e:
            print(f"  [ERR ] {route} - {e}")
            all_passed = False

    print("--------------------------------------------------")
    if all_passed:
        print(f"ALL {len(ROUTES)} ROUTES RETURNED HTTP 200 OK")
    else:
        print(f"SOME ROUTES FAILED")
    return all_passed


def main() -> int:
    parser = argparse.ArgumentParser(description="Test web routes")
    parser.add_argument("--base-url", default="http://localhost:3000", help="Base URL to test (default: http://localhost:3000)")
    args = parser.parse_args()

    success = test_routes(args.base_url)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

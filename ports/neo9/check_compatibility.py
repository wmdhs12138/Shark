#!/usr/bin/env python3
"""Report device/profile compatibility without running a root backend."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import BadZipFile, ZipFile


def device_properties():
    getprop = shutil.which("getprop")
    names = {
        "model": "ro.product.model",
        "device": "ro.product.device",
        "manufacturer": "ro.product.manufacturer",
        "android_version": "ro.build.version.release",
        "system_version": "ro.build.display.id",
        "security_patch": "ro.build.version.security_patch",
        "abi": "ro.product.cpu.abi",
    }
    result = {"kernel_release": os.uname().release}
    for name, prop in names.items():
        result[name] = None
        if getprop:
            try:
                process = subprocess.run(
                    [getprop, prop], capture_output=True, text=True, timeout=2
                )
                if process.returncode == 0:
                    result[name] = process.stdout.strip() or None
            except (OSError, subprocess.TimeoutExpired):
                pass
    return result


def shark_profile_match(release):
    root = Path(__file__).resolve().parents[2]
    source = root / "app/app/src/main/java/com/shark/kty/MainActivity.kt"
    text = source.read_text(encoding="utf-8")
    match = re.search(r"PROFILE_BY_RELEASE[^=]*=\s*mapOf\((.*?)\n\s*\)", text, re.S)
    if not match:
        raise ValueError("Cannot locate Shark's complete kernel profile mapping")
    profiles = re.findall(r'"([^"\n]+)"\s+to\s+ExploitKind\.\w+', match.group(1))
    if not profiles:
        raise ValueError("Shark's kernel profile mapping is empty or unrecognized")
    return release in profiles


def inspect_timer(apk, release):
    entry = f"assets/kernel_profiles/{release}.conf"
    with apk.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    result = {
        "apk_sha256": digest,
        "expected_entry": entry,
        "matching_entry_present": False,
        "declared_release_matches": None,
    }
    with ZipFile(apk) as archive:
        try:
            info = archive.getinfo(entry)
        except KeyError:
            return result
        result["matching_entry_present"] = True
        if info.file_size > 65536:
            raise ValueError("Profile exceeds the 64 KiB metadata inspection limit")
        text = archive.read(entry).decode("utf-8")
        declared = None
        for line in text.splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() == "release":
                declared = value.strip().strip("\"'")
                break
        result["declared_release_matches"] = (
            declared == release if declared is not None else None
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timer-apk", type=Path, help="Existing local Timer APK")
    args = parser.parse_args()
    device = device_properties()
    report = {
        "device": device,
        "check_mode": "read_only",
        "exploit_executed": False,
        "root_support_verified": False,
    }
    try:
        report["shark_profile_match"] = shark_profile_match(device["kernel_release"])
        if args.timer_apk:
            report["timer"] = inspect_timer(args.timer_apk, device["kernel_release"])
    except (OSError, ValueError, BadZipFile, UnicodeError) as error:
        report["inspection_error"] = str(error)
        json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
        print()
        return 1
    report["status"] = (
        "profile_present_unverified"
        if report["shark_profile_match"]
        else "unsupported_by_current_shark_profile_map"
    )
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

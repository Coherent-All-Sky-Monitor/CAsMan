#!/usr/bin/env python3
"""
Test script for scanning and assembly duplicate prevention.
"""

import subprocess
import sys


def test_duplicate_prevention():
    """Test that duplicate scanning prevention works."""

    print("Testing duplicate scanning prevention...")

    # First, try to use ANT-P1-00001 which is already used
    cmd = [sys.executable, "scripts/scan_and_assemble.py"]

    # Input: Start with ANTENNA, manual entry, pol 1, part number 1
    input_data = "0\n2\n1\n1\nn\n"

    try:
        result = subprocess.run(
            cmd, input=input_data, text=True, capture_output=True, timeout=10
        )

        output = result.stdout
        print("STDOUT:")
        print(output)

        if "has already been scanned" in output:
            print("✅ SUCCESS: Duplicate scanning prevention is working!")
        else:
            print("❌ FAILED: Duplicate scanning not detected")

    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT: Script took too long")
    except Exception as e:
        print(f"❌ ERROR: {e}")


def test_connection_with_fresh_parts():
    """Test connection with fresh parts."""

    print("\nTesting connection with fresh parts...")

    # Input: Start with ANTENNA, manual entry, pol 1, part number 3,
    #        then LNA manual entry, pol 1, part number 3
    cmd = [sys.executable, "scripts/scan_and_assemble.py"]
    input_data = "0\n2\n1\n3\n2\n1\n3\nn\n"

    try:
        result = subprocess.run(
            cmd, input=input_data, text=True, capture_output=True, timeout=15
        )

        output = result.stdout
        print("STDOUT:")
        print(output)

        if "Successfully recorded connection" in output:
            print("✅ SUCCESS: Fresh parts connection working!")
        elif "has already been scanned" in output:
            print("ℹ️  INFO: Parts already used, which is expected behavior")
        else:
            print("❌ FAILED: Connection not successful")
            print("STDERR:")
            print(result.stderr)

    except subprocess.TimeoutExpired:
        print("❌ TIMEOUT: Script took too long")
    except Exception as e:
        print(f"❌ ERROR: {e}")


if __name__ == "__main__":
    test_duplicate_prevention()
    test_connection_with_fresh_parts()

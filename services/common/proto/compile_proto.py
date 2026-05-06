#!/usr/bin/env python3
"""Protocol Buffer 编译脚本"""

import subprocess
import sys
from pathlib import Path

PROTO_DIR = Path(__file__).parent.parent / "proto"
OUTPUT_DIR = Path(__file__).parent


def compile_proto_files():
    proto_files = list(PROTO_DIR.glob("*.proto"))

    if not proto_files:
        print(f"No proto files found in {PROTO_DIR}")
        return

    for proto_file in proto_files:
        print(f"Compiling {proto_file.name}...")

        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={PROTO_DIR}",
            f"--python_out={OUTPUT_DIR}",
            f"--grpc_python_out={OUTPUT_DIR}",
            str(proto_file),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error compiling {proto_file.name}:")
            print(result.stderr)
            sys.exit(1)

        print(f"  -> Generated {proto_file.stem}_pb2.py and {proto_file.stem}_pb2_grpc.py")


if __name__ == "__main__":
    compile_proto_files()
    print("Proto compilation complete!")

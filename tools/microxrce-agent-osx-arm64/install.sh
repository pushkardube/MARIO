#!/usr/bin/env bash
# Install pre-built MicroXRCEAgent v2.3.0 (Apple Silicon)
# Built on macOS 15.7.3 / Apple clang 17.0.0 / arm64
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
sudo cp "$DIR/MicroXRCEAgent" /usr/local/bin/
sudo cp "$DIR/libmicroxrcedds_agent.2.3.0.dylib" /usr/local/lib/
sudo cp "$DIR/libfastcdr.1.0.26.dylib" /usr/local/lib/
sudo ln -sf /usr/local/lib/libmicroxrcedds_agent.2.3.0.dylib /usr/local/lib/libmicroxrcedds_agent.2.3.dylib
sudo ln -sf /usr/local/lib/libmicroxrcedds_agent.2.3.0.dylib /usr/local/lib/libmicroxrcedds_agent.dylib
sudo ln -sf /usr/local/lib/libfastcdr.1.0.26.dylib /usr/local/lib/libfastcdr.dylib
echo "MicroXRCEAgent v2.3.0 installed to /usr/local/bin/"

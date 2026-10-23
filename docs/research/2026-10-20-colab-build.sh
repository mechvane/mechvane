#!/bin/bash
# Cold SolidCraft build timing on a Colab VM.
exec > /content/w/log.txt 2>&1
set -x
nproc; free -g | head -2; df -h /content | tail -1
t0=$(date +%s)
apt-get -qq update && apt-get -qq install -y libxkbcommon-dev libwayland-dev libudev-dev libssl-dev pkg-config > /dev/null
curl -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-toolchain stable -c clippy,rustfmt > /dev/null
. $HOME/.cargo/env; rustc --version
t1=$(date +%s); echo "SETUP_S=$((t1-t0))"
git clone -q --depth 1 https://github.com/tangency-labs/solidcraft /content/w/solidcraft
cd /content/w/solidcraft && git log -1 --format="%h %ad"
t2=$(date +%s); echo "CLONE_S=$((t2-t1))"
cargo build --release -p solidcraft-cli -q; echo "BUILD_CLI_RC=$?"
t3=$(date +%s); echo "BUILD_CLI_S=$((t3-t2))"
touch crates/doc/src/lib.rs; cargo build --release -p solidcraft-cli -q; echo "INCR_RC=$?"
t4=$(date +%s); echo "INCR_DOC_S=$((t4-t3))"
timeout 5400 cargo xtask ci; echo "CI_RC=$?"
t5=$(date +%s); echo "CI_S=$((t5-t4))"
du -sh target
echo DONE

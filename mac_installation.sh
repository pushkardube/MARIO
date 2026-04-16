#!/usr/bin/env bash
# MARIO — macOS installation script (Rerun + micro-ROS over USB)
# Tested on macOS with miniforge / conda.

set -e

red=$(tput setaf 1)
green=$(tput setaf 2)
blue=$(tput setaf 4)
reset=$(tput sgr0)

banner() { echo "${blue}=======================${reset}"; echo "$1"; echo "${blue}=======================${reset}"; }

_shell_=$(basename "$SHELL")   # zsh or bash — used for rc file name

# ── 1. ESP-IDF ────────────────────────────────────────────────────────────────
banner "Checking ESP-IDF"

if [ -d "$HOME/esp/esp-idf" ]; then
    echo "${red}ESP-IDF already installed — skipping${reset}"
else
    if ! brew --version &>/dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    brew install git cmake ninja dfu-util python3

    mkdir -p "$HOME/esp"
    cd "$HOME/esp"
    git clone -b release/v5.1 --recursive https://github.com/espressif/esp-idf.git
    cd esp-idf
    ./install.sh esp32
    . "$HOME/esp/esp-idf/export.sh"

    echo "alias get_idf='. \$HOME/esp/esp-idf/export.sh'" >> "$HOME/.${_shell_}rc"
    echo "${green}ESP-IDF installed${reset}"
fi

# ── 2. Clone MARIO ────────────────────────────────────────────────────────────
banner "Checking MARIO repository"

if [ ! -d "$HOME/MARIO" ]; then
    cd "$HOME"
    git clone -b mac/rerun --recursive https://github.com/SRA-VJTI/MARIO.git
    echo "${green}MARIO cloned${reset}"
else
    echo "${red}MARIO already exists — skipping clone${reset}"
fi

# ── 3. Miniforge ──────────────────────────────────────────────────────────────
banner "Checking Miniforge"

if ! command -v conda &>/dev/null; then
    echo "Installing Miniforge..."
    curl -fsSL "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" -o miniforge.sh
    chmod +x miniforge.sh
    ./miniforge.sh -b
    rm miniforge.sh
    export PATH="$HOME/miniforge3/bin:$PATH"
    conda init "$_shell_"
    echo "${green}Miniforge installed${reset}"
    echo "Re-open your terminal after this script finishes, then re-run if needed."
fi

# Find conda wherever it is installed
CONDA_BASE=$(conda info --base 2>/dev/null || echo "$HOME/miniforge3")
export PATH="$CONDA_BASE/bin:$PATH"
source "$CONDA_BASE/etc/profile.d/conda.sh" 2>/dev/null || true

# ── 4. ros2_mario conda environment ──────────────────────────────────────────
banner "Setting up ros2_mario conda environment"

if conda info --envs | grep -q "^ros2_mario"; then
    echo "${red}ros2_mario env already exists — skipping create${reset}"
else
    conda create -n ros2_mario -y
fi

conda activate ros2_mario

conda config --env --add channels conda-forge
conda config --env --add channels robostack-staging
conda config --env --remove channels defaults 2>/dev/null || true

# ── 5. ROS 2 Humble ───────────────────────────────────────────────────────────
banner "Installing ROS 2 Humble"

mamba install -n ros2_mario -y \
    ros-humble-desktop \
    colcon-common-extensions \
    ros-humble-kdl-parser

# Force-reinstall urdfdom_headers so its cmake config files are written to disk.
# On a fresh conda install the cmake config is sometimes missing despite the package
# being listed as installed, which breaks simulation_mujoco's cmake configuration.
mamba install -n ros2_mario -y --force-reinstall urdfdom_headers

# ── 6. Python packages ────────────────────────────────────────────────────────
banner "Installing Python packages"

conda run -n ros2_mario pip install \
    rerun-sdk \
    trimesh \
    numpy \
    mujoco \
    pybullet \
    pyserial

# ── 7. Shell activation ───────────────────────────────────────────────────────
if ! grep -q "conda activate ros2_mario" "$HOME/.${_shell_}rc" 2>/dev/null; then
    echo "" >> "$HOME/.${_shell_}rc"
    echo "# MARIO — activate ROS 2 environment" >> "$HOME/.${_shell_}rc"
    echo "conda activate ros2_mario" >> "$HOME/.${_shell_}rc"
fi

# ── 8. ROS 2 workspace ────────────────────────────────────────────────────────
banner "Setting up ROS 2 workspace"

# Workspace lives outside the repo so build/install/log don't pollute the source.
# Packages are symlinked — Python edits take effect without rebuilding.
mkdir -p "$HOME/ros2_mario_ws/src"
cd "$HOME/ros2_mario_ws/src"

for pkg in 1_chatter_listener 2_simulation_dh 3_simulation_rerun; do
    if [ ! -L "$pkg" ]; then
        ln -s "$HOME/MARIO/$pkg" "$pkg"
        echo "  linked: $pkg"
    else
        echo "  already linked: $pkg"
    fi
done

# Ensure all Python scripts and launch files are executable (required for ros2 run on Mac).
# Also fix any remaining #!/usr/bin/python3 shebangs to #!/usr/bin/env python3.
# Prune build/install/log to avoid chasing broken symlinks from old colcon installs.
find "$HOME/MARIO" \
    -not -path "$HOME/MARIO/build/*" \
    -not -path "$HOME/MARIO/install/*" \
    -not -path "$HOME/MARIO/log/*" \
    \( -path "*/scripts/*.py" -o -path "*/launch/*.py" \) \
    -exec chmod +x {} \+ \
    -exec sed -i '' '1s|#!/usr/bin/python3|#!/usr/bin/env python3|' {} \;

cd "$HOME/ros2_mario_ws"

# Remove build dirs for packages that were renamed or had failed cmake runs.
# Stale cmake state causes "Makefile: No such file or directory" on the next build.
for stale_pkg in simulation_rviz; do
    rm -rf build/"$stale_pkg" install/"$stale_pkg"
done
for pkg_build_dir in build/*/; do
    rc_file="${pkg_build_dir}colcon_build.rc"
    if [ -f "$rc_file" ] && [ "$(cat "$rc_file" | tr -d '[:space:]')" != "0" ]; then
        echo "  Cleaning failed build state: $(basename "$pkg_build_dir")"
        rm -rf "$pkg_build_dir"
    fi
done

conda run -n ros2_mario colcon build --symlink-install

if ! grep -q "ros2_mario_ws/install/setup" "$HOME/.${_shell_}rc" 2>/dev/null; then
    echo "" >> "$HOME/.${_shell_}rc"
    echo "# MARIO — source ROS 2 workspace" >> "$HOME/.${_shell_}rc"
    echo "source \$HOME/ros2_mario_ws/install/setup.sh" >> "$HOME/.${_shell_}rc"
fi

echo "${green}Workspace built${reset}"

# ── 9. micro-ROS Agent (native, wired USB) ────────────────────────────────────
banner "Installing micro-ROS Agent (native)"

brew install asio tinyxml2 openssl

if [ ! -d "$HOME/Micro-XRCE-DDS-Agent" ]; then
    git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git "$HOME/Micro-XRCE-DDS-Agent"
fi

cd "$HOME/Micro-XRCE-DDS-Agent"
cmake -Bbuild -DCMAKE_BUILD_TYPE=Release \
    -DOPENSSL_ROOT_DIR="$(brew --prefix openssl)"
cmake --build build --parallel
sudo cmake --install build

if ! grep -q "alias microros_agent" "$HOME/.${_shell_}rc" 2>/dev/null; then
    echo "" >> "$HOME/.${_shell_}rc"
    echo "# MARIO — start micro-ROS agent over wired USB" >> "$HOME/.${_shell_}rc"
    echo "alias microros_agent='MicroXRCEAgent serial --dev \$(ls /dev/cu.usbserial-* /dev/cu.SLAB_USBtoUART 2>/dev/null | head -1) -b 115200'" >> "$HOME/.${_shell_}rc"
fi

echo "${green}MicroXRCEAgent installed${reset}"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "${green}=======================${reset}"
echo "Installation complete."
echo "Restart your terminal, then:"
echo "  cd ~/ros2_mario_ws && source install/setup.sh"
echo "  ros2 run simulation_rerun rerun.py"
echo "  ros2 run chatter_listener talker.py"
echo ""
echo "To start the micro-ROS agent:  microros_agent"
echo "  (or: MicroXRCEAgent serial --dev /dev/cu.usbserial-XXXX -b 115200)"
echo "${green}=======================${reset}"

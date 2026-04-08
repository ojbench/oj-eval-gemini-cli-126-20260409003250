#!/bin/bash

# 脚本功能：
# 1. 检查并安装 python3-pip
# 2. 检查并创建虚拟环境 (venv)
# 3. 激活虚拟环境并安装所需的 Python 库
# 4. 使用 CMake 和 Make 编译项目
# 5. 解析脚本参数 [filename] 和 [--standard-visualizer]
# 6. 根据参数执行不同的命令

# 定义颜色变量
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

set -e  # 如果任何命令失败，则退出脚本

# 函数：检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 函数：显示使用说明
usage() {
    echo -e "${RED}用法: $0 [filename] [--standard-visualizer]? ${NC}"
    exit 1
}

# 解析参数
if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    echo -e "${RED}参数数量不正确。${NC}"
    usage
fi

FILENAME="$1"

if [ $# -eq 2 ]; then
    if [ "$2" == "--standard-visualizer" ]; then
        VISUALIZER=true
    else
        echo -e "${RED}未知的参数: $2${NC}"
        usage
    fi
else
    VISUALIZER=false
fi

echo -e "${BLUE}Filename: $FILENAME${NC}"
echo -e "${BLUE}Standard Visualizer: $VISUALIZER${NC}"

# 检查并安装 python3-pip
if command_exists pip3; then
    echo -e "${GREEN}检测到python3-pip${NC}"
else
    # 更新包列表
    echo -e "${GREEN}更新包列表...${NC}"
    sudo apt update
    echo -e "${GREEN}pip3 未安装，正在安装...${NC}"
    sudo apt install -y python3-pip
fi

if ! dpkg -s python3-venv >/dev/null 2>&1; then
    echo -e "${GREEN}python3-venv 未安装，正在安装...${NC}"
    sudo apt update
    sudo apt install -y python3-venv
fi

# 定义虚拟环境目录
VENV_DIR="./venv"

# 检查并创建虚拟环境
if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}虚拟环境 '$VENV_DIR' 已存在。${NC}"
else
    echo -e "${GREEN}虚拟环境 '$VENV_DIR' 不存在，正在创建...${NC}"
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}虚拟环境已创建。${NC}"
fi

# 激活虚拟环境
echo -e "${GREEN}激活虚拟环境...${NC}"
source "$VENV_DIR/bin/activate"

# 定义需要检查和安装的 Python 包（系统自带的包除外）
REQUIRED_PYTHON_PACKAGES=("pygame")

# 检查并安装 Python 包
for package in "${REQUIRED_PYTHON_PACKAGES[@]}"; do
    if pip show "$package" >/dev/null 2>&1; then
        echo -e "${GREEN}检测到Python包'$package'${NC}"
    else
        echo -e "${GREEN}Python包 '$package' 未安装，正在安装...${NC}"
        pip install "$package"
    fi
done

if [ "$VISUALIZER" = true ]; then
    python3 resources/visualizer.py ./resources/GameofLife "$FILENAME"
    exit 0
fi

# 创建并进入构建目录
BUILD_DIR="build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# 运行 CMake 配置
echo -e "${GREEN}配置CMake...${NC}"
cmake .. -DCompileOpt=ON

# 编译项目
echo -e "${GREEN}编译项目...${NC}"
make

cd ..

if [ ! -f build/GameofLife ]; then
  echo -e "${RED}未找到可执行文件，请确认目录和文件正确${NC}"
  exit 1
fi

python3 resources/visualizer.py ./build/GameofLife "$FILENAME"

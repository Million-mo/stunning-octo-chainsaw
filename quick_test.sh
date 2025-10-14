#!/bin/bash
# 快速测试脚本 - 验证 ArkTS 符号表服务安装

echo "======================================================================"
echo "ArkTS 符号表服务 - 快速测试"
echo "======================================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python
echo "1. 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "   ${GREEN}✓${NC} $PYTHON_VERSION"
else
    echo -e "   ${RED}✗${NC} Python 3 未找到"
    exit 1
fi

# 检查是否在虚拟环境中
echo ""
echo "2. 检查虚拟环境..."
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "   ${GREEN}✓${NC} 虚拟环境: $VIRTUAL_ENV"
else
    echo -e "   ${YELLOW}⚠${NC} 未在虚拟环境中（推荐使用虚拟环境）"
fi

# 安装依赖
echo ""
echo "3. 安装依赖..."
echo "   执行: pip install -r requirements.txt"
pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✓${NC} 依赖安装成功"
else
    echo -e "   ${RED}✗${NC} 依赖安装失败"
    exit 1
fi

# 安装项目
echo ""
echo "4. 安装项目（开发模式）..."
echo "   执行: pip install -e ."
pip install -q -e .
if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✓${NC} 项目安装成功"
else
    echo -e "   ${RED}✗${NC} 项目安装失败"
    exit 1
fi

# 运行验证脚本
echo ""
echo "5. 运行环境验证..."
python3 verify_installation.py

# 显示下一步
echo ""
echo "======================================================================"
echo "快速开始:"
echo "======================================================================"
echo "1. 运行完整示例:"
echo "   python examples/complete_example.py"
echo ""
echo "2. 运行测试:"
echo "   pytest tests/ -v"
echo ""
echo "3. 查看文档:"
echo "   cat README.md"
echo "   cat QUICKSTART.md"
echo "======================================================================"

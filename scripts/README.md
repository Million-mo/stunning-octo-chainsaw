# 脚本工具目录

本目录包含用于开发、调试和验证的实用脚本工具。

## 🔧 可用脚本

### [inspect_ast.py](./inspect_ast.py)
AST 结构检查工具

**功能**：分析 ArkTS 代码的 AST 结构，打印详细的节点信息

**使用方式**：
```bash
python scripts/inspect_ast.py
```

**用途**：
- 理解 tree-sitter-arkts 的 AST 节点结构
- 调试符号提取逻辑
- 验证节点类型和字段
- 查看节点的子节点关系

**输出示例**：
```
class_declaration (0, 0) to (5, 1)
  ├── class (keyword)
  ├── MyClass (identifier)
  └── class_body
      ├── { (punctuation)
      ├── method_declaration
      └── } (punctuation)
```

### [inspect_arkui_ast.py](./inspect_arkui_ast.py)
ArkUI 专用 AST 检查工具

**功能**：专门分析 ArkUI 框架相关的 AST 结构

**使用方式**：
```bash
python scripts/inspect_arkui_ast.py
```

**用途**：
- 检查 ArkUI 装饰器的 AST 结构
- 验证组件声明的节点类型
- 分析 build() 方法的 UI 树结构
- 调试 ArkUI 特性提取逻辑

**特点**：
- 包含 ArkUI 测试用例
- 高亮显示装饰器节点
- 详细的节点属性信息

### [verify_installation.py](./verify_installation.py)
环境验证工具

**功能**：验证项目依赖和环境配置是否正确

**使用方式**：
```bash
python scripts/verify_installation.py
```

**检查项**：
- ✅ Python 版本
- ✅ tree-sitter 库
- ✅ tree-sitter-arkts-open 包
- ✅ 其他依赖库
- ✅ 能否成功解析 ArkTS 代码

**输出示例**：
```
✅ Python 版本: 3.10.0
✅ tree-sitter 已安装
✅ tree-sitter-arkts-open 已安装
✅ 成功解析测试代码
所有检查通过！
```

## 🚀 使用场景

### 1. 开发新功能时
使用 `inspect_ast.py` 或 `inspect_arkui_ast.py` 来：
- 了解需要处理的 AST 节点结构
- 验证节点类型名称
- 查看节点的子节点和字段

### 2. 调试问题时
使用检查工具来：
- 对比预期结构和实际结构
- 找出节点访问错误的原因
- 验证修改后的提取逻辑

### 3. 设置新环境时
使用 `verify_installation.py` 来：
- 快速检查环境配置
- 确认依赖安装正确
- 排除环境问题

## 📝 自定义脚本

你可以基于现有脚本创建自定义工具：

```python
# 示例：创建自定义 AST 检查脚本
from tree_sitter_arkts import get_parser

parser = get_parser()
tree = parser.parse(your_code.encode('utf-8'))

# 自定义遍历逻辑
def traverse(node, depth=0):
    print("  " * depth + f"{node.type}")
    for child in node.children:
        traverse(child, depth + 1)

traverse(tree.root_node)
```

## 🐛 问题排查

如果脚本运行出错：
1. 确保在项目根目录运行脚本
2. 检查 Python 路径是否正确
3. 验证依赖是否安装（`pip install -r requirements.txt`）
4. 查看脚本输出的错误信息

## 💡 提示

- 这些脚本主要用于开发和调试，不应在生产环境使用
- 可以修改脚本中的测试代码来分析特定的 ArkTS 语法
- 建议在修改提取器逻辑前先用检查工具验证 AST 结构

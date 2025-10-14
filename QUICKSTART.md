# 快速开始指南

## 前提条件

在开始之前，请确保您的环境满足以下要求：

- Python 3.9 或更高版本
- pip 包管理器
- （可选）虚拟环境工具（venv 或 conda）

## 安装步骤

### 1. 克隆项目

```bash
cd /Users/million_mo/projects/stunning-octo-chainsaw
```

### 2. 创建虚拟环境（推荐）

```bash
# 使用 venv
python -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 开发模式安装（推荐）
pip install -e .
```

## 配置 Tree-sitter ArkTS 解析器

`tree-sitter-arkts-open` 已经公开发布，可以通过 pip 直接安装：

```bash
pip install tree-sitter-arkts-open
```

### 在代码中使用

```python
import tree_sitter_arkts_open as ts_arkts
from tree_sitter import Language, Parser

# 获取ArkTS语言
ARKTS_LANGUAGE = Language(ts_arkts.language(), "arkts")

# 创建解析器
parser = Parser()
parser.set_language(ARKTS_LANGUAGE)
```

### 完整示例

```python
import tree_sitter_arkts as ts_arkts
from tree_sitter import Language, Parser
from arkts_processor import SymbolService

# 1. 初始化服务
service = SymbolService(db_path="my_symbols.db")

# 2. 配置解析器
ARKTS_LANGUAGE = Language(ts_arkts.language(), "arkts")
parser = Parser()
parser.set_language(ARKTS_LANGUAGE)
service.set_parser(parser)

# 3. 处理文件
result = service.process_file("example.ets")
print(f"提取了 {result['symbols']} 个符号")
```

## 基本使用

### 示例 1：处理单个文件

```python
from arkts_processor import SymbolService
import tree_sitter

# 1. 初始化服务
service = SymbolService(db_path="my_symbols.db")

# 2. 配置解析器（需要先获取ArkTS语言库）
# parser = tree_sitter.Parser()
# arkts_language = tree_sitter.Language('path/to/arkts.so', 'arkts')
# parser.set_language(arkts_language)
# service.set_parser(parser)

# 3. 处理文件
# result = service.process_file("example.ets")
# print(f"提取了 {result['symbols']} 个符号")
# print(f"构建了 {result['scopes']} 个作用域")
# print(f"解析了 {result['references']} 个引用")
```

### 示例 2：符号查询

```python
# 按名称查找
symbols = service.find_symbol_by_name("MyClass")
for symbol in symbols:
    print(f"{symbol.symbol_type.value}: {symbol.name}")

# 查找所有类
classes = service.index_service.find_classes()
for cls in classes:
    print(f"类: {cls.name} at {cls.file_path}:{cls.range.start.line}")

# 查找所有函数
functions = service.index_service.find_functions()
for func in functions:
    print(f"函数: {func.name}")
```

### 示例 3：LSP功能

```python
# 跳转到定义
definition = service.find_definition("file.ets", line=10, column=5)
if definition:
    print(f"定义位置: {definition.file_path}:{definition.range.start.line}")

# 查找引用
if definition and definition.id:
    references = service.find_references(definition.id)
    print(f"找到 {len(references)} 个引用")

# 悬停信息
hover_info = service.get_hover_info("file.ets", line=10, column=5)
if hover_info:
    print(f"名称: {hover_info['name']}")
    print(f"签名: {hover_info['signature']}")

# 代码补全
completions = service.get_completion_items("file.ets", line=10, column=5, prefix="get")
for symbol in completions:
    print(f"补全项: {symbol.name}")
```

## 运行示例代码

### 运行基本使用示例

```bash
python examples/basic_usage.py
```

该示例展示了：
- 服务初始化
- 符号查询
- 统计信息获取

**注意**：由于缺少ArkTS解析器，示例使用模拟数据演示功能。

## 运行测试

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定测试

```bash
# 测试数据库仓库
pytest tests/test_repository.py -v

# 测试符号提取器
pytest tests/test_extractor.py -v

# 测试集成功能
pytest tests/test_integration.py -v
```

### 生成覆盖率报告

```bash
pytest tests/ --cov=arkts_processor --cov-report=html
# 报告位于 htmlcov/index.html
```

## 项目结构概览

```
stunning-octo-chainsaw/
├── src/arkts_processor/          # 核心代码
│   ├── models.py                  # 数据模型
│   ├── database/                  # 数据库层
│   └── symbol_service/            # 符号服务
├── tests/                         # 测试代码
├── examples/                      # 示例代码
├── requirements.txt               # 依赖
├── setup.py                       # 安装配置
├── README.md                      # 项目文档
├── IMPLEMENTATION_SUMMARY.md      # 实现总结
└── QUICKSTART.md                  # 本文件
```

## 常见问题

### Q1: 如何获取 tree-sitter-arkts-open？

**A**: 该库尚未公开发布。您可以：
1. 联系项目维护者获取访问权限
2. 使用类似的TypeScript解析器进行测试
3. 等待正式发布

### Q2: 为什么测试显示导入错误？

**A**: 这是正常的。在正式安装包之前，IDE可能无法解析导入。解决方法：
```bash
# 开发模式安装
pip install -e .
```

### Q4: 如何处理大型项目？

**A**: 
```python
# 批量处理文件
file_list = ["file1.ets", "file2.ets", "file3.ets"]
results = service.process_files(file_list)
for result in results:
    print(result)
```

### Q5: 如何清空数据库？

**A**:
```python
service.clear_database()
```

### Q6: 如何刷新单个文件的符号？

**A**:
```python
service.refresh_file("file.ets")
```

## 下一步

1. **阅读完整文档**：查看 [README.md](README.md) 了解所有功能
2. **查看实现细节**：阅读 [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
3. **参考架构设计**：查看 [.qoder/quests/arkts-code-processing-mvp-architecture.md](.qoder/quests/arkts-code-processing-mvp-architecture.md)
4. **编写自己的代码**：基于示例开发自己的应用

## 获取帮助

如有问题，请：
1. 查看项目文档
2. 查看测试用例了解使用方式
3. 提交 Issue
4. 联系项目维护者

## 贡献

欢迎贡献代码！请：
1. Fork 项目
2. 创建功能分支
3. 提交 Pull Request

---

**祝您使用愉快！** 🎉

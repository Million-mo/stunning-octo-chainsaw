# 快速开始指南

本指南将帮助您快速上手 ArkTS 代码处理平台，包括**符号服务**和**Chunk 服务**两大核心功能，以及最新的**动态上下文控制** 🆕 功能。

## 前提条件

在开始之前，请确保您的环境满足以下要求：

- Python 3.9 或更高版本
- pip 包管理器
- （可选）虚拟环境工具（venv 或 conda）

## 安装步骤

### 1. 克隆项目

```bash
cd stunning-octo-chainsaw
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
import tree_sitter_arkts as ts_arkts
from tree_sitter import Language, Parser

# 获取ArkTS语言
ARKTS_LANGUAGE = Language(ts_arkts.language())

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
ARKTS_LANGUAGE = Language(ts_arkts.language())
parser = Parser(ARKTS_LANGUAGE)
service.set_parser(parser)

# 3. 处理文件
result = service.process_file("example.ets")
print(f"提取了 {result['symbols']} 个符号")
```

## 基本使用

### 示例 1：使用符号服务处理单个文件

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

### 示例 2：使用符号服务进行符号查询

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

### 示例 3：LSP 功能集成

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

## 使用 Chunk 服务

> ⭐ **Chunk 服务**是针对 RAG（检索增强生成）应用优化的代码块生成服务，能够自动提取语义完整的代码块并增强上下文。
> 🆕 **动态上下文控制**：根据代码块大小智能调整上下文增强策略，优化 embedding 效果。

### Chunk 服务特性

- ✅ **语义完整性**: 自动提取函数、类、组件等完整代码块
- ✅ **动态上下文控制** 🆕: 
  - 小型代码块 (<100 tokens): 丰富的 L1-L3 层元数据头
  - 中型代码块 (100-500 tokens): 平衡的 L1-L2 层元数据头  
  - 大型代码块 (>500 tokens): 精简的 L1 层元数据头
- ✅ **ArkUI 特化**: 识别装饰器、状态变量、生命周期方法，自动添加 L4 层元数据
- ✅ **依赖追溯**: 保留 imports、extends、implements 关系
- ✅ **Embedding 就绪**: 生成可直接用于向量化的增强文本

### 示例 4：快速体验 Chunk 服务

```python
import tree_sitter
import tree_sitter_arkts as ts_arkts
from arkts_processor.symbol_service.service import SymbolService
from arkts_processor.chunk_service.service import ChunkService

# 1. 初始化符号服务
symbol_service = SymbolService("symbols.db")
parser = tree_sitter.Parser(tree_sitter.Language(ts_arkts.language()))
symbol_service.set_parser(parser)

# 2. 初始化 Chunk 服务
chunk_service = ChunkService(symbol_service, "chunks.db")

# 3. 为文件生成 Chunk
chunks = chunk_service.generate_chunks("example.ets")
print(f"生成了 {len(chunks)} 个 Chunk")

# 4. 查看 Chunk 信息
for chunk in chunks[:3]:  # 显示前 3 个
    print(f"\n{chunk.name} ({chunk.type.value})")
    print(f"  - Context: {chunk.context}")
    print(f"  - Imports: {', '.join(chunk.imports) if chunk.imports else 'None'}")

# 5. 获取可嵌入文本（用于 RAG）
embedable_texts = chunk_service.get_embedable_texts("example.ets")
for item in embedable_texts:
    # 可以直接用于 embedding 模型
    text = item['text']  # 包含元数据头 + 原始代码
    chunk_id = item['chunk_id']  # 唯一标识符
    metadata = item['metadata']  # 完整元数据
```

### 示例 5：Chunk 查询和搜索

```python
# 按 ID 查询
chunk = chunk_service.get_chunk_by_id("example.ets#MyClass")
if chunk:
    print(f"找到 Chunk: {chunk.name}")

# 按文件查询
chunks = chunk_service.get_chunks_by_file("example.ets")
print(f"文件包含 {len(chunks)} 个 Chunk")

# 按类型查询
from arkts_processor.chunk_models import ChunkType
functions = chunk_service.get_chunks_by_type(ChunkType.FUNCTION)
print(f"找到 {len(functions)} 个函数 Chunk")

# 名称搜索
results = chunk_service.search_chunks("get", limit=5)
for chunk in results:
    print(f"  - {chunk.name} ({chunk.type.value})")

# 查找相关 Chunk
related = chunk_service.get_related_chunks(chunk.chunk_id)
print(f"找到 {len(related)} 个相关 Chunk")
```

### 示例 6：RAG 集成完整流程

```python
import tree_sitter
import tree_sitter_arkts as ts_arkts
from arkts_processor.symbol_service.service import SymbolService
from arkts_processor.chunk_service.service import ChunkService

# 1. 初始化服务
parser = tree_sitter.Parser(tree_sitter.Language(ts_arkts.language()))
symbol_service = SymbolService("symbols.db")
symbol_service.set_parser(parser)
chunk_service = ChunkService(symbol_service, "chunks.db")

# 2. 处理项目中的所有 .ets 文件
from pathlib import Path

project_files = list(Path("./src").rglob("*.ets"))
for file_path in project_files:
    chunks = chunk_service.generate_chunks(str(file_path))
    print(f"处理了 {file_path}: {len(chunks)} 个 Chunk")

# 3. 获取所有可嵌入文本
all_embedable = []
for file_path in project_files:
    embedable = chunk_service.get_embedable_texts(str(file_path))
    all_embedable.extend(embedable)

print(f"\n总计 {len(all_embedable)} 个可嵌入文本")

# 4. 与 embedding 模型集成（示意）
# from sentence_transformers import SentenceTransformer
# model = SentenceTransformer('all-MiniLM-L6-v2')
# 
# for item in all_embedable:
#     vector = model.encode(item['text'])
#     # 存储到向量数据库
#     vector_db.insert(
#         id=item['chunk_id'],
#         vector=vector,
#         metadata=item['metadata']
#     )

# 5. 查看增强后的文本格式
if all_embedable:
    sample = all_embedable[0]
    print("\n增强文本示例:")
    print("-" * 60)
    print(sample['text'][:500])  # 显示前 500 字符
```

### 上下文增强格式说明

#### 动态上下文策略 🆕

根据代码块大小自动调整元数据头详细程度：

**元数据分层策略**：
- **L1 层（必要层）**: 文件路径、类型、名称 - 所有代码块均包含
- **L2 层（重要层）**: 上下文、导入、标签 - 小/中型代码块包含
- **L3 层（辅助层）**: 装饰器、可见性、参数 - 仅小型代码块包含
- **L4 层（特化层）**: 组件类型、状态变量 - ArkUI 组件自动添加

**大小阈值**：
- < 100 tokens: 小型代码块 → L1 + L2 + L3 (丰富元数据)
- 100-500 tokens: 中型代码块 → L1 + L2 (平衡元数据)
- \> 500 tokens: 大型代码块 → L1 (精简元数据)

#### 通用函数/类示例

**小型函数** (< 100 tokens, 包含 L1-L3):
```
# file: src/services/user_service.ts
# class: UserService
# function: getUserProfile
# imports: [UserRepo, AuthService]
# tags: [async, public]
# return_type: Promise<User>

function getUserProfile(id: string): Promise<User> {
  return UserRepo.findById(id);
}
```

**中型类** (100-500 tokens, 包含 L1-L2):
```
# file: src/models/user.ts
# class: User
# imports: [BaseModel, Validator]
# tags: [class, has-constructor]

export class User extends BaseModel {
  // ... 完整类定义 ...
}
```

**大型服务** (> 500 tokens, 仅包含 L1):
```
# file: src/services/data_service.ts
# class: DataService

export class DataService {
  // ... 复杂服务逻辑 ...
}
```

#### ArkUI 组件示例 (自动添加 L4 层)

**小型组件** (包含 L1-L4):
```
```
# file: src/views/Login.ets
# component: LoginView
# component_type: Entry
# decorators: [@Component, @Entry]
# state_vars: [username: string, password: string]
# lifecycle_hooks: [aboutToAppear]
# imports: [router, promptAction]
# tags: [ui-component, entry]

@Component
struct LoginView {
  @State username: string = '';
  @State password: string = '';
  
  aboutToAppear() { /* ... */ }
  build() { /* ... */ }
}
```

### 示例 7：动态上下文控制演示 🆕

```bash
python examples/dynamic_context_demo.py
```

该示例展示了：
- 小型代码块的丰富元数据头 (L1-L3)
- 中型代码块的平衡元数据头 (L1-L2)
- ArkUI 组件的特化元数据 (L1-L4)
- 元数据占比分析

## 运行示例代码

### 运行符号服务示例

```bash
python examples/basic_usage.py
```

该示例展示了：
- 符号服务初始化
- 符号查询和搜索
- 统计信息获取

### 运行 Chunk 服务示例 ⭐

```bash
python examples/chunk_example.py
```

该示例展示了 6 个完整场景：

1. **生成 Chunk**: 为单个文件生成代码块
2. **查询 Chunk**: 按 ID、文件、类型、名称查询
3. **相关 Chunk**: 查找具有依赖关系的 Chunk
4. **增强文本**: 查看用于 Embedding 的增强文本
5. **JSON 导出**: 导出 Chunk 数据为 JSON 格式
6. **统计信息**: 获取 Chunk 统计数据

**输出示例**：
```
========================================
示例 1：为单个文件生成 Chunk
========================================

正在处理文件: example.ets

生成了 15 个 Chunk:

1. Person (class)
   - ID: example.ets#Person
   - Context: Person
   - Imports: None
   - Tags: class, has-constructor
   - Range: L10-L45

2. getName (function)
   - ID: example.ets#Person.getName
   - Context: Person.getName
   - Tags: function, public, pure-function
   - Return Type: string
```

## 运行测试

### 运行所有测试

```bash
pytest tests/ -v
```

### 运行特定测试

#### 符号服务测试

```bash
# 测试数据库仓库
pytest tests/test_repository.py -v

# 测试符号提取器
pytest tests/test_extractor.py -v

# 测试集成功能
pytest tests/test_integration.py -v

# 测试 ArkUI 支持
pytest tests/test_arkui_support.py -v
```

#### Chunk 服务测试 ⭐

```bash
# 运行所有 Chunk 测试
./run_chunk_tests.sh

# 或分别运行
pytest tests/test_chunk_extractor.py -v        # Chunk 提取器测试 (7 个)
pytest tests/test_context_enricher.py -v       # 上下文增强器测试 (6 个)
pytest tests/test_metadata_builder.py -v       # 元数据构建器测试 (13 个)
pytest tests/test_chunk_integration.py -v      # Chunk 集成测试 (13 个)

# 运行 Chunk 验证脚本
python verify_chunk_service.py
```

**测试覆盖**：
- 符号服务：19 个单元测试 ✅
- Chunk 服务：45+ 个测试（单元 + 集成 + 动态上下文）✅
- 总计：64+ 个测试，100% 通过率 ✅

### 生成覆盖率报告

```bash
pytest tests/ --cov=arkts_processor --cov-report=html
# 报告位于 htmlcov/index.html
```

## 项目结构概览

```
stunning-octo-chainsaw/
├── src/arkts_processor/          # 核心代码
│   ├── models.py                  # 符号数据模型
│   ├── chunk_models.py            # Chunk 数据模型 ⭐
│   ├── database/                  # 数据库层
│   ├── symbol_service/            # 符号服务
│   └── chunk_service/             # Chunk 服务 ⭐
├── tests/                         # 测试代码
│   ├── test_extractor.py          # 符号提取器测试
│   ├── test_chunk_*.py            # Chunk 服务测试 ⭐
│   ├── test_dynamic_context_*.py  # 动态上下文测试 🆕
│   └── ...                        # 其他测试
├── examples/                      # 示例代码
│   ├── basic_usage.py             # 符号服务示例
│   ├── chunk_example.py           # Chunk 服务示例 ⭐
│   └── dynamic_context_demo.py    # 动态上下文控制演示 🆕
├── docs/                          # 文档
│   ├── CHUNK_README.md            # Chunk 功能说明 ⭐
│   ├── CHUNK_API.md               # Chunk API 文档 ⭐
│   ├── DYNAMIC_CONTEXT_CONTROL.md # 动态上下文控制设计 🆕
│   ├── DYNAMIC_CONTEXT_IMPLEMENTATION.md  # 动态上下文实现 🆕
│   └── ...                        # 其他文档
├── requirements.txt               # 依赖
├── setup.py                       # 安装配置
├── README.md                      # 项目主文档
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

### Q3: Chunk 服务和符号服务有什么区别？

**A**: 
- **符号服务**: 提供代码符号的精确分析，用于 LSP、代码导航等场景
- **Chunk 服务**: 基于符号服务，专为 RAG 应用优化，提供语义完整的代码块和增强上下文
- **动态上下文控制** 🆕: 根据代码块大小智能调整上下文详细程度，优化 embedding 效果

```python
# 两者可以一起使用
symbol_service = SymbolService("symbols.db")
chunk_service = ChunkService(symbol_service, "chunks.db")

# Chunk 服务会自动应用动态上下文策略
chunks = chunk_service.generate_chunks("example.ets")
```

### Q4: 如何处理大型项目？

**A**: 
```python
# 符号服务 - 批量处理文件
file_list = ["file1.ets", "file2.ets", "file3.ets"]
results = service.process_files(file_list)
for result in results:
    print(result)

# Chunk 服务 - 批量生成
from pathlib import Path
files = list(Path("./src").rglob("*.ets"))
for file_path in files:
    chunks = chunk_service.generate_chunks(str(file_path))
    print(f"处理了 {file_path}: {len(chunks)} 个 Chunk")
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
2. **了解 Chunk 服务**：
   - 功能概述：[docs/CHUNK_README.md](docs/CHUNK_README.md)
   - API 参考：[docs/CHUNK_API.md](docs/CHUNK_API.md)
   - 实现细节：[docs/CHUNK_IMPLEMENTATION_SUMMARY.md](docs/CHUNK_IMPLEMENTATION_SUMMARY.md)
   - 动态上下文控制 🆕：[docs/DYNAMIC_CONTEXT_CONTROL.md](docs/DYNAMIC_CONTEXT_CONTROL.md)
3. **了解 ArkUI 支持**：[docs/ARKUI_QUICK_REFERENCE.md](docs/ARKUI_QUICK_REFERENCE.md)
4. **运行示例代码**：
   - 符号服务：`python examples/basic_usage.py`
   - Chunk 服务：`python examples/chunk_example.py`
   - 动态上下文演示 🆕：`python examples/dynamic_context_demo.py`
5. **编写自己的代码**：基于示例开发自己的应用

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

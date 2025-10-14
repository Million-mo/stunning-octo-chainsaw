# ArkTS代码处理平台 - 符号表服务MVP

> ⚡ **重要更新**: `tree-sitter-arkts-open` 已公开发布！现在可以通过 `pip install tree-sitter-arkts-open` 直接安装。

基于tree-sitter-arkts-open的ArkTS代码符号表服务，提供代码符号提取、作用域分析、类型推导和引用解析功能。

## 功能特性

### 核心功能

1. **符号提取** - 从ArkTS代码中提取以下符号类型：
   - 类 (Class)
   - 接口 (Interface)
   - 方法 (Method)
   - 函数 (Function)
   - 变量 (Variable)
   - 参数 (Parameter)
   - 属性 (Property)
   - 枚举 (Enum)
   - 枚举成员 (Enum Member)
   - 模块 (Module)
   - 命名空间 (Namespace)
   - 类型别名 (Type Alias)

2. **作用域分析** - 构建嵌套作用域层次结构
   - 全局作用域 (Global)
   - 模块作用域 (Module)
   - 类作用域 (Class)
   - 函数作用域 (Function)
   - 块作用域 (Block)
   - 命名空间作用域 (Namespace)

3. **类型推导** - 分析符号的类型信息
   - 显式类型声明
   - 字面量类型推导
   - 表达式类型推导
   - 泛型参数解析

4. **引用解析** - 建立符号间的引用关系
   - 符号定义查找
   - 符号引用查找
   - 调用关系分析
   - 继承关系追踪
   - 实现关系追踪

5. **符号索引** - 高效的符号查询
   - 按名称查询
   - 按类型查询
   - 按文件查询
   - 前缀搜索（代码补全）
   - 模糊搜索

6. **数据持久化** - SQLite数据库存储
   - 符号表 (symbols)
   - 作用域表 (scopes)
   - 引用表 (references)
   - 类型表 (types)
   - 符号关系表 (symbol_relations)

## 项目结构

```
src/arkts_processor/
├── __init__.py                    # 包初始化
├── models.py                      # 核心数据模型
├── database/                      # 数据库模块
│   ├── __init__.py
│   ├── schema.py                  # 数据库Schema定义
│   └── repository.py              # 数据访问层
└── symbol_service/                # 符号服务模块
    ├── __init__.py
    ├── service.py                 # 主服务接口
    ├── ast_traverser.py           # AST遍历器
    ├── extractor.py               # 符号提取器
    ├── scope_analyzer.py          # 作用域分析器
    ├── type_inference.py          # 类型推导引擎
    ├── reference_resolver.py      # 引用解析器
    └── index_service.py           # 符号索引服务

tests/                             # 测试模块
├── __init__.py
├── test_extractor.py              # 符号提取器测试
├── test_scope_analyzer.py         # 作用域分析器测试
└── test_repository.py             # 数据库仓库测试

examples/                          # 示例代码
└── basic_usage.py                 # 基本使用示例
```

## 安装

### 依赖要求

- Python 3.9+
- tree-sitter >= 0.20.0
- tree-sitter-arkts-open >= 0.1.0（已公开发布）
- sqlalchemy >= 2.0.0

### 安装步骤

```bash
# 克隆仓库
git clone <repository-url>
cd stunning-octo-chainsaw

# 安装依赖（包括tree-sitter-arkts-open）
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

## 快速开始

### 基本使用

```python
import tree_sitter
from arkts_processor import SymbolService

# 1. 初始化符号服务
service = SymbolService(db_path="arkts_symbols.db")

# 2. 配置tree-sitter解析器
parser = tree_sitter.Parser()
# 需要先编译ArkTS语言库
arkts_language = tree_sitter.Language('path/to/arkts.so', 'arkts')
parser.set_language(arkts_language)
service.set_parser(parser)

# 3. 处理ArkTS文件
result = service.process_file("path/to/file.ets")
print(f"提取符号数: {result['symbols']}")
print(f"作用域数: {result['scopes']}")
print(f"引用数: {result['references']}")
for symbol in symbols:
    print(f"{symbol.symbol_type.value}: {symbol.name}")

# 5. 查找定义
symbol = service.find_definition("file.ets", line=10, column=5)
if symbol:
    print(f"定义: {symbol.name} at {symbol.file_path}:{symbol.range.start.line}")

# 6. 查找引用
references = service.find_references(symbol.id)
for ref in references:
    print(f"引用: {ref.file_path}:{ref.position.line}")
```

### 符号查询示例

```python
# 按类型查询
classes = service.index_service.find_classes("file.ets")
functions = service.index_service.find_functions("file.ets")
interfaces = service.index_service.find_interfaces("file.ets")

# 前缀搜索（用于代码补全）
completions = service.index_service.find_symbols_by_prefix("get")

# 模糊搜索
results = service.index_service.search_symbols("person", fuzzy=True)

# 获取文档符号（大纲视图）
doc_symbols = service.get_document_symbols("file.ets")

# 工作区符号搜索
workspace_symbols = service.get_workspace_symbols("MyClass")
```

### LSP集成示例

符号服务可以与LSP服务器集成，提供以下功能：

- **textDocument/hover** - 悬停提示
- **textDocument/definition** - 跳转到定义
- **textDocument/references** - 查找引用
- **textDocument/documentSymbol** - 文档符号
- **textDocument/completion** - 代码补全

```python
# 悬停信息
hover_info = service.get_hover_info("file.ets", line=10, column=5)
if hover_info:
    print(f"名称: {hover_info['name']}")
    print(f"类型: {hover_info['type']}")
    print(f"签名: {hover_info['signature']}")
    print(f"文档: {hover_info['documentation']}")

# 代码补全
completions = service.get_completion_items("file.ets", line=10, column=5, prefix="get")
```

## API文档

### SymbolService

主服务类，提供统一的符号服务接口。

#### 方法

- `set_parser(parser)` - 设置tree-sitter解析器
- `process_file(file_path)` - 处理单个文件
- `process_files(file_paths)` - 批量处理文件
- `find_symbol_by_name(name, file_path=None)` - 按名称查找符号
- `find_symbol_at_position(file_path, line, column)` - 查找位置的符号
- `find_definition(file_path, line, column)` - 查找定义
- `find_references(symbol_id)` - 查找引用
- `get_document_symbols(file_path)` - 获取文档符号
- `get_workspace_symbols(query)` - 工作区符号搜索
- `get_completion_items(file_path, line, column, prefix)` - 获取补全项
- `get_hover_info(file_path, line, column)` - 获取悬停信息
- `get_statistics(file_path=None)` - 获取统计信息
- `refresh_file(file_path)` - 刷新文件

### 数据模型

#### Symbol

符号信息，包含以下属性：

- `id` - 符号ID
- `name` - 符号名称
- `symbol_type` - 符号类型 (SymbolType枚举)
- `file_path` - 文件路径
- `range` - 代码范围 (Range对象)
- `scope_id` - 所属作用域ID
- `type_info` - 类型信息 (TypeInfo对象)
- `return_type` - 返回类型 (TypeInfo对象)
- `visibility` - 可见性 (Visibility枚举)
- `is_static` - 是否静态
- `is_abstract` - 是否抽象
- `is_readonly` - 是否只读
- `is_async` - 是否异步
- `parameters` - 参数列表
- `members` - 成员列表
- `extends` - 继承列表
- `implements` - 实现列表
- `documentation` - 文档注释

#### Scope

作用域信息：

- `id` - 作用域ID
- `scope_type` - 作用域类型 (ScopeType枚举)
- `file_path` - 文件路径
- `range` - 代码范围
- `parent_id` - 父作用域ID
- `symbols` - 符号字典
- `children` - 子作用域列表

#### Reference

符号引用：

- `id` - 引用ID
- `symbol_id` - 符号ID
- `file_path` - 文件路径
- `position` - 位置信息
- `reference_type` - 引用类型 (ReferenceType枚举)
- `context` - 引用上下文

## 测试

运行单元测试：

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_repository.py -v

# 生成覆盖率报告
pytest tests/ --cov=arkts_processor --cov-report=html
```

## 性能优化

符号服务实现了多级优化策略：

1. **内存索引** - 高频查询使用内存索引，避免数据库访问
2. **批量操作** - 符号保存使用批量插入，提升写入性能
3. **懒加载** - 按需加载符号详情，减少内存占用
4. **缓存机制** - 文件级别的符号和作用域缓存

## 架构设计

符号服务采用分层架构：

```
┌─────────────────────────────────┐
│      Service Layer              │  SymbolService
├─────────────────────────────────┤
│      Business Logic             │  Extractor, ScopeAnalyzer
│                                 │  TypeInference, ReferenceResolver
├─────────────────────────────────┤
│      Index Layer                │  SymbolIndexService
├─────────────────────────────────┤
│      Data Access Layer          │  SymbolRepository
├─────────────────────────────────┤
│      Storage Layer              │  SQLite Database
└─────────────────────────────────┘
```

## 扩展开发

### 添加新的符号类型

1. 在 `models.py` 中的 `SymbolType` 枚举添加新类型
2. 在 `extractor.py` 中实现对应的 `visit_*` 方法
3. 更新数据库Schema（如需要）

### 自定义类型推导规则

在 `type_inference.py` 中的 `TypeInferenceEngine` 类添加新的推导方法。

### 扩展查询功能

在 `index_service.py` 中的 `SymbolIndexService` 类添加新的查询方法。

## 已知限制

1. **解析器依赖** - 需要 tree-sitter-arkts-open 库（尚未公开发布）
2. **跨文件分析** - 当前版本主要支持单文件分析，跨文件引用解析需要进一步开发
3. **复杂类型** - 对于复杂泛型和联合类型的支持有限
4. **增量更新** - 暂不支持增量解析，文件修改需要完全重新处理

## 路线图

- [ ] 完善tree-sitter-arkts-open集成
- [ ] 实现跨文件引用解析
- [ ] 增强类型推导能力
- [ ] 支持增量解析
- [ ] 实现代码重构功能
- [ ] LSP服务器完整实现
- [ ] 性能基准测试
- [ ] 生产环境优化

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 作者

ArkTS Team

## 参考文档

- [MVP架构设计文档](.qoder/quests/arkts-code-processing-mvp-architecture.md)
- [Tree-sitter文档](https://tree-sitter.github.io/tree-sitter/)
- [LSP协议规范](https://microsoft.github.io/language-server-protocol/)

# 更新日志

本文档记录了 ArkTS 符号表服务的所有重要变更。

## [未发布]

### 修复
- 🐛 **修复AST遍历问题**：添加了对 'source_file' 和 'program' 根节点类型的处理方法
  - 添加了 `visit_source_file()` 方法处理 ArkTS 文件的根节点
  - 添加了 `visit_program()` 方法处理程序根节点
  - 增强了 `generic_visit()` 方法，提供默认的子节点遍历行为
  - 修复了SQLAlchemy中 `metadata` 字段冲突问题，重命名为 `meta_data`

### 重要更新
- 🎉 **tree-sitter-arkts-open 已公开发布**：现在可以通过 `pip install tree-sitter-arkts-open` 直接安装解析器

### 更新内容
- 更新了所有文档以反映 tree-sitter-arkts-open 的公开发布
- 更新了示例代码以使用新的安装方式
- 添加了完整的可运行示例 `examples/complete_example.py`
- 修正了快速开始指南中的安装说明

## [0.1.0] - 2025-10-13

### 新增功能

#### 核心功能
- ✨ 实现了完整的符号提取器，支持 13 种符号类型
- ✨ 实现了作用域分析器，支持嵌套作用域管理
- ✨ 实现了类型推导引擎，支持多种表达式类型推导
- ✨ 实现了引用解析器，建立符号间的引用关系
- ✨ 实现了符号索引服务，提供高效的符号查询

#### 数据持久化
- ✨ 使用 SQLAlchemy 实现了完整的数据库层
- ✨ 定义了 5 个核心数据表（symbols, scopes, references, types, symbol_relations）
- ✨ 实现了数据仓库模式，提供 CRUD 操作

#### LSP 功能
- ✨ 支持 textDocument/hover - 悬停提示
- ✨ 支持 textDocument/definition - 跳转到定义
- ✨ 支持 textDocument/references - 查找引用
- ✨ 支持 textDocument/documentSymbol - 文档符号
- ✨ 支持 textDocument/completion - 代码补全

#### 架构设计
- 🏗️ 采用分层架构（Service → Business Logic → Data Access → Storage）
- 🏗️ 模块化设计，高内聚、低耦合
- 🏗️ 访问者模式支持扩展新的符号类型

#### 性能优化
- ⚡ 实现了多维度内存索引（名称、类型、文件）
- ⚡ 支持批量操作提升性能
- ⚡ 文件级符号和作用域缓存

### 文档
- 📝 创建了完整的 README.md
- 📝 创建了详细的实现总结 IMPLEMENTATION_SUMMARY.md
- 📝 创建了快速开始指南 QUICKSTART.md
- 📝 所有核心类和方法都有文档字符串

### 测试
- ✅ 实现了单元测试框架
- ✅ 创建了集成测试
- ✅ 提供了测试示例

### 已知问题
- ⚠️ 跨文件引用解析需要进一步开发
- ⚠️ 复杂泛型和联合类型支持有限
- ⚠️ 暂不支持增量解析

### 依赖项
- tree-sitter >= 0.20.0
- tree-sitter-arkts-open >= 0.1.0
- sqlalchemy >= 2.0.0
- alembic >= 1.12.0
- pygls >= 1.2.0
- networkx >= 3.2.0
- fastapi >= 0.104.0
- pydantic >= 2.5.0

## 版本说明

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

### 变更类型

- `新增` - 新功能
- `变更` - 现有功能的变更
- `弃用` - 即将移除的功能
- `移除` - 已移除的功能
- `修复` - 错误修复
- `安全` - 安全相关的修复

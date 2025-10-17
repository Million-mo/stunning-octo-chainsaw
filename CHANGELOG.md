# 更新日志

本文档记录了 ArkTS 符号表服务的所有重要变更。

## [未发布]

### 新增功能
- ✨ **Export 关键字支持** 🆕: 识别并标记通过 `export` 导出的符号
  - 支持 `export class`、`export interface`、`export function` 等
  - 支持 `export const/let/var` 变量导出
  - 支持 `export type` 类型别名导出
  - 支持 `export default` 默认导出
  - 新增 `is_exported` 和 `is_export_default` 字段到 Symbol 模型
  - 与 ChunkService 完全集成，导出信息自动传递
  - ⚠️ **限制**: `export enum` 由于 tree-sitter-arkts-open 解析器限制不支持

- ✨ **动态上下文控制** 🆕: 根据代码块大小智能调整上下文增强策略
  - 小型代码块 (<100 tokens): 添加丰富的 L1-L3 层元数据头
  - 中型代码块 (100-500 tokens): 添加平衡的 L1-L2 层元数据头
  - 大型代码块 (>500 tokens): 仅添加精简的 L1 层元数据头
  - ArkUI 组件自动添加 L4 层特化元数据（组件类型、状态变量、生命周期等）
  - 优化 embedding 效果，提升 RAG 系统召回准确性

### 数据库 Schema 更新
- 💾 在 SymbolModel 中新增 `is_exported` 和 `is_export_default` 字段
- 💾 更新 Repository 保存和读取逻辑以支持新字段

### 文档更新
- 📝 新增 `docs/EXPORT_SUPPORT.md` - Export 功能完整文档
- 📝 新增 `docs/PARSER_LIMITATIONS.md` - ArkTS 解析器限制说明
- 📝 新增 `docs/DYNAMIC_CONTEXT_CONTROL.md` - 动态上下文控制设计文档
- 📝 新增 `docs/DYNAMIC_CONTEXT_IMPLEMENTATION.md` - 动态上下文控制实现文档
- 📝 新增 `examples/dynamic_context_demo.py` - 动态上下文控制演示示例
- 📝 更新 README.md，添加 Export 和动态上下文功能说明
- 📝 更新 QUICKSTART.md，添加动态上下文使用指南和示例
- 📝 归档 `docs/archives/EXPORT_IMPLEMENTATION_SUMMARY.md` - Export 实现细节

### 测试
- ✅ 新增 Export 功能测试（除 `export enum` 外）
- ✅ 新增动态上下文控制集成测试
- ✅ 总测试数量提升至 64+ 个，100% 通过率

### 清理与优化
- 🧹 移除临时测试文件（debug_export_enum.py、inspect_export.py 等）
- 🧹 整理文档结构，将 Export 相关文档移至 docs/ 目录
- 🧹 删除重复文档，保持文档结构清晰

## [0.2.0] - 2025-10-14

### 新增功能 - Chunk 服务完整实现

#### 核心模块（6个）
- ✨ **ChunkExtractor**: 从符号表提取语义完整的代码块
- ✨ **ContextEnricher**: 为代码块添加上下文元数据头
- ✨ **ChunkMetadataBuilder**: 构建完整的 Chunk 元数据
- ✨ **ChunkService**: 提供统一的 Chunk 服务接口
- ✨ **ChunkRepository**: Chunk 数据库存储和查询
- ✨ **ChunkModels**: 完整的 Chunk 数据模型定义

#### 功能特性
- ✅ 语义完整的代码块生成（函数、类、组件、接口、枚举等）
- ✅ 上下文增强（文件路径、类名、导入依赖等元数据头）
- ✅ ArkUI 组件特化（识别装饰器、状态变量、生命周期方法）
- ✅ 依赖关系追溯（imports、extends、implements）
- ✅ RAG 系统集成就绪（提供可直接用于向量化的增强文本）

#### 测试套件
- ✅ 26 个单元测试全部通过
- ✅ 13 个集成测试全部通过
- ✅ 6 个验证测试全部通过

#### 文档
- 📝 `docs/CHUNK_README.md` - Chunk 功能说明
- 📝 `docs/CHUNK_API.md` - Chunk API 完整文档
- 📝 `docs/CHUNK_IMPLEMENTATION_SUMMARY.md` - Chunk 实现总结
- 📝 `examples/chunk_example.py` - 6 个完整使用示例

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

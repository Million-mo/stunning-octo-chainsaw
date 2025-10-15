# 文档目录

本目录包含 ArkTS 符号提取器项目的所有文档。

## 📚 核心文档

### [ARKUI_SUPPORT_SUMMARY.md](./ARKUI_SUPPORT_SUMMARY.md)
ArkUI 框架支持功能的完整文档，包括：
- 支持的所有 ArkUI 装饰器（@State、@Prop、@Link 等）
- 组件声明和生命周期方法
- UI 绑定和事件处理器提取
- 样式函数和资源引用处理
- 使用示例和测试结果

### [ARKUI_QUICK_REFERENCE.md](./ARKUI_QUICK_REFERENCE.md)
ArkUI 功能快速参考指南：
- 支持的装饰器类型速查表
- 符号类型说明
- 快速使用示例
- 常见问题解答

### [AST_ANALYSIS_SUMMARY.md](./AST_ANALYSIS_SUMMARY.md)
AST 节点结构分析文档：
- tree-sitter-arkts 的 AST 节点类型
- 节点结构和字段说明
- 与标准 TypeScript AST 的差异
- 节点访问最佳实践

### [CHUNK_README.md](./CHUNK_README.md)
Chunk 服务功能说明：
- 语义完整的代码块生成
- 上下文增强机制
- ArkUI 组件特化处理
- RAG 系统集成指南

### [CHUNK_API.md](./CHUNK_API.md)
Chunk 服务 API 完整文档：
- API 接口详细说明
- 数据模型定义
- 使用场景示例
- 最佳实践和故障排除

### [CHUNK_IMPLEMENTATION_SUMMARY.md](./CHUNK_IMPLEMENTATION_SUMMARY.md)
Chunk 服务实现总结：
- 核心模块实现细节
- 测试覆盖情况
- 架构设计和数据流
- 功能验证和扩展建议

### [DYNAMIC_CONTEXT_CONTROL.md](./DYNAMIC_CONTEXT_CONTROL.md)
动态上下文控制设计文档：
- 元数据分层策略（L1-L4）
- 大小阈值和上下文策略
- ArkUI 特化元数据
- 性能优化和最佳实践

### [DYNAMIC_CONTEXT_IMPLEMENTATION.md](./DYNAMIC_CONTEXT_IMPLEMENTATION.md)
动态上下文控制实现文档：
- 实现细节和代码结构
- 测试覆盖和验证
- 使用示例和集成指南

## 📦 历史归档

[archives/](./archives/) 目录包含了开发过程中的历史文档：

### 修复和问题追溯
- `BUGFIX_SUMMARY.md` - 修复问题汇总
- `EXTRACTOR_FIX_REPORT.md` - 提取器修复报告
- `FIXES_SUMMARY_2025-10-14.md` - 每日修复总结

### 实现和更新记录
- `IMPLEMENTATION_SUMMARY.md` - 早期实现详细总结
- `SYMBOL_EXTRACTOR_UPDATE.md` - 符号提取器更新说明
- `UPDATE_NOTICE.md` - 功能更新通知

### 项目管理文档
- `PROJECT_ORGANIZATION.md` - 项目文件整理总结 (2025-10-14)
- `CHUNK_SERVICE_COMPLETION.md` - Chunk 服务完整实现报告
- `DOCUMENTATION_UPDATE_SUMMARY.md` - 文档更新总结 (2025-10-15)

### 原始分析数据
- `ast_analysis.txt` - AST 分析原始输出

## 🔍 如何使用这些文档

### 新用户入门路径
1. 阅读项目根目录的 `README.md` 了解项目概况
2. 查看 `QUICKSTART.md` 快速开始使用
3. 参考 `ARKUI_QUICK_REFERENCE.md` 了解 ArkUI 支持

### Chunk 服务学习路径
1. 阅读 `CHUNK_README.md` 了解功能概览
2. 查看 `CHUNK_API.md` 学习 API 使用
3. 参考 `DYNAMIC_CONTEXT_CONTROL.md` 了解动态上下文控制
4. 查看 `CHUNK_IMPLEMENTATION_SUMMARY.md` 了解实现细节

### 开发者参考路径
1. 查看 `AST_ANALYSIS_SUMMARY.md` 理解 AST 结构
2. 参考 `ARKUI_SUPPORT_SUMMARY.md` 深入了解 ArkUI 功能
3. 使用 `scripts/` 目录中的工具脚本进行开发调试
4. 查看 `tests/README.md` 了解测试规范

### 问题排查路径
1. 查看 `archives/` 中的历史问题修复文档
2. 参考项目管理文档了解功能演进过程
3. 使用 `scripts/verify_installation.py` 验证环境

## 📝 文档维护

- 核心功能文档应保持最新
- 历史文档仅作归档参考，不再更新
- 新增功能时请更新对应的核心文档

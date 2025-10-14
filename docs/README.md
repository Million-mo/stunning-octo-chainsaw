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

## 📦 历史归档

[archives/](./archives/) 目录包含了开发过程中的历史文档：
- `BUGFIX_SUMMARY.md` - 修复问题汇总
- `EXTRACTOR_FIX_REPORT.md` - 提取器修复报告
- `FIXES_SUMMARY_2025-10-14.md` - 每日修复总结
- `IMPLEMENTATION_SUMMARY.md` - 实现详细总结
- `SYMBOL_EXTRACTOR_UPDATE.md` - 符号提取器更新说明
- `UPDATE_NOTICE.md` - 更新通知
- `ast_analysis.txt` - AST 分析原始输出

## 🔍 如何使用这些文档

1. **新用户入门**：先阅读项目根目录的 `README.md` 和 `QUICKSTART.md`
2. **了解 ArkUI 支持**：查看 `ARKUI_QUICK_REFERENCE.md` 获取快速概览
3. **深入功能细节**：参考 `ARKUI_SUPPORT_SUMMARY.md` 了解完整功能
4. **开发和调试**：查看 `AST_ANALYSIS_SUMMARY.md` 了解 AST 结构
5. **历史问题追溯**：查看 `archives/` 目录中的历史文档

## 📝 文档维护

- 核心功能文档应保持最新
- 历史文档仅作归档参考，不再更新
- 新增功能时请更新对应的核心文档

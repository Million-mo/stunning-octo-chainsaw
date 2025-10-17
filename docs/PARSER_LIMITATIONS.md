# ArkTS Parser 限制说明

## 当前解析器

项目使用 **tree-sitter-arkts-open** 作为 ArkTS 语法解析器。

安装方式：
```bash
pip install tree-sitter-arkts-open
```

## 已知限制

### 1. Export Enum 解析问题

**问题描述**：
当前版本的 tree-sitter-arkts-open 无法正确解析 `export enum` 语法，会将其识别为 ERROR 节点。

**示例代码**：
```typescript
export enum LoginTrigger {
  LOGIN = 'third-login',
  LOGOUT = 'third-logout'
}
```

**AST 解析结果**：
```
ERROR [Point(row=0, column=0)-Point(row=3, column=1)]
  export [Point(row=0, column=0)-Point(row=0, column=6)]
  ERROR [Point(row=0, column=7)-Point(row=0, column=8)]
  ...
```

**影响范围**：
- `export enum` 声明无法被正确提取
- 枚举成员可能无法被识别
- 相关的类型推导和引用分析受影响

### 2. 其他已知问题

- **命名导出**: `export { Name1, Name2 }` 暂不支持
- **重导出**: `export * from './module'` 暂不支持
- **复杂类型别名**: 包含联合类型的 `export type` 可能解析不完整

## 建议的解决方案

### 短期方案（当前实现）

✅ **已实现**: 对于除 `export enum` 外的其他 export 类型，均能正确处理：
- ✅ `export class`
- ✅ `export interface`
- ✅ `export function`
- ✅ `export const/let/var`
- ✅ `export type`（简单类型）
- ✅ `export default`

❌ **未处理**: `export enum` - 建议用户使用以下替代方案：

**方案 A**: 分离导出
```typescript
// 推荐：先声明，再导出
enum LoginTrigger {
  LOGIN = 'third-login',
  LOGOUT = 'third-logout'
}

export { LoginTrigger };  // 注意：此语法也可能不支持
```

**方案 B**: 使用 const 替代
```typescript
// 使用常量对象替代枚举
export const LoginTrigger = {
  LOGIN: 'third-login',
  LOGOUT: 'third-logout'
} as const;
```

### 中期方案

**选项 1**: 等待 tree-sitter-arkts-open 更新

- 优点：官方支持，长期稳定
- 缺点：依赖上游修复进度
- 行动：向 tree-sitter-arkts-open 项目提交 issue

**选项 2**: 使用官方 ArkTS 解析器（如果存在）

- 需要调研 HarmonyOS 官方是否提供 ArkTS 解析器
- 评估集成复杂度和性能

**选项 3**: Fork 并修复 tree-sitter-arkts-open

- 优点：可以快速修复问题
- 缺点：需要维护自己的 fork，增加维护成本

### 长期方案

**考虑实现多解析器支持**：
```python
class ParserFactory:
    @staticmethod
    def create_parser(parser_type: str):
        if parser_type == "tree-sitter-arkts-open":
            return TreeSitterArkTSParser()
        elif parser_type == "official-arkts":
            return OfficialArkTSParser()
        # ...
```

这样可以：
- 支持多种解析器
- 根据需求选择最合适的解析器
- 在某个解析器有问题时快速切换

## 如何报告问题

如果你发现解析器的问题，请按照以下步骤：

### 1. 确认问题

使用 `inspect_export.py` 或类似工具检查 AST 结构：
```python
import tree_sitter
import tree_sitter_arkts as ts_arkts

code = b"export enum MyEnum { A, B }"
parser = tree_sitter.Parser(tree_sitter.Language(ts_arkts.language()))
tree = parser.parse(code)

# 打印 AST
print(tree.root_node.sexp())
```

### 2. 向上游报告

如果确认是解析器问题，请向 tree-sitter-arkts-open 项目报告：

- **项目地址**: 需要查找 tree-sitter-arkts-open 的 GitHub 仓库
- **Issue 模板**:

```markdown
## 问题描述
`export enum` 语法被解析为 ERROR 节点

## 重现代码
\`\`\`typescript
export enum LoginTrigger {
  LOGIN = 'third-login'
}
\`\`\`

## 期望行为
应该解析为 `export_declaration` 包含 `enum_declaration`

## 实际 AST
\`\`\`
ERROR [...]
  export [...]
  ERROR [...]
\`\`\`

## 环境信息
- tree-sitter-arkts-open version: X.X.X
- Python version: 3.X.X
- OS: macOS/Linux/Windows
```

## 最佳实践

在当前解析器限制下，建议遵循以下最佳实践：

### 1. 优先使用支持良好的语法

✅ **推荐**:
```typescript
export class MyClass { }
export interface MyInterface { }
export function myFunction() { }
export const MY_CONST = 42;
```

⚠️ **谨慎使用**:
```typescript
export enum MyEnum { }  // 可能无法正确解析
export { Name1, Name2 }  // 不支持
export * from './module'  // 不支持
```

### 2. 使用替代方案

如果必须使用枚举：
```typescript
// 方案 1: 使用 const 对象
export const Status = {
  ACTIVE: 'active',
  INACTIVE: 'inactive'
} as const;

export type StatusType = typeof Status[keyof typeof Status];

// 方案 2: 使用字符串字面量类型
export type Status = 'active' | 'inactive';
```

### 3. 逐步迁移

如果项目中已经有大量 `export enum`：
1. 标记这些文件
2. 在解析时记录警告
3. 逐步重构为支持的语法

## 相关资源

- [Tree-sitter 官方文档](https://tree-sitter.github.io/tree-sitter/)
- [TypeScript Grammar for Tree-sitter](https://github.com/tree-sitter/tree-sitter-typescript)
- [ArkTS 官方文档](https://developer.harmonyos.com/cn/docs/documentation/doc-guides/arkts-get-started-0000001504769321)

## 更新日志

### 2025-10-16
- ❌ 移除了 ERROR 节点的临时处理方案
- ✅ 保留了正常 export 语法的完整支持
- 📝 创建了此文档说明解析器限制
- 💡 提供了替代方案和最佳实践

---

**注意**: 本文档会随着解析器的更新而更新。如果你发现新的问题或找到了解决方案，请提交 PR 更新此文档。

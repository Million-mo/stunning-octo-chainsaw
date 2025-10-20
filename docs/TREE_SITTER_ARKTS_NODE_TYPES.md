# tree-sitter-arkts 0.1.8 节点类型参考

本文档记录了 tree-sitter-arkts 0.1.8 版本使用的实际节点类型，与标准 TypeScript 解析器或旧版本存在差异。

## 重要差异

tree-sitter-arkts 0.1.8 使用 `*_statement` 而非 `*_declaration` 作为某些节点类型：

### Export 语句
- ❌ **错误**: `export_declaration`
- ✅ **正确**: `export_statement`

**结构**:
```
export_statement
  ├── export (关键字)
  ├── default (可选)
  └── 实际声明 (class_declaration, lexical_declaration 等)
```

**示例**:
```typescript
export const myVar = 1;        // export_statement → lexical_declaration
export class MyClass {}        // export_statement → class_declaration
export default MyClass;        // export_statement with default
```

### 变量声明
- ❌ **错误**: `variable_declaration` (仅用于 var)
- ✅ **正确**: 
  - `variable_statement` (用于 var)
  - `lexical_declaration` (用于 let/const)

**结构**:
```
variable_statement              // var 声明
  ├── var
  └── variable_declarator
      ├── identifier
      └── ...

lexical_declaration             // let/const 声明
  ├── const (或 let)
  └── variable_declarator
      ├── identifier
      └── ...
```

**示例**:
```typescript
var myVar = 1;                 // variable_statement
let myLet = 2;                 // lexical_declaration
const myConst = 3;             // lexical_declaration
```

### Import 语句
- ❌ **错误**: `import_declaration`
- ✅ **正确**: `import_statement`

**结构**:
```
import_statement
  ├── import
  ├── import_clause
  └── string (模块路径)
```

## 完整节点类型映射

### 顶层声明节点

| 语法 | tree-sitter-arkts 0.1.8 节点类型 | extractor.py 方法 |
|------|----------------------------------|-------------------|
| `class MyClass {}` | `class_declaration` | `visit_class_declaration()` |
| `interface MyInterface {}` | `interface_declaration` | `visit_interface_declaration()` |
| `function myFunc() {}` | `function_declaration` | `visit_function_declaration()` |
| `var myVar = 1;` | `variable_statement` | `visit_variable_statement()` |
| `let myLet = 2;` | `lexical_declaration` | `visit_lexical_declaration()` |
| `const myConst = 3;` | `lexical_declaration` | `visit_lexical_declaration()` |
| `enum MyEnum { A }` | `enum_declaration` | `visit_enum_declaration()` |
| `type MyType = string;` | `type_alias_declaration` | `visit_type_alias_declaration()` |
| `export ...` | `export_statement` | `visit_export_statement()` |
| `import ...` | `import_statement` | _(暂不处理)_ |

### ArkUI 特有节点

| 语法 | 节点类型 | extractor.py 方法 |
|------|---------|-------------------|
| `@Component struct MyComp {}` | `component_declaration` | `visit_component_declaration()` |
| `build() {}` | `build_method` | `visit_build_method()` |

### 类成员节点

| 语法 | 节点类型 | extractor.py 方法 |
|------|---------|-------------------|
| `myMethod() {}` | `method_declaration` | `visit_method_declaration()` |
| `constructor() {}` | `constructor_declaration` | `visit_constructor_declaration()` |
| `myProp: string;` | `property_declaration` | `visit_property_declaration()` |

## 兼容性处理

为了保持向后兼容，extractor.py 同时保留了旧节点类型的处理方法：

```python
# 主要方法（tree-sitter-arkts 0.1.8）
def visit_export_statement(self, node: Node) -> None:
    # 实际处理逻辑
    ...

# 兼容方法（转发到主要方法）
def visit_export_declaration(self, node: Node) -> None:
    """旧节点类型，为兼容性保留"""
    self.visit_export_statement(node)
```

## 测试验证

所有节点类型已通过全面测试验证：

- ✅ 所有变量声明类型（var, let, const）
- ✅ 所有导出语法（export class, export const 等）
- ✅ 所有顶层声明（class, interface, function, enum, type）
- ✅ ArkUI 组件和装饰器
- ✅ 导出状态正确标记

## 更新历史

- **2025-10-20**: 修复 `export_statement` 和 `variable_statement` 节点类型支持
- 相关 Issue: TagColorMap.ets 文件未提取 export const 符号

## 参考

- tree-sitter-arkts GitHub: https://github.com/SPY-LAB-PG/tree-sitter-arkts
- tree-sitter-arkts-open PyPI: https://pypi.org/project/tree-sitter-arkts-open/

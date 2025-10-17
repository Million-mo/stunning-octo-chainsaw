# Export 关键字支持文档

## 概述

本项目已增强对 ArkTS `export` 关键字的支持，现在能够正确识别、提取并处理各种类型的导出声明。

## 支持的 Export 类型

### 1. Export Class（导出类）
```typescript
export class MyClass {
  name: string;
}
```

### 2. Export Interface（导出接口）
```typescript
export interface MyInterface {
  id: number;
  name: string;
}
```

### 3. Export Function（导出函数）
```typescript
export function myFunction(a: number, b: number): number {
  return a + b;
}
```

### 4. Export Variable（导出变量）
```typescript
export const MY_CONSTANT = 42;
export let myVariable = 'test';
export var myVar = 100;
```

### 5. Export Enum（导出枚举）

**重要说明**: 由于 tree-sitter-arkts-open 解析器的限制，`export enum` 语法**无法正确解析**。

请使用以下替代方案：

**方案 A**: 使用 const 对象
```typescript
export const LoginTrigger = {
  LOGIN: 'third-login',
  LOGOUT: 'third-logout'
} as const;
```

**方案 B**: 分离声明和导出（如果支持）
```typescript
enum LoginTrigger {
  LOGIN = 'third-login'
}
// 注意：命名导出也可能不支持
```

详情请参考 [PARSER_LIMITATIONS.md](PARSER_LIMITATIONS.md)。

### 6. Export Type Alias（导出类型别名）
```typescript
export type MyType = string | number;
```

### 7. Export Default（默认导出）
```typescript
export default class DefaultClass {
  value: number = 0;
}
```

## 数据模型增强

### Symbol 模型新增字段

在 [`Symbol`](src/arkts_processor/models.py) 数据模型中新增了两个字段：

```python
@dataclass
class Symbol:
    # ... 其他字段 ...
    
    # Export 信息
    is_exported: bool = False          # 是否通过 export 导出
    is_export_default: bool = False    # 是否为 export default
```

### 数据库 Schema 更新

在 [`SymbolModel`](src/arkts_processor/database/schema.py) 中添加了对应的数据库字段：

```python
class SymbolModel(Base):
    # ... 其他字段 ...
    
    # Export 信息
    is_exported = Column(Boolean, default=False)
    is_export_default = Column(Boolean, default=False)
```

## 实现细节

### 1. SymbolExtractor 增强

在 [`SymbolExtractor`](src/arkts_processor/symbol_service/extractor.py) 中新增了以下方法：

- **`visit_export_declaration()`**: 处理 `export_declaration` AST 节点

**注意**: 由于 tree-sitter-arkts-open 的限制，`export enum` 无法正确解析。详情请参考 [PARSER_LIMITATIONS.md](PARSER_LIMITATIONS.md)。

### 2. Export 状态跟踪

提取器使用内部状态变量来跟踪当前是否在处理导出声明：

```python
self._current_is_exported = False
self._current_is_export_default = False
```

当进入 `export_declaration` 节点时，这些状态会被设置，并在处理完成后恢复。

### 3. 符号标记

所有支持的符号类型（class、interface、function、variable、enum、type_alias）在创建时都会检查并设置 export 状态：

```python
symbol.is_exported = getattr(self, '_current_is_exported', False)
symbol.is_export_default = getattr(self, '_current_is_export_default', False)
```

## 使用示例

### 基本用法

```python
import tree_sitter
import tree_sitter_arkts as ts_arkts
from arkts_processor.symbol_service.service import SymbolService

# 初始化服务
parser = tree_sitter.Parser(tree_sitter.Language(ts_arkts.language()))
symbol_service = SymbolService("my_symbols.db")
symbol_service.set_parser(parser)

# 处理文件
result = symbol_service.process_file("example.ets")

# 获取符号
symbols = symbol_service.repository.get_symbols_by_file("example.ets")

# 筛选导出的符号
exported_symbols = [s for s in symbols if s.is_exported]
for symbol in exported_symbols:
    print(f"{symbol.name} ({symbol.symbol_type.value})")
    if symbol.is_export_default:
        print("  -> 这是默认导出")
```

### 查询导出符号

```python
# 获取所有导出的类
exported_classes = [
    s for s in symbols 
    if s.symbol_type == SymbolType.CLASS and s.is_exported
]

# 获取默认导出
default_exports = [s for s in symbols if s.is_export_default]

# 获取非导出符号（私有符号）
private_symbols = [s for s in symbols if not s.is_exported]
```

### 与 ChunkService 集成

Export 信息会自动传递到 ChunkService，可以在生成的 chunks 中使用：

```python
from arkts_processor.chunk_service.service import ChunkService

chunk_service = ChunkService(symbol_service, "my_chunks.db")
chunks = chunk_service.generate_chunks("example.ets")

for chunk in chunks:
    # chunks 包含对应 symbol 的所有信息，包括 export 状态
    symbol = symbol_service.repository.get_symbol_by_id(chunk.symbol_id)
    if symbol and symbol.is_exported:
        print(f"Exported chunk: {chunk.name}")
```

## 测试验证

### 运行测试

项目包含多个测试文件来验证 export 功能：

```bash
# 测试 example.ets（包含 export enum）
python test_export.py

# 测试所有 export 类型
python test_all_exports.py

# 调试 export enum 的 AST 处理
python debug_export_enum.py
```

### 测试覆盖

- ✅ Export class
- ✅ Export interface  
- ✅ Export function
- ✅ Export const/let/var
- ❌ Export enum（解析器限制，不支持）
- ✅ Export type alias
- ✅ Export default
- ✅ 非导出符号正确标记

## 已知限制

### 1. Export Enum 不支持

由于 tree-sitter-arkts-open 解析器的限制，`export enum` 无法正确解析。

**建议的解决方案**:
- 使用 `const` 对象替代枚举
- 等待解析器更新
- 参考 [PARSER_LIMITATIONS.md](PARSER_LIMITATIONS.md) 了解详情

### 2. 嵌套导出

暂不支持复杂的嵌套导出模式，例如：

```typescript
export { MyClass, MyFunction };  // 不支持
export * from './other';         // 不支持
export { default as MyClass } from './other';  // 不支持
```

### 3. 动态导出

不支持运行时动态导出：

```typescript
if (condition) {
  export const value = 1;  // 条件导出不支持
}
```

## 未来改进方向

1. **等待解析器修复**: 关注 tree-sitter-arkts-open 项目更新，特别是 `export enum` 的支持
2. **支持命名导出**: 实现 `export { ... }` 语法支持
3. **支持重导出**: 实现 `export * from '...'` 语法支持
4. **导出分析**: 添加模块依赖分析，跟踪导出和导入的关系
5. **多解析器支持**: 考虑支持多种 ArkTS 解析器，根据需求选择最合适的

## 相关文件

- [`src/arkts_processor/models.py`](src/arkts_processor/models.py) - Symbol 数据模型
- [`src/arkts_processor/database/schema.py`](src/arkts_processor/database/schema.py) - 数据库 Schema
- [`src/arkts_processor/symbol_service/extractor.py`](src/arkts_processor/symbol_service/extractor.py) - 符号提取器
- [`src/arkts_processor/database/repository.py`](src/arkts_processor/database/repository.py) - 数据库仓储
- [`test_export.py`](test_export.py) - 基础测试
- [`test_all_exports.py`](test_all_exports.py) - 完整测试
- [`debug_export_enum.py`](debug_export_enum.py) - 调试工具

## 更新日志

### 2025-10-16
- ✅ 新增 `is_exported` 和 `is_export_default` 字段到 Symbol 模型
- ✅ 更新数据库 Schema 支持 export 字段
- ✅ 实现 `export_declaration` 节点处理
- ✅ 更新 Repository 保存和读取 export 信息
- ✅ 添加完整测试用例
- ✅ 创建文档说明
- ⚠️ 确认 `export enum` 由于解析器限制不支持
- ✅ 创建 [PARSER_LIMITATIONS.md](PARSER_LIMITATIONS.md) 说明解析器限制

## 贡献者

如需报告问题或贡献代码，请参考项目的 CONTRIBUTING.md 文件。

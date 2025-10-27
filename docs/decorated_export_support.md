# decorated_export_declaration 节点支持

## 概述

项目现已支持 `decorated_export_declaration` 节点的符号提取和 Chunk 生成。这种节点类型用于处理装饰器在 export 关键字之前的声明。

## 支持的语法

### 1. 装饰器导出组件 (Component)

```typescript
@Component
export struct MyComponent {
  @State count: number = 0;
  
  build() {
    Text(`Count: ${this.count}`)
  }
}
```

**特性：**
- 正确识别 `@Component` 装饰器
- 提取组件类型（Entry, Component, Preview等）
- 支持成员属性的装饰器（如 `@State`, `@Prop`, `@Link`）

### 2. 装饰器导出类 (Class)

```typescript
@Observed
export class DataModel {
  name: string = "";
  age: number = 0;
  
  updateName(newName: string): void {
    this.name = newName;
  }
}
```

**特性：**
- 识别通用装饰器（如 `@Observed`）
- 保存装饰器信息到符号的 `decorators` 字段
- 如果是 ArkUI 装饰器，同时保存到 `arkui_decorators` 字段

### 3. 装饰器导出函数 (Function)

```typescript
@Styles
export function globalButtonStyle() {
  .width('100%')
  .height(40)
  .backgroundColor('#007DFF')
}
```

**特性：**
- 识别 `@Styles` 等函数装饰器
- 自动识别为 `STYLE_FUNCTION` 类型
- 支持 ArkUI 样式函数特性

## AST 节点结构

`decorated_export_declaration` 节点的结构如下：

```
decorated_export_declaration
  ├── decorator (@Component, @Styles 等)
  ├── export (关键字)
  ├── class/function/struct (关键字)
  ├── identifier (名称)
  └── body (class_body/component_body/function_body 等)
```

## 实现细节

### 符号提取器 (SymbolExtractor)

新增以下方法：

1. **`visit_decorated_export_declaration(node)`**
   - 主入口方法，处理 `decorated_export_declaration` 节点
   - 提取装饰器信息
   - 根据子节点类型分发到具体处理方法

2. **`_extract_decorated_export_component(node, decorators)`**
   - 处理组件声明
   - 提取 ArkUI 装饰器
   - 确定组件类型

3. **`_extract_decorated_export_class(node, decorators)`**
   - 处理类声明
   - 保存装饰器信息
   - 提取继承和实现关系

4. **`_extract_decorated_export_function(node, decorators)`**
   - 处理函数声明
   - 识别样式函数
   - 提取参数和返回类型

### 数据持久化

**ArkUI 元数据存储：**

符号的 ArkUI 相关字段（`arkui_decorators`, `component_type`, `style_bindings` 等）被保存到数据库的 `meta_data` JSON 字段中：

```python
meta_data = {
    'arkui_decorators': {'Component': [], 'State': []},
    'component_type': 'Component',
    'style_bindings': [],
    'event_handlers': {},
    'resource_refs': []
}
```

**Repository 修改：**

- [`save_symbol`](file:///Users/million_mo/projects/stunning-octo-chainsaw/src/arkts_processor/database/repository.py#L140-L190) 方法：将 ArkUI 字段保存到 `meta_data`
- [`save_symbols_batch`](file:///Users/million_mo/projects/stunning-octo-chainsaw/src/arkts_processor/database/repository.py#L289-L350) 方法：批量保存时同样处理 ArkUI 字段
- [`_symbol_model_to_entity`](file:///Users/million_mo/projects/stunning-octo-chainsaw/src/arkts_processor/database/repository.py#L349-L410) 方法：从 `meta_data` 恢复 ArkUI 字段

## 测试

测试文件：[`tests/test_decorated_export.py`](file:///Users/million_mo/projects/stunning-octo-chainsaw/tests/test_decorated_export.py)

运行测试：

```bash
.conda/bin/python tests/test_decorated_export.py
```

**测试覆盖：**

- ✅ `@Component export struct` - 组件声明
- ✅ `@Observed export class` - 类声明
- ✅ 符号提取正确性
- ✅ 装饰器信息保存
- ✅ Chunk 生成

## 与其他 export 形式的对比

### 1. export_statement / export_declaration

```typescript
export class MyClass { }
export const value = 1;
```

由 [`visit_export_statement`](file:///Users/million_mo/projects/stunning-octo-chainsaw/src/arkts_processor/symbol_service/extractor.py#L145-L184) 和 [`visit_export_declaration`](file:///Users/million_mo/projects/stunning-octo-chainsaw/src/arkts_processor/symbol_service/extractor.py#L186-L201) 方法处理。

### 2. decorated_export_declaration

```typescript
@Component
export struct MyComponent { }
```

由新增的 [`visit_decorated_export_declaration`](file:///Users/million_mo/projects/stunning-octo-chainsaw/src/arkts_processor/symbol_service/extractor.py#L203-L263) 方法处理。

### 3. export + 装饰器

```typescript
export @Component
class TestComponent { }
```

由 [`visit_export_declaration`](file:///Users/million_mo/projects/stunning-octo-chainsaw/src/arkts_processor/symbol_service/extractor.py#L186-L201) 方法处理，会遍历子节点并识别带装饰器的声明。

## 兼容性

- tree-sitter-arkts-open >= 0.1.8
- 兼容现有的 export 处理逻辑
- 保持向后兼容

## 相关文件

- 符号提取器：[`src/arkts_processor/symbol_service/extractor.py`](file:///Users/million_mo/projects/stunning-octo-chainsaw/src/arkts_processor/symbol_service/extractor.py)
- 数据库仓库：[`src/arkts_processor/database/repository.py`](file:///Users/million_mo/projects/stunning-octo-chainsaw/src/arkts_processor/database/repository.py)
- 测试文件：[`tests/test_decorated_export.py`](file:///Users/million_mo/projects/stunning-octo-chainsaw/tests/test_decorated_export.py)
- AST 检查脚本：[`scripts/inspect_decorated_export.py`](file:///Users/million_mo/projects/stunning-octo-chainsaw/scripts/inspect_decorated_export.py)

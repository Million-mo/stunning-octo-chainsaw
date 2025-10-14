# ArkUI 支持快速参考

## 🎯 新增符号类型

| 符号类型 | 用途 | 示例 |
|---------|------|------|
| `COMPONENT` | ArkUI 组件 | `@Component struct MyComponent {}` |
| `BUILD_METHOD` | UI 构建方法 | `build() { ... }` |
| `STYLE_FUNCTION` | 样式函数 | `@Styles cardStyle() {}` |
| `EXTEND_FUNCTION` | 组件扩展 | `@Extend(Text) fancy() {}` |
| `LIFECYCLE_METHOD` | 生命周期 | `aboutToAppear() {}` |

## 🏷️ 支持的装饰器

### 组件装饰器
```typescript
@Entry          // 入口组件
@Component      // 自定义组件
@Preview        // 预览组件
@CustomDialog   // 自定义对话框
```

### 状态管理
```typescript
@State          // 组件内状态
@Prop           // 单向传递
@Link           // 双向绑定
@Provide        // 提供数据
@Consume        // 消费数据
@Watch('fn')    // 状态监听
@StorageLink('key')  // 应用级状态
```

### 样式相关
```typescript
@Styles         // 样式函数
@Extend(Text)   // 组件扩展
```

## 📦 Symbol 新增字段

```python
symbol.arkui_decorators  # Dict[str, Any] - 装饰器详情
symbol.component_type    # str - 组件类型
symbol.style_bindings    # List[str] - 样式绑定
symbol.event_handlers    # Dict[str, str] - 事件处理
symbol.resource_refs     # List[str] - 资源引用
```

## 🔍 快速查询

### 查找 Entry 组件
```python
entry = [s for s in symbols 
         if s.symbol_type == SymbolType.COMPONENT 
         and s.component_type == "Entry"]
```

### 查找所有状态属性
```python
states = [s for s in symbols 
          if "State" in s.arkui_decorators]
```

### 查找 build 方法
```python
builds = [s for s in symbols 
          if s.symbol_type == SymbolType.BUILD_METHOD]
```

## 🎨 提取的 UI 信息

### 样式绑定
```typescript
Text('Hello')
  .fontSize(50)    // ✅ 提取
  .fontColor(Color.Red)  // ✅ 提取
```

### 事件处理
```typescript
Button('Click')
  .onClick(() => {...})  // ✅ 提取事件和处理器
```

### 资源引用
```typescript
Image($r('app.media.icon'))  // ✅ 提取 "app.media.icon"
```

## ⚡ 使用示例

```python
from arkts_processor.symbol_service.extractor import SymbolExtractor

# 提取符号
extractor = SymbolExtractor("MyComponent.ets", code)
symbols = extractor.extract(tree)

# 分析组件
for symbol in symbols:
    if symbol.symbol_type == SymbolType.COMPONENT:
        print(f"组件: {symbol.name}")
        print(f"  类型: {symbol.component_type}")
        print(f"  装饰器: {list(symbol.arkui_decorators.keys())}")
    
    elif symbol.symbol_type == SymbolType.PROPERTY:
        if symbol.arkui_decorators:
            decorators = ", ".join(f"@{k}" for k in symbol.arkui_decorators.keys())
            print(f"属性: {symbol.name} ({decorators})")
    
    elif symbol.symbol_type == SymbolType.BUILD_METHOD:
        print(f"Build 方法:")
        print(f"  样式: {symbol.style_bindings}")
        print(f"  事件: {list(symbol.event_handlers.keys())}")
        print(f"  资源: {symbol.resource_refs}")
```

## ✅ 测试验证

```bash
# 运行 ArkUI 测试
python test_arkui_support.py

# 运行所有测试
pytest tests/test_extractor.py -v
```

## 📚 更多信息

- 详细文档: [ARKUI_SUPPORT_SUMMARY.md](ARKUI_SUPPORT_SUMMARY.md)
- AST 分析: [AST_ANALYSIS_SUMMARY.md](AST_ANALYSIS_SUMMARY.md)
- 原始修复: [EXTRACTOR_FIX_REPORT.md](EXTRACTOR_FIX_REPORT.md)

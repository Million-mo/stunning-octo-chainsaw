#!/usr/bin/env python3
"""
测试 ArkUI 特性支持
"""

import tree_sitter_arkts as ts_arkts
from tree_sitter import Language, Parser
from arkts_processor.symbol_service.extractor import SymbolExtractor

# 初始化解析器
ARKTS_LANGUAGE = Language(ts_arkts.language())
parser = Parser(ARKTS_LANGUAGE)

# 测试代码
test_code_str = """
@Entry
@Component
struct MyComponent {
  @State message: string = 'Hello World';
  @Prop title: string;
  @Link count: number;
  @StorageLink('theme') theme: string = 'light';
  @Watch('onValueChange') watchedValue: string = '';
  
  @Styles
  cardStyle() {
    .width('100%')
    .height(100)
    .backgroundColor(Color.White)
  }
  
  aboutToAppear() {
    console.log('Component is about to appear');
  }
  
  onValueChange(oldValue: string, newValue: string) {
    console.log(`Value changed: ${oldValue} -> ${newValue}`);
  }
  
  build() {
    Column() {
      Text(this.message)
        .fontSize(50)
        .fontWeight(FontWeight.Bold)
        .onClick(() => {
          this.message = 'Hello ArkUI';
        })
      
      Button('Click Me')
        .width('80%')
        .height(40)
        .onClick(this.handleClick.bind(this))
      
      Image($r('app.media.icon'))
        .width(50)
        .height(50)
    }
    .cardStyle()
  }
  
  private handleClick() {
    this.count++;
  }
}

@Component
struct CustomButton {
  @Prop label: string = 'Button';
  
  build() {
    Button(this.label)
  }
}

@Preview
struct PreviewComponent {
  build() {
    MyComponent({ title: 'Preview', count: 0 })
  }
}
"""

test_code = test_code_str.encode('utf-8')

print("=" * 80)
print("测试 ArkUI 特性支持")
print("=" * 80)

# 解析代码
tree = parser.parse(test_code)

# 提取符号
extractor = SymbolExtractor("test.ets", test_code)
symbols = extractor.extract(tree)

print(f"\n提取到 {len(symbols)} 个符号:\n")

for symbol in symbols:
    print(f"{'─' * 80}")
    print(f"符号类型: {symbol.symbol_type.value:20s} | 名称: {symbol.name}")
    print(f"位置: Line {symbol.range.start.line}, Column {symbol.range.start.column}")
    
    # 显示组件类型
    if symbol.component_type:
        print(f"  └─ 组件类型: {symbol.component_type}")
    
    # 显示 ArkUI 装饰器
    if symbol.arkui_decorators:
        decorators_str = ", ".join([f"@{k}" + (f"({v})" if v else "") 
                                   for k, v in symbol.arkui_decorators.items()])
        print(f"  └─ ArkUI 装饰器: {decorators_str}")
    
    # 显示继承
    if symbol.extends:
        print(f"  └─ 继承: {', '.join(symbol.extends)}")
    
    # 显示参数
    if symbol.parameters:
        params = ', '.join([f"{p.name}: {p.type_info.name if p.type_info else '?'}" 
                           for p in symbol.parameters])
        print(f"  └─ 参数: ({params})")
    
    # 显示返回类型
    if symbol.return_type:
        print(f"  └─ 返回类型: {symbol.return_type.name}")
    
    # 显示类型
    if symbol.type_info:
        print(f"  └─ 类型: {symbol.type_info.name}")
    
    # 显示样式绑定
    if symbol.style_bindings:
        print(f"  └─ 样式绑定: {', '.join(symbol.style_bindings)}")
    
    # 显示事件处理器
    if symbol.event_handlers:
        for event, handler in symbol.event_handlers.items():
            print(f"  └─ 事件: {event} -> {handler}")
    
    # 显示资源引用
    if symbol.resource_refs:
        print(f"  └─ 资源引用: {', '.join(symbol.resource_refs)}")

print("\n" + "=" * 80)
print("测试完成！")
print("=" * 80)

# 统计信息
from collections import Counter
type_counts = Counter([s.symbol_type.value for s in symbols])
print("\n符号类型统计:")
for symbol_type, count in sorted(type_counts.items()):
    print(f"  {symbol_type:20s}: {count}")

# ArkUI 装饰器统计
decorator_counts = Counter()
for symbol in symbols:
    for decorator_name in symbol.arkui_decorators.keys():
        decorator_counts[decorator_name] += 1

if decorator_counts:
    print("\nArkUI 装饰器统计:")
    for decorator, count in sorted(decorator_counts.items()):
        print(f"  @{decorator:20s}: {count}")

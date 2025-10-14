#!/usr/bin/env python3
"""
检查 ArkUI 特有语法的 AST 结构
"""

import tree_sitter_arkts as ts_arkts
from tree_sitter import Language, Parser

# 初始化解析器
ARKTS_LANGUAGE = Language(ts_arkts.language())
parser = Parser(ARKTS_LANGUAGE)

def print_tree(node, indent=0, source_code=None, max_depth=4):
    """递归打印AST树结构"""
    if indent > max_depth:
        return
        
    prefix = "  " * indent
    node_text = ""
    if source_code and indent < 3:
        node_text = source_code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
        if len(node_text) > 40:
            node_text = node_text[:40] + "..."
        node_text = f" | Text: {repr(node_text)}"
    
    print(f"{prefix}{node.type}{node_text}")
    
    for child in node.children:
        print_tree(child, indent + 1, source_code, max_depth)

# ArkUI 特性测试用例
test_cases = [
    ("装饰器 @Entry @Component", b"""
@Entry
@Component
struct MyComponent {
  @State message: string = 'Hello';
}
"""),
    ("@State 装饰器", b"""
struct Test {
  @State count: number = 0;
  @Prop title: string;
  @Link data: any;
}
"""),
    ("@Styles 样式函数", b"""
struct Test {
  @Styles
  cardStyle() {
    .width('100%')
  }
}
"""),
    ("@Extend 扩展", b"""
@Extend(Text)
fancyText(color: Color) {
  .fontSize(20)
}
"""),
    ("build 函数", b"""
struct Test {
  build() {
    Column() {
      Text('Hello')
    }
  }
}
"""),
    ("struct 声明", b"""
@Component
struct MyStruct {
  @State value: number = 0;
  
  build() {
    Text('test')
  }
}
"""),
]

print("=" * 80)
print("ArkUI 特有语法 AST 结构分析")
print("=" * 80)

for name, code in test_cases:
    print(f"\n{'='*80}")
    print(f"测试: {name}")
    print(f"{'='*80}")
    print("源代码:")
    print(code.decode('utf-8'))
    print("\nAST 结构:")
    
    tree = parser.parse(code)
    print_tree(tree.root_node, source_code=code)
    print()

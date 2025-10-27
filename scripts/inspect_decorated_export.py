#!/usr/bin/env python3
"""
检查 decorated_export_declaration 节点的 AST 结构
"""

import sys
from tree_sitter_arkts import language


def get_parser():
    """获取解析器"""
    from tree_sitter import Parser, Language
    parser = Parser(Language(language()))
    return parser


def print_tree(node, source_code, indent=0):
    """打印AST树"""
    prefix = "  " * indent
    node_text = source_code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
    # 限制显示长度
    if len(node_text) > 50:
        node_text = node_text[:50] + "..."
    # 替换换行符
    node_text = node_text.replace('\n', '\\n')
    
    print(f"{prefix}{node.type} [{node.start_point[0]}:{node.start_point[1]}-{node.end_point[0]}:{node.end_point[1]}]")
    if node_text.strip():
        print(f"{prefix}  → {repr(node_text)}")
    
    for child in node.children:
        print_tree(child, source_code, indent + 1)


# 测试用例
test_cases = [
    ("decorated export class", b"""
@Component
export class MyComponent {
  name: string = "test";
}
"""),
    ("decorated export struct", b"""
@Component
export struct MyStruct {
  @State count: number = 0;
  build() {}
}
"""),
    ("decorated export function", b"""
@Styles
export function globalStyles() {
  .width(100)
}
"""),
    ("export decorated class", b"""
export @Component
class TestComponent {
  value: number = 0;
}
"""),
]

parser = get_parser()

print("=" * 80)
print("decorated_export_declaration 节点检查")
print("=" * 80)

for name, code in test_cases:
    print(f"\n{'='*80}")
    print(f"测试用例: {name}")
    print(f"{'='*80}")
    print(f"源代码:")
    print(code.decode('utf-8'))
    print(f"\nAST 结构:")
    
    tree = parser.parse(code)
    print_tree(tree.root_node, source_code=code)
    print()

print(f"\n{'='*80}")
print("✅ 检查完成")
print(f"{'='*80}")

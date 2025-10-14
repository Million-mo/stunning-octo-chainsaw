#!/usr/bin/env python3
"""
检查 tree-sitter-arkts 的实际 AST 结构
"""

import tree_sitter_arkts as ts_arkts
from tree_sitter import Language, Parser

# 初始化解析器
ARKTS_LANGUAGE = Language(ts_arkts.language())
parser = Parser(ARKTS_LANGUAGE)

def print_tree(node, indent=0, source_code=None):
    """递归打印AST树结构"""
    prefix = "  " * indent
    node_text = ""
    if source_code:
        node_text = source_code[node.start_byte:node.end_byte].decode('utf-8', errors='ignore')
        # 限制文本长度
        if len(node_text) > 50:
            node_text = node_text[:50] + "..."
        node_text = f" | Text: {repr(node_text)}"
    
    # 打印节点信息
    print(f"{prefix}{node.type} [{node.start_point}-{node.end_point}]{node_text}")
    
    # 打印字段信息
    if hasattr(node, 'children_by_field_name'):
        fields = {}
        for field_name in ['name', 'type', 'parameters', 'return_type', 'body', 'heritage', 'value', 'pattern', 'element']:
            field_node = node.child_by_field_name(field_name)
            if field_node:
                fields[field_name] = field_node.type
        if fields:
            print(f"{prefix}  [Fields: {fields}]")
    
    # 递归打印子节点
    for child in node.children:
        print_tree(child, indent + 1, source_code)

# 测试用例
test_cases = [
    ("class_declaration", b"""
export class MyClass extends BaseClass implements IMyInterface {
    private name: string;
    
    constructor(name: string) {
        this.name = name;
    }
    
    public getName(): string {
        return this.name;
    }
}
"""),
    ("interface_declaration", b"""
interface Person {
    name: string;
    age: number;
    greet(): void;
}
"""),
    ("function_declaration", b"""
function add(a: number, b: number): number {
    return a + b;
}
"""),
    ("method_definition", b"""
class Test {
    async testMethod(param: string): Promise<void> {
        console.log(param);
    }
}
"""),
    ("variable_declaration", b"""
const PI: number = 3.14159;
let counter: number = 0;
var message: string = "Hello";
"""),
    ("enum_declaration", b"""
enum Color {
    Red = 0,
    Green = 1,
    Blue = 2
}
"""),
    ("type_alias", b"""
type StringOrNumber = string | number;
"""),
]

print("=" * 80)
print("Tree-sitter-arkts AST 结构分析")
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

# 额外测试：检查根节点类型
simple_code = b"class Test {}"
tree = parser.parse(simple_code)
print(f"\n{'='*80}")
print(f"根节点类型: {tree.root_node.type}")
print(f"{'='*80}")

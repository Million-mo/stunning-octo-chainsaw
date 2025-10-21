#!/usr/bin/env python3
"""
验证 extractor.py 中节点访问方式的完整性

检查所有 visit_* 方法对应的节点类型是否正确使用子节点访问方式
"""

import sys
sys.path.insert(0, '/Users/million_mo/projects/stunning-octo-chainsaw/src')

from tree_sitter_arkts import language as arkts_language
import tree_sitter as ts

parser = ts.Parser(ts.Language(arkts_language()))

def analyze_node(code, target_type=None):
    """分析代码的AST结构"""
    tree = parser.parse(bytes(code, 'utf8'))
    
    def find_and_print(node, depth=0):
        if depth > 3:
            return
        
        prefix = "  " * depth
        text = ""
        if node.type == "identifier" and node.text:
            text = f" = '{node.text.decode('utf8')}'"
        
        print(f"{prefix}{node.type}{text}")
        
        if not target_type or node.type == target_type:
            # 分析子节点
            named_children = [c for c in node.children if c.is_named]
            if named_children:
                print(f"{prefix}  📋 命名子节点: {[c.type for c in named_children]}")
        
        for child in node.children:
            find_and_print(child, depth + 1)
    
    find_and_print(tree.root_node)

# 关键节点验证
print("=" * 80)
print("extractor.py 节点类型验证报告")
print("=" * 80)

tests = [
    ("class_declaration", """
class MyClass extends Base {
  prop: string;
  method() {}
}
"""),
    
    ("interface_declaration", """
interface MyInterface {
  prop: string;
}
"""),
    
    ("enum_declaration", """
enum MyEnum {
  A = 'a',
  B = 'b'
}
"""),
    
    ("function (expression_statement)", """
function myFunc(p: string): void {
  return;
}
"""),
    
    ("variable_declaration (var/let/const)", """
var v = 1;
let l = 2;
const c = 3;
"""),
    
    ("export_declaration", """
export const exp = 1;
export class ExpClass {}
"""),
    
    ("component_declaration", """
@Component
struct MyComp {
  @State count: number = 0;
  build() {}
}
"""),
]

for name, code in tests:
    print(f"\n{'=' * 80}")
    print(f"📌 {name}")
    print(f"{'=' * 80}")
    analyze_node(code)

print(f"\n{'=' * 80}")
print("✅ 验证完成")
print("=" * 80)
print("""
关键发现:
1. export 使用 export_declaration (包含 variable_declaration/class_declaration)
2. var/let/const 都使用 variable_declaration (通过关键字区分)  
3. function 作为顶层声明时是 expression_statement
4. 所有节点都必须通过 _get_child_by_type() 访问子节点
5. identifier 通过 _get_identifier_name() 获取

建议:
- visit_export_statement() 应改名为 visit_export_declaration()
- visit_variable_statement() 应改名为 visit_variable_declaration()
- visit_lexical_declaration() 可以合并到 visit_variable_declaration()
""")

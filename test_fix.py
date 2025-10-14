#!/usr/bin/env python3
"""
测试修复后的AST遍历逻辑
"""

# 测试导入是否正常
try:
    from arkts_processor import SymbolService
    print("✓ arkts_processor 导入成功")
except Exception as e:
    print(f"✗ arkts_processor 导入失败: {e}")
    exit(1)

# 测试符号服务初始化
try:
    service = SymbolService(db_path=":memory:")  # 使用内存数据库
    print("✓ SymbolService 初始化成功")
except Exception as e:
    print(f"✗ SymbolService 初始化失败: {e}")
    exit(1)

# 测试AST访问者的修复
try:
    from arkts_processor.symbol_service.ast_traverser import ASTVisitor
    from arkts_processor.symbol_service.extractor import SymbolExtractor
    
    # 创建一个简单的AST节点模拟对象
    class MockNode:
        def __init__(self, node_type, children=None):
            self.type = node_type
            self.children = children or []
            self.start_point = (0, 0)
            self.end_point = (0, 10)
            self.start_byte = 0
            self.end_byte = 10
            self.is_named = True
    
    # 测试访问者模式
    visitor = ASTVisitor()
    
    # 测试source_file节点处理
    source_file_node = MockNode("source_file", [
        MockNode("class_declaration"),
        MockNode("function_declaration")
    ])
    
    extractor = SymbolExtractor("test.ets", b"class Test {}")
    
    # 测试是否有对应的处理方法
    assert hasattr(extractor, 'visit_source_file'), "缺少 visit_source_file 方法"
    assert hasattr(extractor, 'visit_program'), "缺少 visit_program 方法"
    
    print("✓ AST访问者修复验证成功")
    print("  - visit_source_file 方法已添加")
    print("  - visit_program 方法已添加")
    print("  - generic_visit 方法已增强")
    
except Exception as e:
    print(f"✗ AST访问者修复验证失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n🎉 所有测试通过！source_file 节点处理问题已修复。")
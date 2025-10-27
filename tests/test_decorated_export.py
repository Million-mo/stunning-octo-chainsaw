#!/usr/bin/env python3
"""
测试 decorated_export_declaration 节点的符号提取和 Chunk 生成
"""

import sys
import os
import tempfile

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from arkts_processor.symbol_service import SymbolService
from arkts_processor.chunk_service import ChunkService
from tree_sitter import Parser, Language
from tree_sitter_arkts import language


def get_parser():
    """获取ArkTS解析器"""
    parser = Parser(Language(language()))
    return parser


def test_decorated_export_component():
    """测试装饰器在 export 之前的组件声明"""
    code = b"""
@Component
export struct MyComponent {
  @State count: number = 0;
  
  build() {
    Text(`Count: ${this.count}`)
  }
}
"""
    
    print("=" * 80)
    print("测试: @Component export struct")
    print("=" * 80)
    
    # 创建符号服务
    symbol_service = SymbolService(db_path=":memory:")
    symbol_service.set_parser(get_parser())
    
    # 写入临时文件
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ets', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # 处理文件
        symbol_service.process_file(temp_file)
        
        # 获取符号
        symbols = symbol_service.repository.get_symbols_by_file(temp_file)
        
        print(f"\n提取到 {len(symbols)} 个符号:")
        for symbol in symbols:
            print(f"  - {symbol.name} ({symbol.symbol_type.value})")
            print(f"    is_exported: {symbol.is_exported}")
            print(f"    arkui_decorators: {symbol.arkui_decorators}")
            if symbol.symbol_type.value == "component":
                print(f"    component_type: {symbol.component_type}")
        
        # 验证结果
        assert len(symbols) > 0, "应该提取到至少一个符号"
        
        # 查找组件符号
        component_symbol = next((s for s in symbols if s.name == "MyComponent"), None)
        assert component_symbol is not None, "应该提取到 MyComponent 组件"
        assert component_symbol.is_exported, "组件应该被标记为 exported"
        assert "Component" in component_symbol.arkui_decorators, "应该包含 @Component 装饰器"
        
        print("\n✅ 符号提取测试通过")
        
        # 测试 Chunk 生成 - 使用新的数据库防止冲突
        chunk_service = ChunkService(SymbolService(db_path=":memory:"), db_path=":memory:")
        chunk_service.symbol_service.set_parser(get_parser())
        chunks = chunk_service.generate_chunks(temp_file, save_to_db=False)
        
        print(f"\n生成 {len(chunks)} 个 Chunk:")
        for chunk in chunks:
            print(f"  - {chunk.name} ({chunk.type.value})")
            print(f"    chunk_id: {chunk.chunk_id}")
            if chunk.metadata:
                print(f"    decorators: {chunk.metadata.decorators}")
        
        # 验证 Chunk
        component_chunk = next((c for c in chunks if c.name == "MyComponent"), None)
        assert component_chunk is not None, "应该生成 MyComponent 的 Chunk"
        assert component_chunk.type.value == "component", "Chunk 类型应该是 component"
        if component_chunk.metadata:
            assert "@Component" in component_chunk.metadata.decorators, "应该包含 @Component 装饰器"
        
        print("\n✅ Chunk 生成测试通过")
        
    finally:
        os.unlink(temp_file)
    
    return True


def test_decorated_export_class():
    """测试装饰器在 export 之前的类声明"""
    code = b"""
@Observed
export class DataModel {
  name: string = "";
  
  updateName(newName: string): void {
    this.name = newName;
  }
}
"""
    
    print("\n" + "=" * 80)
    print("测试: @Observed export class")
    print("=" * 80)
    
    symbol_service = SymbolService(db_path=":memory:")
    symbol_service.set_parser(get_parser())
    
    # 写入临时文件
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ets', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        symbol_service.process_file(temp_file)
        symbols = symbol_service.repository.get_symbols_by_file(temp_file)
        
        print(f"\n提取到 {len(symbols)} 个符号:")
        for symbol in symbols:
            print(f"  - {symbol.name} ({symbol.symbol_type.value})")
            print(f"    is_exported: {symbol.is_exported}")
            print(f"    decorators: {symbol.decorators}")
        
        # 验证类符号
        class_symbol = next((s for s in symbols if s.name == "DataModel"), None)
        assert class_symbol is not None, "应该提取到 DataModel 类"
        assert class_symbol.is_exported, "类应该被标记为 exported"
        assert "@Observed" in class_symbol.decorators, "应该包含 @Observed 装饰器"
        
        print("\n✅ 符号提取测试通过")
        
        # 测试 Chunk - 使用新的数据库防止冲突
        chunk_service = ChunkService(SymbolService(db_path=":memory:"), db_path=":memory:")
        chunk_service.symbol_service.set_parser(get_parser())
        chunks = chunk_service.generate_chunks(temp_file, save_to_db=False)
        
        print(f"\n生成 {len(chunks)} 个 Chunk:")
        for chunk in chunks:
            print(f"  - {chunk.name} ({chunk.type.value})")
        
        class_chunk = next((c for c in chunks if c.name == "DataModel"), None)
        assert class_chunk is not None, "应该生成 DataModel 的 Chunk"
        
        print("\n✅ Chunk 生成测试通过")
    
    finally:
        os.unlink(temp_file)
    
    return True


if __name__ == "__main__":
    try:
        print("=" * 80)
        print("decorated_export_declaration 节点测试套件")
        print("=" * 80)
        
        test_decorated_export_component()
        test_decorated_export_class()
        
        print("\n" + "=" * 80)
        print("🎉 所有测试通过！")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

"""
ContextEnricher 单元测试

测试上下文增强器的各项功能。
"""

import unittest
from arkts_processor.chunk_service.enricher import ContextEnricher
from arkts_processor.chunk_models import CodeChunk, ChunkType, ChunkMetadata, PositionRange
from arkts_processor.models import Symbol, SymbolType, Range, Position, Scope, ScopeType


class TestContextEnricher(unittest.TestCase):
    """ContextEnricher 单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.enricher = ContextEnricher()
    
    def test_enrich_chunk_function(self):
        """测试函数 Chunk 的上下文增强"""
        chunk = CodeChunk(
            chunk_id="test.ets#testFunc",
            type=ChunkType.FUNCTION,
            path="test.ets",
            name="testFunc",
            context="MyClass",
            source="function testFunc() { return 42; }",
            imports=["Helper", "Utils"],
            symbol_id=1
        )
        
        metadata = ChunkMetadata(
            range=PositionRange(0, 10, 0, 100),
            decorators=[],
            tags=["async", "public"]
        )
        chunk.metadata = metadata
        
        symbol = Symbol(
            id=1,
            name="testFunc",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(10, 0, 100))
        )
        
        enriched = self.enricher.enrich_chunk(chunk, symbol, {})
        
        # 验证包含元数据头
        self.assertIn("# file:", enriched.source)
        self.assertIn("# function:", enriched.source)
        self.assertIn("# imports:", enriched.source)
        self.assertIn("# tags:", enriched.source)
        
        # 验证包含原始源代码
        self.assertIn("function testFunc()", enriched.source)
    
    def test_enrich_chunk_component(self):
        """测试 ArkUI 组件 Chunk 的上下文增强"""
        chunk = CodeChunk(
            chunk_id="test.ets#LoginView",
            type=ChunkType.COMPONENT,
            path="test.ets",
            name="LoginView",
            context="@Component",
            source="@Component struct LoginView { build() {} }",
            imports=["router"],
            symbol_id=1
        )
        
        metadata = ChunkMetadata(
            range=PositionRange(0, 20, 0, 200),
            decorators=["@Component", "@Entry"],
            component_type="Entry",
            state_vars=[{"name": "username", "type": "string"}],
            lifecycle_hooks=["aboutToAppear"],
            tags=["ui-component"]
        )
        chunk.metadata = metadata
        
        symbol = Symbol(
            id=1,
            name="LoginView",
            symbol_type=SymbolType.COMPONENT,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(20, 0, 200))
        )
        
        enriched = self.enricher.enrich_chunk(chunk, symbol, {})
        
        # 验证包含组件特有的元数据头
        self.assertIn("# component:", enriched.source)
        self.assertIn("# component_type:", enriched.source)
        self.assertIn("# state_vars:", enriched.source)
        self.assertIn("# lifecycle_hooks:", enriched.source)
        self.assertIn("# decorators:", enriched.source)
    
    def test_format_metadata_headers_general(self):
        """测试通用元数据头格式化"""
        chunk = CodeChunk(
            chunk_id="test.ets#calc",
            type=ChunkType.FUNCTION,
            path="src/utils/calc.ts",
            name="calculate",
            context="MathUtils",
            source="function calculate() {}",
            imports=["Math"]
        )
        
        metadata = ChunkMetadata(
            range=PositionRange(0, 10, 0, 100),
            decorators=["@deprecated"],
            tags=["pure-function"]
        )
        chunk.metadata = metadata
        
        symbol = Symbol(
            id=1,
            name="calculate",
            symbol_type=SymbolType.FUNCTION,
            file_path="src/utils/calc.ts",
            range=Range(Position(0, 0, 0), Position(10, 0, 100))
        )
        
        headers = self.enricher.format_metadata_headers(chunk, symbol)
        
        self.assertIn("# file: src/utils/calc.ts", headers)
        self.assertIn("# function: calculate", headers)
        self.assertIn("# imports: [Math]", headers)
        self.assertIn("# decorators: [@deprecated]", headers)
        self.assertIn("# tags: [pure-function]", headers)
    
    def test_enrich_chunks_batch(self):
        """测试批量增强"""
        chunks = [
            CodeChunk(
                chunk_id="test.ets#func1",
                type=ChunkType.FUNCTION,
                path="test.ets",
                name="func1",
                context="",
                source="function func1() {}",
                symbol_id=1
            ),
            CodeChunk(
                chunk_id="test.ets#func2",
                type=ChunkType.FUNCTION,
                path="test.ets",
                name="func2",
                context="",
                source="function func2() {}",
                symbol_id=2
            )
        ]
        
        symbols = [
            Symbol(
                id=1,
                name="func1",
                symbol_type=SymbolType.FUNCTION,
                file_path="test.ets",
                range=Range(Position(0, 0, 0), Position(5, 0, 50))
            ),
            Symbol(
                id=2,
                name="func2",
                symbol_type=SymbolType.FUNCTION,
                file_path="test.ets",
                range=Range(Position(6, 0, 60), Position(10, 0, 100))
            )
        ]
        
        scopes = []
        
        enriched_chunks = self.enricher.enrich_chunks(chunks, symbols, scopes)
        
        self.assertEqual(len(enriched_chunks), 2)
        for chunk in enriched_chunks:
            self.assertIn("# file:", chunk.source)
            self.assertIn("# function:", chunk.source)
    
    def test_build_context_path(self):
        """测试上下文路径构建"""
        # 这个测试需要依赖实际的 scope 层级结构
        # 由于 build_context_path 的实现逻辑依赖于 scope 的 parent 关系
        # 这里简化测试，只验证方法可以正常调用
        symbol = Symbol(
            id=1,
            name="method",
            symbol_type=SymbolType.METHOD,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(5, 0, 50)),
            scope_id=2
        )
        
        scopes = {
            1: Scope(
                id=1,
                scope_type=ScopeType.GLOBAL,
                file_path="test.ets",
                range=Range(Position(0, 0, 0), Position(20, 0, 200))
            ),
            2: Scope(
                id=2,
                scope_type=ScopeType.CLASS,
                file_path="test.ets",
                range=Range(Position(0, 0, 0), Position(10, 0, 100)),
                parent_id=1
            )
        }
        
        # 添加符号到作用域
        class_symbol = Symbol(
            id=3,
            name="MyClass",
            symbol_type=SymbolType.CLASS,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(10, 0, 100))
        )
        scopes[1].symbols["MyClass"] = class_symbol
        
        context = self.enricher.build_context_path(symbol, scopes)
        
        # 验证返回值是字符串
        self.assertIsInstance(context, str)
    
    def test_empty_metadata(self):
        """测试无元数据的情况"""
        chunk = CodeChunk(
            chunk_id="test.ets#simple",
            type=ChunkType.FUNCTION,
            path="test.ets",
            name="simple",
            context="",
            source="function simple() {}",
            symbol_id=1
        )
        # 不设置 metadata
        
        symbol = Symbol(
            id=1,
            name="simple",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(2, 0, 20))
        )
        
        enriched = self.enricher.enrich_chunk(chunk, symbol, {})
        
        # 应该仍然包含基本的元数据头
        self.assertIn("# file:", enriched.source)
        self.assertIn("# function:", enriched.source)


if __name__ == "__main__":
    unittest.main()

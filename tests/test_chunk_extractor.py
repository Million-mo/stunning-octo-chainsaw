"""
ChunkExtractor 单元测试

测试 Chunk 提取器的各项功能。
"""

import unittest
from arkts_processor.chunk_service.extractor import ChunkExtractor
from arkts_processor.models import Symbol, SymbolType, Range, Position, Scope, ScopeType, Visibility
from arkts_processor.chunk_models import ChunkType


class TestChunkExtractor(unittest.TestCase):
    """ChunkExtractor 单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.source_code = b"""
function test() {
    return 42;
}

class MyClass {
    method() {}
}
"""
        self.extractor = ChunkExtractor("test.ets", self.source_code)
    
    def test_is_chunkable(self):
        """测试是否可分块判断"""
        # 可分块的符号类型
        func_symbol = Symbol(
            id=1,
            name="test",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(0, 10, 10))
        )
        self.assertTrue(self.extractor._is_chunkable(func_symbol))
        
        # 不可分块的符号类型（参数）
        param_symbol = Symbol(
            id=2,
            name="x",
            symbol_type=SymbolType.PARAMETER,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(0, 1, 1))
        )
        self.assertFalse(self.extractor._is_chunkable(param_symbol))
    
    def test_generate_chunk_id(self):
        """测试 chunk_id 生成"""
        symbol = Symbol(
            id=1,
            name="myMethod",
            symbol_type=SymbolType.METHOD,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(0, 10, 10)),
            scope_id=1
        )
        
        scope = Scope(
            id=1,
            scope_type=ScopeType.CLASS,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(10, 0, 100))
        )
        
        chunk_id = self.extractor.generate_chunk_id(symbol, {1: scope})
        self.assertIn("test.ets#", chunk_id)
        self.assertIn("myMethod", chunk_id)
    
    def test_extract_source_code(self):
        """测试源代码提取"""
        symbol = Symbol(
            id=1,
            name="test",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(1, 0, 1), Position(3, 1, 30))
        )
        
        source = self.extractor.extract_source_code(symbol)
        self.assertIn("function test()", source)
        self.assertIn("return 42", source)
    
    def test_extract_imports(self):
        """测试导入依赖提取"""
        from arkts_processor.models import TypeInfo
        
        symbol = Symbol(
            id=1,
            name="test",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(0, 10, 10)),
            type_info=TypeInfo(name="CustomType", is_primitive=False),
            extends=["BaseClass"],
            implements=["IInterface"]
        )
        
        imports = self.extractor._extract_imports(symbol)
        
        self.assertIn("CustomType", imports)
        self.assertIn("BaseClass", imports)
        self.assertIn("IInterface", imports)
    
    def test_symbol_to_chunk_type_mapping(self):
        """测试符号类型到 Chunk 类型的映射"""
        # 函数映射
        self.assertEqual(
            ChunkExtractor.SYMBOL_TO_CHUNK_TYPE[SymbolType.FUNCTION],
            ChunkType.FUNCTION
        )
        
        # 类映射
        self.assertEqual(
            ChunkExtractor.SYMBOL_TO_CHUNK_TYPE[SymbolType.CLASS],
            ChunkType.CLASS
        )
        
        # 组件映射
        self.assertEqual(
            ChunkExtractor.SYMBOL_TO_CHUNK_TYPE[SymbolType.COMPONENT],
            ChunkType.COMPONENT
        )
    
    def test_extract_chunks(self):
        """测试批量提取 Chunk"""
        symbols = [
            Symbol(
                id=1,
                name="testFunc",
                symbol_type=SymbolType.FUNCTION,
                file_path="test.ets",
                range=Range(Position(1, 0, 1), Position(3, 1, 30))
            ),
            Symbol(
                id=2,
                name="MyClass",
                symbol_type=SymbolType.CLASS,
                file_path="test.ets",
                range=Range(Position(5, 0, 50), Position(7, 1, 80))
            )
        ]
        
        scopes = [
            Scope(
                id=1,
                scope_type=ScopeType.GLOBAL,
                file_path="test.ets",
                range=Range(Position(0, 0, 0), Position(10, 0, 100))
            )
        ]
        
        chunks = self.extractor.extract_chunks(symbols, scopes)
        
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0].name, "testFunc")
        self.assertEqual(chunks[0].type, ChunkType.FUNCTION)
        self.assertEqual(chunks[1].name, "MyClass")
        self.assertEqual(chunks[1].type, ChunkType.CLASS)
    
    def test_create_chunk(self):
        """测试创建单个 Chunk"""
        symbol = Symbol(
            id=1,
            name="testFunc",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(1, 0, 1), Position(3, 1, 30)),
            documentation="Test function"
        )
        
        scope = Scope(
            id=1,
            scope_type=ScopeType.GLOBAL,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(10, 0, 100))
        )
        
        chunk = self.extractor._create_chunk(symbol, {1: scope})
        
        self.assertIsNotNone(chunk)
        self.assertEqual(chunk.name, "testFunc")
        self.assertEqual(chunk.type, ChunkType.FUNCTION)
        self.assertEqual(chunk.comments, "Test function")
        self.assertEqual(chunk.symbol_id, 1)


if __name__ == "__main__":
    unittest.main()

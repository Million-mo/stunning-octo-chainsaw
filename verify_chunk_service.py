#!/usr/bin/env python3
"""
快速验证 Chunk 服务实现

验证核心功能是否正常工作。
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def test_import():
    """测试导入是否正常"""
    print("测试 1: 导入模块...")
    try:
        from arkts_processor.chunk_models import CodeChunk, ChunkType, ChunkMetadata
        from arkts_processor.chunk_service.extractor import ChunkExtractor
        from arkts_processor.chunk_service.enricher import ContextEnricher
        from arkts_processor.chunk_service.metadata_builder import ChunkMetadataBuilder
        from arkts_processor.chunk_service.repository import ChunkRepository
        from arkts_processor.chunk_service.service import ChunkService
        print("✅ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_data_models():
    """测试数据模型"""
    print("\n测试 2: 数据模型...")
    try:
        from arkts_processor.chunk_models import (
            CodeChunk, ChunkType, ChunkMetadata, 
            PositionRange, Parameter, TypeInfo
        )
        
        # 创建测试数据
        pos_range = PositionRange(0, 10, 0, 100)
        param = Parameter("name", "string", None)
        type_info = TypeInfo("number", is_primitive=True)
        
        metadata = ChunkMetadata(
            range=pos_range,
            decorators=["@Component"],
            parameters=[param],
            return_type=type_info,
            tags=["test"]
        )
        
        chunk = CodeChunk(
            chunk_id="test.ets#TestFunc",
            type=ChunkType.FUNCTION,
            path="test.ets",
            name="TestFunc",
            context="TestClass",
            source="function TestFunc() {}",
            metadata=metadata
        )
        
        # 测试转换为字典
        chunk_dict = chunk.to_dict()
        assert "chunk_id" in chunk_dict
        assert chunk_dict["type"] == "function"
        
        print("✅ 数据模型测试通过")
        return True
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chunk_extractor():
    """测试 Chunk 提取器"""
    print("\n测试 3: Chunk 提取器...")
    try:
        from arkts_processor.chunk_service.extractor import ChunkExtractor
        from arkts_processor.models import Symbol, SymbolType, Range, Position, Scope, ScopeType
        
        # 创建测试数据
        source_code = b"function test() {}"
        
        symbol = Symbol(
            id=1,
            name="test",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(
                start=Position(0, 0, 0),
                end=Position(0, 18, 18)
            )
        )
        
        scope = Scope(
            id=1,
            scope_type=ScopeType.GLOBAL,
            file_path="test.ets",
            range=Range(
                start=Position(0, 0, 0),
                end=Position(0, 18, 18)
            )
        )
        
        extractor = ChunkExtractor("test.ets", source_code)
        chunks = extractor.extract_chunks([symbol], [scope])
        
        assert len(chunks) > 0
        assert chunks[0].name == "test"
        
        print("✅ Chunk 提取器测试通过")
        return True
    except Exception as e:
        print(f"❌ Chunk 提取器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata_builder():
    """测试元数据构建器"""
    print("\n测试 4: 元数据构建器...")
    try:
        from arkts_processor.chunk_service.metadata_builder import ChunkMetadataBuilder
        from arkts_processor.models import Symbol, SymbolType, Range, Position, Visibility
        
        builder = ChunkMetadataBuilder()
        
        symbol = Symbol(
            id=1,
            name="test",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(
                start=Position(0, 0, 0),
                end=Position(10, 0, 100)
            ),
            visibility=Visibility.PUBLIC,
            is_async=True
        )
        
        metadata = builder.build_metadata(symbol, "function test() {}")
        
        assert metadata is not None
        assert "async" in metadata.tags
        assert "public" in metadata.tags
        
        print("✅ 元数据构建器测试通过")
        return True
    except Exception as e:
        print(f"❌ 元数据构建器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_context_enricher():
    """测试上下文增强器"""
    print("\n测试 5: 上下文增强器...")
    try:
        from arkts_processor.chunk_service.enricher import ContextEnricher
        from arkts_processor.chunk_models import CodeChunk, ChunkType
        from arkts_processor.models import Symbol, SymbolType, Range, Position, Scope, ScopeType
        
        enricher = ContextEnricher()
        
        chunk = CodeChunk(
            chunk_id="test.ets#test",
            type=ChunkType.FUNCTION,
            path="test.ets",
            name="test",
            context="",
            source="function test() {}",
            symbol_id=1
        )
        
        symbol = Symbol(
            id=1,
            name="test",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(
                start=Position(0, 0, 0),
                end=Position(0, 18, 18)
            )
        )
        
        enriched = enricher.enrich_chunk(chunk, symbol, {})
        
        assert "# file:" in enriched.source
        assert "# function:" in enriched.source
        
        print("✅ 上下文增强器测试通过")
        return True
    except Exception as e:
        print(f"❌ 上下文增强器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_repository():
    """测试数据库存储"""
    print("\n测试 6: 数据库存储...")
    try:
        from arkts_processor.chunk_service.repository import ChunkRepository
        from arkts_processor.chunk_models import CodeChunk, ChunkType
        from arkts_processor.database.repository import DatabaseManager
        
        # 创建临时数据库
        import tempfile
        db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        db_path = db_file.name
        db_file.close()
        
        try:
            db_manager = DatabaseManager(db_path)
            repository = ChunkRepository(db_manager)
            
            # 创建测试 Chunk
            chunk = CodeChunk(
                chunk_id="test.ets#test",
                type=ChunkType.FUNCTION,
                path="test.ets",
                name="test",
                context="",
                source="function test() {}"
            )
            
            # 保存
            chunk_id = repository.save_chunk(chunk)
            assert chunk_id > 0
            
            # 读取
            loaded = repository.get_chunk_by_id(chunk.chunk_id)
            assert loaded is not None
            assert loaded.name == "test"
            
            # 删除
            deleted = repository.delete_chunk(chunk.chunk_id)
            assert deleted
            
            print("✅ 数据库存储测试通过")
            return True
        finally:
            # 清理
            if os.path.exists(db_path):
                os.remove(db_path)
    except Exception as e:
        print(f"❌ 数据库存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("代码 Chunk 服务验证")
    print("=" * 60)
    
    tests = [
        test_import,
        test_data_models,
        test_chunk_extractor,
        test_metadata_builder,
        test_context_enricher,
        test_repository
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 所有测试通过！Chunk 服务实现正确。")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查实现。")
        return 1


if __name__ == "__main__":
    sys.exit(main())

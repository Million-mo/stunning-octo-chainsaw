"""
数据库仓库单元测试
"""

import pytest
import tempfile
import os
from arkts_processor.database.repository import DatabaseManager, SymbolRepository
from arkts_processor.models import Symbol, SymbolType, Scope, ScopeType, Position, Range


class TestDatabaseRepository:
    """数据库仓库测试"""
    
    @pytest.fixture
    def db_manager(self):
        """创建临时数据库"""
        # 使用临时文件
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        manager = DatabaseManager(path)
        manager.create_tables()
        
        yield manager
        
        # 清理
        os.unlink(path)
    
    @pytest.fixture
    def repository(self, db_manager):
        """创建仓库实例"""
        return SymbolRepository(db_manager)
    
    def test_save_and_get_scope(self, repository):
        """测试保存和获取作用域"""
        scope = Scope(
            id=None,
            scope_type=ScopeType.GLOBAL,
            file_path="test.ts",
            range=Range(
                start=Position(0, 0, 0),
                end=Position(10, 0, 100)
            )
        )
        
        scope_id = repository.save_scope(scope)
        assert scope_id is not None
        
        retrieved = repository.get_scope_by_id(scope_id)
        assert retrieved is not None
        assert retrieved.scope_type == ScopeType.GLOBAL
        assert retrieved.file_path == "test.ts"
    
    def test_save_and_get_symbol(self, repository):
        """测试保存和获取符号"""
        # 先创建作用域
        scope = Scope(
            id=None,
            scope_type=ScopeType.GLOBAL,
            file_path="test.ts",
            range=Range(
                start=Position(0, 0, 0),
                end=Position(10, 0, 100)
            )
        )
        scope_id = repository.save_scope(scope)
        
        # 创建符号
        symbol = Symbol(
            id=None,
            name="MyClass",
            symbol_type=SymbolType.CLASS,
            file_path="test.ts",
            range=Range(
                start=Position(1, 0, 10),
                end=Position(5, 1, 80)
            ),
            scope_id=scope_id
        )
        
        symbol_id = repository.save_symbol(symbol)
        assert symbol_id is not None
        
        retrieved = repository.get_symbol_by_id(symbol_id)
        assert retrieved is not None
        assert retrieved.name == "MyClass"
        assert retrieved.symbol_type == SymbolType.CLASS
    
    def test_batch_save_symbols(self, repository):
        """测试批量保存符号"""
        # 创建作用域
        scope = Scope(
            id=None,
            scope_type=ScopeType.GLOBAL,
            file_path="test.ts",
            range=Range(
                start=Position(0, 0, 0),
                end=Position(10, 0, 100)
            )
        )
        scope_id = repository.save_scope(scope)
        
        # 创建多个符号
        symbols = [
            Symbol(
                id=None,
                name=f"Symbol{i}",
                symbol_type=SymbolType.CLASS,
                file_path="test.ts",
                range=Range(
                    start=Position(i, 0, i*10),
                    end=Position(i+1, 0, (i+1)*10)
                ),
                scope_id=scope_id
            )
            for i in range(5)
        ]
        
        ids = repository.save_symbols_batch(symbols)
        assert len(ids) == 5
        
        # 验证保存
        for symbol_id in ids:
            retrieved = repository.get_symbol_by_id(symbol_id)
            assert retrieved is not None
    
    def test_get_symbols_by_file(self, repository):
        """测试按文件获取符号"""
        scope = Scope(
            id=None,
            scope_type=ScopeType.GLOBAL,
            file_path="test.ts",
            range=Range(
                start=Position(0, 0, 0),
                end=Position(10, 0, 100)
            )
        )
        scope_id = repository.save_scope(scope)
        
        # 创建符号
        symbols = [
            Symbol(
                id=None,
                name=f"Symbol{i}",
                symbol_type=SymbolType.CLASS,
                file_path="test.ts",
                range=Range(
                    start=Position(i, 0, i*10),
                    end=Position(i+1, 0, (i+1)*10)
                ),
                scope_id=scope_id
            )
            for i in range(3)
        ]
        
        repository.save_symbols_batch(symbols)
        
        # 获取文件的所有符号
        file_symbols = repository.get_symbols_by_file("test.ts")
        assert len(file_symbols) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

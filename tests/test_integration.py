"""
符号服务集成测试

测试符号服务的完整工作流程。
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestSymbolServiceIntegration:
    """符号服务集成测试"""
    
    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def sample_arkts_file(self):
        """创建示例ArkTS文件"""
        fd, path = tempfile.mkstemp(suffix=".ets")
        
        sample_code = """
        export class Calculator {
            private result: number;
            
            constructor() {
                this.result = 0;
            }
            
            public add(a: number, b: number): number {
                this.result = a + b;
                return this.result;
            }
            
            public subtract(a: number, b: number): number {
                this.result = a - b;
                return this.result;
            }
            
            public getResult(): number {
                return this.result;
            }
        }
        
        interface MathOperation {
            execute(a: number, b: number): number;
        }
        
        function multiply(a: number, b: number): number {
            return a * b;
        }
        
        const PI: number = 3.14159;
        """
        
        with os.fdopen(fd, 'w') as f:
            f.write(sample_code)
        
        yield path
        os.unlink(path)
    
    def test_end_to_end_workflow(self, temp_db, sample_arkts_file):
        """测试端到端工作流"""
        from arkts_processor import SymbolService, SymbolType
        
        # 1. 初始化服务
        service = SymbolService(db_path=temp_db)
        
        # 注意：这个测试需要配置tree-sitter解析器才能真正运行
        # 这里主要展示测试结构
        
        # 2. 模拟符号提取结果
        # 在真实场景中，这些数据会通过process_file自动生成
        from arkts_processor.models import Symbol, Scope, ScopeType, Position, Range, TypeInfo
        
        mock_symbols = [
            Symbol(
                id=1,
                name="Calculator",
                symbol_type=SymbolType.CLASS,
                file_path=sample_arkts_file,
                range=Range(
                    start=Position(2, 8, 0),
                    end=Position(20, 9, 500)
                )
            ),
            Symbol(
                id=2,
                name="MathOperation",
                symbol_type=SymbolType.INTERFACE,
                file_path=sample_arkts_file,
                range=Range(
                    start=Position(22, 8, 520),
                    end=Position(24, 9, 580)
                )
            ),
            Symbol(
                id=3,
                name="multiply",
                symbol_type=SymbolType.FUNCTION,
                file_path=sample_arkts_file,
                range=Range(
                    start=Position(26, 8, 600),
                    end=Position(28, 9, 650)
                )
            ),
        ]
        
        # 3. 构建索引
        service.index_service.build_index(mock_symbols)
        
        # 4. 测试查询功能
        
        # 按名称查找
        results = service.find_symbol_by_name("Calculator", sample_arkts_file)
        assert len(results) == 1
        assert results[0].symbol_type == SymbolType.CLASS
        
        # 按类型查找
        classes = service.index_service.find_classes(sample_arkts_file)
        assert len(classes) == 1
        assert classes[0].name == "Calculator"
        
        interfaces = service.index_service.find_interfaces(sample_arkts_file)
        assert len(interfaces) == 1
        assert interfaces[0].name == "MathOperation"
        
        functions = service.index_service.find_functions(sample_arkts_file)
        assert len(functions) == 1
        assert functions[0].name == "multiply"
        
        # 统计信息
        stats = service.get_statistics(sample_arkts_file)
        assert stats['class'] == 1
        assert stats['interface'] == 1
        assert stats['function'] == 1
        assert stats['total'] == 3
    
    def test_scope_analysis(self):
        """测试作用域分析"""
        from arkts_processor.symbol_service.scope_analyzer import ScopeAnalyzer
        from arkts_processor.models import Scope, ScopeType, Position, Range
        
        # 创建模拟作用域结构
        source_code = b"class MyClass { method() { } }"
        analyzer = ScopeAnalyzer("test.ts", source_code)
        
        # 测试作用域层次
        # 注意：需要AST才能真正测试
        # 这里只是演示测试结构
    
    def test_type_inference(self):
        """测试类型推导"""
        from arkts_processor.symbol_service.type_inference import TypeInferenceEngine
        from arkts_processor.models import TypeInfo
        
        source_code = b"const x: number = 42;"
        engine = TypeInferenceEngine(source_code)
        
        # 测试类型推导
        # 注意：需要AST节点才能真正测试
    
    def test_reference_resolution(self):
        """测试引用解析"""
        from arkts_processor.symbol_service.reference_resolver import ReferenceResolver
        
        source_code = b"function add(a: number, b: number) { return a + b; }"
        resolver = ReferenceResolver("test.ts", source_code)
        
        # 测试引用解析
        # 注意：需要AST和符号表才能真正测试
    
    def test_database_persistence(self, temp_db):
        """测试数据库持久化"""
        from arkts_processor.database.repository import DatabaseManager, SymbolRepository
        from arkts_processor.models import Symbol, SymbolType, Scope, ScopeType, Position, Range
        
        # 创建数据库管理器
        db_manager = DatabaseManager(temp_db)
        db_manager.create_tables()
        
        repository = SymbolRepository(db_manager)
        
        # 保存作用域
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
        
        # 保存符号
        symbol = Symbol(
            id=None,
            name="TestSymbol",
            symbol_type=SymbolType.CLASS,
            file_path="test.ts",
            range=Range(
                start=Position(1, 0, 10),
                end=Position(5, 1, 80)
            ),
            scope_id=scope_id
        )
        symbol_id = repository.save_symbol(symbol)
        
        # 验证持久化
        retrieved_symbol = repository.get_symbol_by_id(symbol_id)
        assert retrieved_symbol is not None
        assert retrieved_symbol.name == "TestSymbol"
        assert retrieved_symbol.symbol_type == SymbolType.CLASS
        
        # 验证关系
        file_symbols = repository.get_symbols_by_file("test.ts")
        assert len(file_symbols) == 1
        assert file_symbols[0].name == "TestSymbol"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
符号提取器单元测试
"""

import pytest
from arkts_processor.models import Symbol, SymbolType, Position, Range
from arkts_processor.symbol_service.extractor import SymbolExtractor


class TestSymbolExtractor:
    """符号提取器测试"""
    
    def test_extract_class(self):
        """测试提取类符号"""
        source_code = b"""
        export class MyClass {
            name: string;
            
            constructor(name: string) {
                this.name = name;
            }
            
            getName(): string {
                return this.name;
            }
        }
        """
        
        # 注意：实际测试需要tree-sitter解析器
        # 这里仅演示测试结构
        
    def test_extract_interface(self):
        """测试提取接口符号"""
        source_code = b"""
        interface Person {
            name: string;
            age: number;
            greet(): void;
        }
        """
        
    def test_extract_function(self):
        """测试提取函数符号"""
        source_code = b"""
        function add(a: number, b: number): number {
            return a + b;
        }
        """
        
    def test_extract_variable(self):
        """测试提取变量符号"""
        source_code = b"""
        const PI: number = 3.14159;
        let counter: number = 0;
        var message: string = "Hello";
        """
        
    def test_extract_enum(self):
        """测试提取枚举符号"""
        source_code = b"""
        enum Color {
            Red,
            Green,
            Blue
        }
        """

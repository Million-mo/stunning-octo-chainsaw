"""
符号服务示例

演示如何使用符号表服务处理ArkTS代码。
"""

import tree_sitter_arkts as ts_arkts
from tree_sitter import Language, Parser
from arkts_processor import SymbolService, SymbolType


def main():
    """主函数"""
    
    # 1. 初始化符号服务
    print("初始化符号服务...")
    service = SymbolService(db_path="example_symbols.db")
    
    # 2. 配置tree-sitter解析器
    print("配置解析器...")
    ARKTS_LANGUAGE = Language(ts_arkts.language(), "arkts")
    parser = Parser()
    parser.set_language(ARKTS_LANGUAGE)
    service.set_parser(parser)
    
    # 3. 创建示例ArkTS文件
    example_code = """
    export class Person {
        private name: string;
        private age: number;
        
        constructor(name: string, age: number) {
            this.name = name;
            this.age = age;
        }
        
        public getName(): string {
            return this.name;
        }
        
        public getAge(): number {
            return this.age;
        }
        
        public greet(): void {
            console.log(`Hello, my name is ${this.name}`);
        }
    }
    
    interface Greeter {
        greet(): void;
    }
    
    function createPerson(name: string, age: number): Person {
        return new Person(name, age);
    }
    
    const DEFAULT_AGE: number = 18;
    """
    
    # 保存示例文件
    example_file = "example.ets"
    with open(example_file, 'w') as f:
        f.write(example_code)
    
    print(f"创建示例文件: {example_file}")
    
    # 4. 处理文件
    print("\n处理文件...")
    try:
        result = service.process_file(example_file)
        print(f"处理结果: {result}")
        
        # 使用实际提取的符号进行查询
        print("\n符号查询示例...")
        
        # 查询类符号
        print("\n查找类符号:")
        classes = service.index_service.find_classes(example_file)
        for cls in classes:
            print(f"  - {cls.name} at line {cls.range.start.line}")
        
        # 查询函数符号
        print("\n查找函数符号:")
        functions = service.index_service.find_functions(example_file)
        for func in functions:
            print(f"  - {func.name} at line {func.range.start.line}")
            if func.return_type:
                print(f"    返回类型: {func.return_type.to_string()}")
        
        # 统计信息
        print("\n统计信息:")
        stats = service.get_statistics(example_file)
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"处理文件时出错: {e}")
        print("\n回退到模拟数据演示...")
        demonstrate_with_mock_data(service, example_file)


def demonstrate_with_mock_data(service, example_file):
    """使用模拟数据演示功能"""
    print("\n符号查询示例（基于模拟数据）...")
    
    # 创建模拟数据用于演示
    from arkts_processor.models import Symbol, Scope, ScopeType, Position, Range, TypeInfo
    
    # 模拟符号
    mock_symbols = [
        Symbol(
            id=1,
            name="Person",
            symbol_type=SymbolType.CLASS,
            file_path=example_file,
            range=Range(
                start=Position(2, 4, 0),
                end=Position(20, 5, 300)
            )
        ),
        Symbol(
            id=2,
            name="getName",
            symbol_type=SymbolType.METHOD,
            file_path=example_file,
            range=Range(
                start=Position(10, 8, 150),
                end=Position(12, 9, 180)
            ),
            return_type=TypeInfo(name="string", is_primitive=True)
        ),
        Symbol(
            id=3,
            name="createPerson",
            symbol_type=SymbolType.FUNCTION,
            file_path=example_file,
            range=Range(
                start=Position(26, 4, 400),
                end=Position(28, 5, 450)
            ),
            return_type=TypeInfo(name="Person")
        ),
    ]
    
    # 构建索引
    service.index_service.build_index(mock_symbols)
    
    # 查询示例
    print("\n查找类符号:")
    classes = service.index_service.find_classes(example_file)
    for cls in classes:
        print(f"  - {cls.name} at line {cls.range.start.line}")
    
    print("\n查找函数符号:")
    functions = service.index_service.find_functions(example_file)
    for func in functions:
        print(f"  - {func.name} at line {func.range.start.line}")
        if func.return_type:
            print(f"    返回类型: {func.return_type.to_string()}")
    
    print("\n按名称查找:")
    symbols = service.find_symbol_by_name("Person", example_file)
    for symbol in symbols:
        print(f"  - {symbol.symbol_type.value}: {symbol.name}")
    
    print("\n前缀搜索 (get*):")
    symbols = service.index_service.find_symbols_by_prefix("get", example_file)
    for symbol in symbols:
        print(f"  - {symbol.name} ({symbol.symbol_type.value})")
    
    # 6. 统计信息
    print("\n统计信息:")
    stats = service.get_statistics(example_file)
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n示例完成！")


if __name__ == "__main__":
    main()

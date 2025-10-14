"""
完整示例 - 使用 tree-sitter-arkts-open 处理 ArkTS 代码

这个示例展示了如何：
1. 安装和配置 tree-sitter-arkts-open
2. 处理 ArkTS 代码文件
3. 查询符号信息
4. 使用 LSP 功能
"""

import tree_sitter_arkts_open as ts_arkts
from tree_sitter import Language, Parser
from arkts_processor import SymbolService, SymbolType
import tempfile
import os


def create_sample_arkts_file():
    """创建示例 ArkTS 文件"""
    sample_code = """
// 定义一个计算器类
export class Calculator {
    private result: number;
    
    constructor() {
        this.result = 0;
    }
    
    /**
     * 加法运算
     * @param a 第一个数
     * @param b 第二个数
     * @returns 计算结果
     */
    public add(a: number, b: number): number {
        this.result = a + b;
        return this.result;
    }
    
    public subtract(a: number, b: number): number {
        this.result = a - b;
        return this.result;
    }
    
    public multiply(a: number, b: number): number {
        this.result = a * b;
        return this.result;
    }
    
    public divide(a: number, b: number): number {
        if (b === 0) {
            throw new Error("Division by zero");
        }
        this.result = a / b;
        return this.result;
    }
    
    public getResult(): number {
        return this.result;
    }
    
    public reset(): void {
        this.result = 0;
    }
}

// 定义数学运算接口
interface MathOperation {
    execute(a: number, b: number): number;
}

// 实现加法操作
class AddOperation implements MathOperation {
    public execute(a: number, b: number): number {
        return a + b;
    }
}

// 工具函数
function factorial(n: number): number {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

function fibonacci(n: number): number {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

// 常量定义
const PI: number = 3.14159;
const E: number = 2.71828;
const MAX_VALUE: number = 1000000;

// 枚举定义
enum Operation {
    Add,
    Subtract,
    Multiply,
    Divide
}

// 类型别名
type OperationCallback = (a: number, b: number) => number;
"""
    
    # 创建临时文件
    fd, path = tempfile.mkstemp(suffix=".ets", prefix="calculator_")
    with os.fdopen(fd, 'w') as f:
        f.write(sample_code)
    
    return path


def main():
    """主函数"""
    
    print("=" * 80)
    print("ArkTS 符号表服务完整示例")
    print("=" * 80)
    
    # 1. 初始化符号服务
    print("\n1. 初始化符号服务...")
    db_path = tempfile.mktemp(suffix=".db")
    service = SymbolService(db_path=db_path)
    print(f"   数据库路径: {db_path}")
    
    # 2. 配置 tree-sitter 解析器
    print("\n2. 配置 tree-sitter ArkTS 解析器...")
    try:
        ARKTS_LANGUAGE = Language(ts_arkts.language(), "arkts")
        parser = Parser()
        parser.set_language(ARKTS_LANGUAGE)
        service.set_parser(parser)
        print("   ✓ 解析器配置成功")
    except Exception as e:
        print(f"   ✗ 解析器配置失败: {e}")
        print("   提示: 请确保已安装 tree-sitter-arkts-open")
        print("   安装命令: pip install tree-sitter-arkts-open")
        return
    
    # 3. 创建示例文件
    print("\n3. 创建示例 ArkTS 文件...")
    sample_file = create_sample_arkts_file()
    print(f"   文件路径: {sample_file}")
    
    # 4. 处理文件
    print("\n4. 处理文件并提取符号...")
    try:
        result = service.process_file(sample_file)
        print(f"   ✓ 处理成功！")
        print(f"   - 提取符号数: {result['symbols']}")
        print(f"   - 作用域数: {result['scopes']}")
        print(f"   - 引用数: {result['references']}")
        print(f"   - 符号关系数: {result.get('relations', 0)}")
    except Exception as e:
        print(f"   ✗ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 5. 符号查询演示
    print("\n5. 符号查询演示...")
    
    # 5.1 查找所有类
    print("\n   5.1 查找所有类:")
    classes = service.index_service.find_classes(sample_file)
    for cls in classes:
        print(f"       - {cls.name} (line {cls.range.start.line})")
        if cls.implements:
            print(f"         实现接口: {', '.join(cls.implements)}")
    
    # 5.2 查找所有接口
    print("\n   5.2 查找所有接口:")
    interfaces = service.index_service.find_interfaces(sample_file)
    for interface in interfaces:
        print(f"       - {interface.name} (line {interface.range.start.line})")
    
    # 5.3 查找所有函数
    print("\n   5.3 查找所有函数:")
    functions = service.index_service.find_functions(sample_file)
    for func in functions:
        return_type = func.return_type.to_string() if func.return_type else "void"
        print(f"       - {func.name}(): {return_type} (line {func.range.start.line})")
    
    # 5.4 查找所有枚举
    print("\n   5.4 查找所有枚举:")
    enums = service.index_service.find_symbols_by_type(SymbolType.ENUM, sample_file)
    for enum in enums:
        print(f"       - {enum.name} (line {enum.range.start.line})")
    
    # 5.5 查找常量
    print("\n   5.5 查找常量:")
    variables = service.index_service.find_symbols_by_type(SymbolType.VARIABLE, sample_file)
    constants = [v for v in variables if v.is_readonly]
    for const in constants:
        type_str = const.type_info.to_string() if const.type_info else "unknown"
        print(f"       - {const.name}: {type_str} (line {const.range.start.line})")
    
    # 6. 按名称查找
    print("\n6. 按名称查找符号...")
    symbol_name = "Calculator"
    symbols = service.find_symbol_by_name(symbol_name, sample_file)
    if symbols:
        symbol = symbols[0]
        print(f"   找到符号: {symbol.name}")
        print(f"   - 类型: {symbol.symbol_type.value}")
        print(f"   - 位置: line {symbol.range.start.line}, col {symbol.range.start.column}")
        if symbol.documentation:
            print(f"   - 文档: {symbol.documentation}")
    
    # 7. 前缀搜索（代码补全）
    print("\n7. 前缀搜索（模拟代码补全）...")
    prefix = "fib"
    completions = service.index_service.find_symbols_by_prefix(prefix, sample_file)
    print(f"   搜索前缀 '{prefix}' 的结果:")
    for symbol in completions:
        print(f"   - {symbol.name} ({symbol.symbol_type.value})")
    
    # 8. LSP 功能演示
    print("\n8. LSP 功能演示...")
    
    # 假设我们要查找 Calculator 类定义的位置
    # 在实际使用中，这个位置会从编辑器光标位置获取
    if classes:
        calc_class = classes[0]
        line = calc_class.range.start.line
        column = calc_class.range.start.column
        
        # 8.1 悬停信息
        print(f"\n   8.1 悬停信息 (line {line}, col {column}):")
        hover_info = service.get_hover_info(sample_file, line, column)
        if hover_info:
            print(f"       名称: {hover_info['name']}")
            print(f"       类型: {hover_info['type']}")
            print(f"       签名: {hover_info['signature']}")
        
        # 8.2 查找定义
        print(f"\n   8.2 查找定义 (line {line}, col {column}):")
        definition = service.find_definition(sample_file, line, column)
        if definition:
            print(f"       定义: {definition.name}")
            print(f"       位置: {definition.file_path}:{definition.range.start.line}")
        
        # 8.3 查找引用
        if definition and definition.id:
            print(f"\n   8.3 查找 '{definition.name}' 的引用:")
            references = service.find_references(definition.id)
            print(f"       找到 {len(references)} 个引用")
            for i, ref in enumerate(references[:5], 1):  # 只显示前5个
                print(f"       {i}. {ref.file_path}:{ref.position.line}:{ref.position.column}")
    
    # 9. 统计信息
    print("\n9. 统计信息...")
    stats = service.get_statistics(sample_file)
    print("   符号类型分布:")
    for symbol_type, count in stats.items():
        if count > 0 and symbol_type != 'total':
            print(f"   - {symbol_type}: {count}")
    print(f"   总计: {stats['total']} 个符号")
    
    # 10. 文档符号（大纲）
    print("\n10. 文档符号（大纲视图）...")
    doc_symbols = service.get_document_symbols(sample_file)
    print(f"   文档包含 {len(doc_symbols)} 个顶级符号")
    
    # 按类型分组显示
    from collections import defaultdict
    symbols_by_type = defaultdict(list)
    for symbol in doc_symbols:
        symbols_by_type[symbol.symbol_type].append(symbol)
    
    for symbol_type, symbols in symbols_by_type.items():
        print(f"\n   {symbol_type.value}s:")
        for symbol in symbols[:3]:  # 每种类型只显示前3个
            print(f"   - {symbol.name} (line {symbol.range.start.line})")
    
    # 清理
    print("\n" + "=" * 80)
    print("示例执行完成！")
    print("=" * 80)
    
    # 清理临时文件
    try:
        os.unlink(sample_file)
        os.unlink(db_path)
    except:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n中断执行")
    except Exception as e:
        print(f"\n执行出错: {e}")
        import traceback
        traceback.print_exc()

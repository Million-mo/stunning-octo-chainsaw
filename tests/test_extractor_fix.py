#!/usr/bin/env python3
"""
测试修复后的符号提取器
"""

import tree_sitter_arkts as ts_arkts
from tree_sitter import Language, Parser
from arkts_processor.symbol_service.extractor import SymbolExtractor

# 初始化解析器
ARKTS_LANGUAGE = Language(ts_arkts.language())
parser = Parser(ARKTS_LANGUAGE)

# 测试用例
test_code = b"""
export class MyClass extends BaseClass {
    private name: string;
    
    constructor(name: string) {
        this.name = name;
    }
    
    public getName(): string {
        return this.name;
    }
}

interface Person {
    name: string;
    age: number;
}

function add(a: number, b: number): number {
    return a + b;
}

const PI: number = 3.14159;
let counter: number = 0;

type StringOrNumber = string | number;
"""

print("=" * 80)
print("测试修复后的符号提取器")
print("=" * 80)

# 解析代码
tree = parser.parse(test_code)

# 提取符号
extractor = SymbolExtractor("test.ets", test_code)
symbols = extractor.extract(tree)

print(f"\n提取到 {len(symbols)} 个符号:\n")

for symbol in symbols:
    print(f"- {symbol.symbol_type.value:15s} | {symbol.name:20s} | Line {symbol.range.start.line}")
    
    # 显示详细信息
    if symbol.extends:
        print(f"  └─ extends: {', '.join(symbol.extends)}")
    
    if symbol.parameters:
        params = ', '.join([f"{p.name}: {p.type_info.name if p.type_info else '?'}" 
                           for p in symbol.parameters])
        print(f"  └─ params: ({params})")
    
    if symbol.return_type:
        print(f"  └─ returns: {symbol.return_type.name}")
    
    if symbol.type_info:
        print(f"  └─ type: {symbol.type_info.name}")

print("\n" + "=" * 80)
print("测试完成！")
print("=" * 80)

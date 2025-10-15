"""
代码 Chunk 服务使用示例

演示如何使用 ChunkService 生成和查询代码块。
"""

import os
import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

import tree_sitter_arkts as ts_arkts
import tree_sitter
from arkts_processor.symbol_service.service import SymbolService
from arkts_processor.chunk_service.service import ChunkService
from arkts_processor.chunk_models import ChunkType


def setup_parser():
    """设置 tree-sitter 解析器"""
    ARKTS_LANGUAGE = tree_sitter.Language(ts_arkts.language())
    parser = tree_sitter.Parser(ARKTS_LANGUAGE)
    return parser


def example_1_generate_chunks():
    """示例 1：为单个文件生成 Chunk"""
    print("=" * 60)
    print("示例 1：为单个文件生成 Chunk")
    print("=" * 60)
    
    # 初始化服务
    parser = setup_parser()
    symbol_service = SymbolService("example_symbols.db")
    symbol_service.set_parser(parser)
    
    chunk_service = ChunkService(symbol_service, "example_chunks.db")
    
    # 使用测试文件
    test_file = project_root / "example.ets"
    
    if not test_file.exists():
        print(f"测试文件不存在: {test_file}")
        return
    
    # 生成 Chunk
    print(f"\n正在处理文件: {test_file}")
    chunks = chunk_service.generate_chunks(str(test_file))
    
    print(f"\n生成了 {len(chunks)} 个 Chunk:")
    for i, chunk in enumerate(chunks, 1):
        print(f"\n{i}. {chunk.name} ({chunk.type.value})")
        print(f"   - ID: {chunk.chunk_id}")
        print(f"   - Context: {chunk.context}")
        print(f"   - Imports: {', '.join(chunk.imports) if chunk.imports else 'None'}")
        if chunk.metadata:
            print(f"   - Tags: {', '.join(chunk.metadata.tags)}")
            print(f"   - Range: L{chunk.metadata.range.start_line}-L{chunk.metadata.range.end_line}")


def example_2_query_chunks():
    """示例 2：查询 Chunk"""
    print("\n" + "=" * 60)
    print("示例 2：查询 Chunk")
    print("=" * 60)
    
    # 初始化服务
    parser = setup_parser()
    symbol_service = SymbolService("example_symbols.db")
    symbol_service.set_parser(parser)
    
    chunk_service = ChunkService(symbol_service, "example_chunks.db")
    
    # 按类型查询
    print("\n查询所有函数类型的 Chunk:")
    function_chunks = chunk_service.get_chunks_by_type(ChunkType.FUNCTION)
    for chunk in function_chunks[:5]:  # 只显示前5个
        print(f"  - {chunk.name} @ {chunk.path}")
    
    # 按名称搜索
    print("\n搜索名称包含 'get' 的 Chunk:")
    search_results = chunk_service.search_chunks("get", limit=5)
    for chunk in search_results:
        print(f"  - {chunk.name} ({chunk.type.value}) @ {chunk.path}")


def example_3_related_chunks():
    """示例 3：查找相关 Chunk"""
    print("\n" + "=" * 60)
    print("示例 3：查找相关 Chunk")
    print("=" * 60)
    
    # 初始化服务
    parser = setup_parser()
    symbol_service = SymbolService("example_symbols.db")
    symbol_service.set_parser(parser)
    
    chunk_service = ChunkService(symbol_service, "example_chunks.db")
    
    test_file = str(project_root / "example.ets")
    
    # 获取第一个 Chunk
    chunks = chunk_service.get_chunks_by_file(test_file)
    if chunks:
        first_chunk = chunks[0]
        print(f"\n当前 Chunk: {first_chunk.name}")
        print(f"Context: {first_chunk.context}")
        print(f"Imports: {first_chunk.imports}")
        
        # 查找相关 Chunk
        related = chunk_service.get_related_chunks(first_chunk.chunk_id)
        print(f"\n找到 {len(related)} 个相关 Chunk:")
        for chunk in related[:5]:
            print(f"  - {chunk.name} ({chunk.type.value})")


def example_4_enriched_source():
    """示例 4：查看增强后的源代码"""
    print("\n" + "=" * 60)
    print("示例 4：查看增强后的源代码（用于 Embedding）")
    print("=" * 60)
    
    # 初始化服务
    parser = setup_parser()
    symbol_service = SymbolService("example_symbols.db")
    symbol_service.set_parser(parser)
    
    chunk_service = ChunkService(symbol_service, "example_chunks.db")
    
    test_file = str(project_root / "example.ets")
    
    # 生成 chunks 并直接准备可嵌入文本
    chunks = chunk_service.generate_chunks(test_file)
    
    # 将 chunks 转换为可嵌入格式
    embedable_texts = [
        {
            "chunk_id": chunk.chunk_id,
            "text": chunk.get_enriched_source(),
            "metadata": {
                "type": chunk.type.value,
                "name": chunk.name,
                "path": chunk.path,
                "context": chunk.context
            }
        }
        for chunk in chunks
    ]
    
    if embedable_texts:
        print(f"\n获取到 {len(embedable_texts)} 个可嵌入文本")
        
        # 显示第一个
        first = embedable_texts[0]
        print(f"\nChunk ID: {first['chunk_id']}")
        print(f"Type: {first['metadata']['type']}")
        print(f"Name: {first['metadata']['name']}")
        print("\n增强后的文本:")
        print("-" * 60)
        print(first['text'][:500])  # 只显示前500字符
        if len(first['text']) > 500:
            print("...")


def example_5_export_json():
    """示例 5：导出 Chunk 为 JSON"""
    print("\n" + "=" * 60)
    print("示例 5：导出 Chunk 为 JSON")
    print("=" * 60)
    
    # 初始化服务
    parser = setup_parser()
    symbol_service = SymbolService("example_symbols.db")
    symbol_service.set_parser(parser)
    
    chunk_service = ChunkService(symbol_service, "example_chunks.db")
    
    test_file = str(project_root / "example.ets")
    output_file = "chunks_export.json"
    
    # 导出
    chunk_service.export_chunks_to_json(test_file, output_file)
    print(f"\nChunk 已导出到: {output_file}")
    
    # 显示文件大小
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        print(f"文件大小: {size} bytes")


def example_6_statistics():
    """示例 6：获取统计信息"""
    print("\n" + "=" * 60)
    print("示例 6：获取统计信息")
    print("=" * 60)
    
    # 初始化服务
    parser = setup_parser()
    symbol_service = SymbolService("example_symbols.db")
    symbol_service.set_parser(parser)
    
    chunk_service = ChunkService(symbol_service, "example_chunks.db")
    
    # 获取全局统计
    stats = chunk_service.get_statistics()
    print("\n全局统计:")
    print(f"  总 Chunk 数: {stats['total_chunks']}")
    print("\n按类型统计:")
    for chunk_type, count in stats['by_type'].items():
        if count > 0:
            print(f"  - {chunk_type}: {count}")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("代码 Chunk 服务示例")
    print("=" * 60)
    
    try:
        # 运行各个示例
        example_1_generate_chunks()
        example_2_query_chunks()
        example_3_related_chunks()
        example_4_enriched_source()
        example_5_export_json()
        example_6_statistics()
        
        print("\n" + "=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

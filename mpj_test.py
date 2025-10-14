
# import tree_sitter_arkts as ts_arkts
# from tree_sitter import Language, Parser
# from arkts_processor import SymbolService

# # 1. 初始化服务
# service = SymbolService(db_path="my_symbols.db")

# # 2. 配置解析器
# ARKTS_LANGUAGE = Language(ts_arkts.language())
# parser = Parser(ARKTS_LANGUAGE)
# service.set_parser(parser)

# # 3. 处理文件
# result = service.process_file("example.ets")
# print(f"提取了 {result['symbols']} 个符号")


############

# import tree_sitter_arkts as ts_arkts
# from tree_sitter import Language, Parser
# from arkts_processor import SymbolService

# # 1. 初始化服务
# service = SymbolService(db_path="my_symbols.db")

# # 2. 配置解析器
# ARKTS_LANGUAGE = Language(ts_arkts.language())
# parser = Parser(ARKTS_LANGUAGE)
# service.set_parser(parser)

# # 3. 处理文件
# result = service.process_file("/Users/million_mo/projects/stunning-octo-chainsaw/tests/test_arkui_features.ets")
# print(f"提取了 {result['symbols']} 个符号")


import tree_sitter
import tree_sitter_arkts as ts_arkts
from arkts_processor.symbol_service.service import SymbolService
from arkts_processor.chunk_service.service import ChunkService

# 1. 初始化符号服务
symbol_service = SymbolService("symbols.db")
parser = tree_sitter.Parser(tree_sitter.Language(ts_arkts.language()))
symbol_service.set_parser(parser)

# 2. 初始化 Chunk 服务
chunk_service = ChunkService(symbol_service, "chunks.db")

# 3. 为文件生成 Chunk
chunks = chunk_service.generate_chunks("/Users/million_mo/projects/stunning-octo-chainsaw/tests/test_arkui_features.ets")
print(f"生成了 {len(chunks)} 个 Chunk")

# 4. 查看 Chunk 信息
for chunk in chunks[:3]:  # 显示前 3 个
    print(f"\n{chunk.name} ({chunk.type.value})")
    print(f"  - Context: {chunk.context}")
    print(f"  - Imports: {', '.join(chunk.imports) if chunk.imports else 'None'}")

# 5. 获取可嵌入文本（用于 RAG）
embedable_texts = chunk_service.get_embedable_texts("example.ets")
for item in embedable_texts:
    # 可以直接用于 embedding 模型
    text = item['text']  # 包含元数据头 + 原始代码
    chunk_id = item['chunk_id']  # 唯一标识符
    metadata = item['metadata']  # 完整元数据
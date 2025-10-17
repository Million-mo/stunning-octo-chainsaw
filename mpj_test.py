
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

# 1. 初始化服务（使用内存数据库，测试时不生成文件）
parser = tree_sitter.Parser(tree_sitter.Language(ts_arkts.language()))
symbol_service = SymbolService(":memory:")  # 使用内存数据库
symbol_service.set_parser(parser)
chunk_service = ChunkService(symbol_service, ":memory:")  # 使用内存数据库

# 2. 处理项目中的所有 .ets 文件
from pathlib import Path

# project_files = list(Path("/Users/million_mo/projects/hmos_projects/hmosworld/").rglob("*.ets"))
# all_chunks = []
# for file_path in project_files:
#     chunks = chunk_service.generate_chunks(str(file_path))
#     all_chunks.extend(chunks)
#     print(f"处理了 {file_path}: {len(chunks)} 个 Chunk")

# print(f"\n总计 {len(all_chunks)} 个可嵌入文本")

# file_path = "/Users/million_mo/projects/hmos_projects/hmosworld/HMOSWorld/Application/features/login/src/main/ets/pages/LoginPage.ets"
file_path = "example.ets"
chunks = chunk_service.generate_chunks(file_path=str(file_path))
print(f"处理了 {file_path}: {len(chunks)} 个 Chunk")
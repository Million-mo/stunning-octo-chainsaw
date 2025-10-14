
import tree_sitter_arkts as ts_arkts
from tree_sitter import Language, Parser
from arkts_processor import SymbolService

# 1. 初始化服务
service = SymbolService(db_path="my_symbols.db")

# 2. 配置解析器
ARKTS_LANGUAGE = Language(ts_arkts.language())
parser = Parser(ARKTS_LANGUAGE)
service.set_parser(parser)

# 3. 处理文件
result = service.process_file("example.ets")
print(f"提取了 {result['symbols']} 个符号")
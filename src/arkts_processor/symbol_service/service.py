"""
符号表服务

整合符号提取、作用域分析、类型推导和引用解析功能，提供统一的符号服务接口。
"""

from typing import List, Optional, Dict, Tuple, Any
from pathlib import Path
import tree_sitter

from ..models import Symbol, Scope, Reference, SymbolRelation, Position
from ..database.repository import SymbolRepository, DatabaseManager
from .extractor import SymbolExtractor
from .scope_analyzer import ScopeAnalyzer
from .type_inference import TypeInferenceEngine
from .reference_resolver import ReferenceResolver
from .index_service import SymbolIndexService


class SymbolService:
    """符号表服务主类"""
    
    def __init__(self, db_path: str = "arkts_symbols.db"):
        """
        初始化符号服务
        
        Args:
            db_path: 数据库文件路径
        """
        # 初始化数据库
        self.db_manager = DatabaseManager(db_path)
        self.db_manager.create_tables()
        self.repository = SymbolRepository(self.db_manager)
        
        # 初始化索引服务
        self.index_service = SymbolIndexService(self.repository)
        
        # Tree-sitter解析器（需要外部初始化）
        self.parser: Optional[tree_sitter.Parser] = None
        
        # 缓存
        self._file_symbols: Dict[str, List[Symbol]] = {}
        self._file_scopes: Dict[str, List[Scope]] = {}
    
    def set_parser(self, parser: tree_sitter.Parser) -> None:
        """
        设置tree-sitter解析器
        
        Args:
            parser: 配置好的tree-sitter解析器
        """
        self.parser = parser
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        处理单个文件，提取并分析所有符号信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            处理结果字典
        """
        if not self.parser:
            raise RuntimeError("Parser not initialized. Call set_parser() first.")
        
        # 读取文件
        with open(file_path, 'rb') as f:
            source_code = f.read()
        
        # 解析AST
        tree = self.parser.parse(source_code)
        
        # 第一步：提取符号
        extractor = SymbolExtractor(file_path, source_code)
        symbols = extractor.extract(tree)
        
        # 第二步：作用域分析
        scope_analyzer = ScopeAnalyzer(file_path, source_code)
        scopes = scope_analyzer.analyze(tree, symbols)
        
        # 第三步：类型推导
        type_engine = TypeInferenceEngine(source_code)
        type_engine.infer_types(symbols, scopes)
        
        # 第四步：引用解析
        reference_resolver = ReferenceResolver(file_path, source_code)
        references, relations = reference_resolver.resolve(tree, symbols, scopes, scope_analyzer)
        
        # 保存到数据库
        self._save_to_database(symbols, scopes, references)
        
        # 缓存结果
        self._file_symbols[file_path] = symbols
        self._file_scopes[file_path] = scopes
        
        # 更新索引
        self.index_service.build_index(symbols)
        
        return {
            "file_path": file_path,
            "symbols": len(symbols),
            "scopes": len(scopes),
            "references": len(references),
            "relations": len(relations)
        }
    
    def process_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """
        批量处理文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            处理结果列表
        """
        results = []
        for file_path in file_paths:
            try:
                result = self.process_file(file_path)
                results.append(result)
            except Exception as e:
                results.append({
                    "file_path": file_path,
                    "error": str(e)
                })
        return results
    
    def _save_to_database(self, 
                          symbols: List[Symbol], 
                          scopes: List[Scope],
                          references: List[Reference]) -> None:
        """
        保存到数据库
        
        Args:
            symbols: 符号列表
            scopes: 作用域列表
            references: 引用列表
        """
        # 保存作用域
        for scope in scopes:
            self.repository.save_scope(scope)
        
        # 更新符号的作用域ID
        for symbol in symbols:
            # 查找包含该符号的作用域
            for scope in scopes:
                if symbol.name in scope.symbols:
                    symbol.scope_id = scope.id
                    break
        
        # 批量保存符号
        self.repository.save_symbols_batch(symbols)
        
        # 保存引用
        for reference in references:
            self.repository.save_reference(reference)
    
    # ========== 符号查询接口 ==========
    
    def find_symbol_by_name(self, name: str, file_path: Optional[str] = None) -> List[Symbol]:
        """
        按名称查找符号
        
        Args:
            name: 符号名称
            file_path: 文件路径（可选）
            
        Returns:
            符号列表
        """
        return self.index_service.find_symbol_by_name(name, file_path)
    
    def find_symbol_at_position(self, file_path: str, line: int, column: int) -> Optional[Symbol]:
        """
        查找指定位置的符号
        
        Args:
            file_path: 文件路径
            line: 行号（从0开始）
            column: 列号（从0开始）
            
        Returns:
            符号或None
        """
        return self.index_service.find_symbol_at_position(file_path, line, column)
    
    def find_references(self, symbol_id: int) -> List[Reference]:
        """
        查找符号的所有引用
        
        Args:
            symbol_id: 符号ID
            
        Returns:
            引用列表
        """
        return self.repository.get_references_by_symbol(symbol_id)
    
    def find_definition(self, file_path: str, line: int, column: int) -> Optional[Symbol]:
        """
        查找定义（Go to Definition）
        
        Args:
            file_path: 文件路径
            line: 行号
            column: 列号
            
        Returns:
            符号定义
        """
        # 首先找到光标位置的符号
        symbol = self.find_symbol_at_position(file_path, line, column)
        if symbol:
            return symbol
        
        # 如果不是定义位置，可能是引用，需要查找引用对应的定义
        references = self.repository.get_references_by_file(file_path)
        for ref in references:
            if ref.position.line == line and ref.position.column <= column:
                # 找到引用，返回对应的符号定义
                return self.repository.get_symbol_by_id(ref.symbol_id)
        
        return None
    
    def get_document_symbols(self, file_path: str) -> List[Symbol]:
        """
        获取文档符号（用于大纲视图）
        
        Args:
            file_path: 文件路径
            
        Returns:
            符号列表
        """
        return self.repository.get_symbols_by_file(file_path)
    
    def get_workspace_symbols(self, query: str) -> List[Symbol]:
        """
        工作区符号搜索
        
        Args:
            query: 搜索查询
            
        Returns:
            符号列表
        """
        return self.index_service.search_symbols(query, fuzzy=True, limit=50)
    
    def get_completion_items(self, file_path: str, line: int, column: int, prefix: str) -> List[Symbol]:
        """
        获取代码补全项
        
        Args:
            file_path: 文件路径
            line: 行号
            column: 列号
            prefix: 输入前缀
            
        Returns:
            符号列表
        """
        # 查找当前位置的作用域
        if file_path in self._file_scopes:
            scopes = self._file_scopes[file_path]
            position = Position(line=line, column=column, offset=0)
            
            # 找到包含该位置的作用域
            current_scope = None
            for scope in scopes:
                if scope.range.contains(position):
                    current_scope = scope
                    break
            
            if current_scope:
                # 获取作用域内可见的符号
                scope_analyzer = ScopeAnalyzer(file_path, b"")
                scope_analyzer.scopes = scopes
                visible_symbols = scope_analyzer.get_visible_symbols(current_scope)
                
                # 按前缀过滤
                return [s for s in visible_symbols if s.name.startswith(prefix)]
        
        # 如果没有缓存，使用索引服务
        return self.index_service.find_symbols_by_prefix(prefix, file_path)
    
    def get_hover_info(self, file_path: str, line: int, column: int) -> Optional[Dict[str, Any]]:
        """
        获取悬停信息
        
        Args:
            file_path: 文件路径
            line: 行号
            column: 列号
            
        Returns:
            悬停信息字典
        """
        symbol = self.find_symbol_at_position(file_path, line, column)
        if not symbol:
            return None
        
        # 构建悬停信息
        hover_info = {
            "name": symbol.name,
            "type": symbol.symbol_type.value,
            "signature": self._build_signature(symbol),
            "documentation": symbol.documentation,
            "location": {
                "file": symbol.file_path,
                "line": symbol.range.start.line,
                "column": symbol.range.start.column
            }
        }
        
        return hover_info
    
    def _build_signature(self, symbol: Symbol) -> str:
        """构建符号签名"""
        signature_parts = []
        
        # 修饰符
        if symbol.is_static:
            signature_parts.append("static")
        if symbol.is_abstract:
            signature_parts.append("abstract")
        if symbol.is_readonly:
            signature_parts.append("readonly")
        if symbol.is_async:
            signature_parts.append("async")
        
        # 类型
        signature_parts.append(symbol.symbol_type.value)
        
        # 名称
        signature_parts.append(symbol.name)
        
        # 参数（对于函数和方法）
        if symbol.parameters:
            params_str = ", ".join([
                f"{p.name}: {p.type_info.to_string() if p.type_info else 'any'}"
                for p in symbol.parameters
            ])
            signature_parts.append(f"({params_str})")
        
        # 返回类型
        if symbol.return_type:
            signature_parts.append(f": {symbol.return_type.to_string()}")
        elif symbol.type_info:
            signature_parts.append(f": {symbol.type_info.to_string()}")
        
        return " ".join(signature_parts)
    
    # ========== 统计和管理接口 ==========
    
    def get_statistics(self, file_path: Optional[str] = None) -> Dict[str, int]:
        """
        获取统计信息
        
        Args:
            file_path: 文件路径（可选）
            
        Returns:
            统计字典
        """
        return self.index_service.get_statistics(file_path)
    
    def refresh_file(self, file_path: str) -> Dict[str, Any]:
        """
        刷新文件的符号信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            处理结果
        """
        # 删除旧数据
        self.repository.delete_symbols_by_file(file_path)
        
        # 清除缓存
        if file_path in self._file_symbols:
            del self._file_symbols[file_path]
        if file_path in self._file_scopes:
            del self._file_scopes[file_path]
        
        # 重新处理
        return self.process_file(file_path)
    
    def clear_database(self) -> None:
        """清空数据库"""
        self.db_manager.drop_tables()
        self.db_manager.create_tables()
        self._file_symbols.clear()
        self._file_scopes.clear()

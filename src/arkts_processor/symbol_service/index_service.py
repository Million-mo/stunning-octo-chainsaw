"""
符号索引服务

提供高效的符号查询和检索功能。
"""

from typing import List, Optional, Dict, Set, Callable, Any
from enum import Enum

from ..models import Symbol, SymbolType, Scope, Reference, Position
from ..database.repository import SymbolRepository, DatabaseManager


class QueryOperator(Enum):
    """查询操作符"""
    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX = "regex"


class SymbolQuery:
    """符号查询条件"""
    
    def __init__(self):
        self.name: Optional[str] = None
        self.name_operator: QueryOperator = QueryOperator.EQUALS
        self.symbol_types: List[SymbolType] = []
        self.file_path: Optional[str] = None
        self.scope_id: Optional[int] = None
        self.is_public: Optional[bool] = None
        self.is_static: Optional[bool] = None
        self.is_abstract: Optional[bool] = None
        self.has_type: Optional[bool] = None
        self.extends: Optional[str] = None
        self.implements: Optional[str] = None


class SymbolIndexService:
    """符号索引服务"""
    
    def __init__(self, repository: SymbolRepository):
        """
        初始化索引服务
        
        Args:
            repository: 符号仓库
        """
        self.repository = repository
        
        # 内存索引（可选，用于性能优化）
        self._symbol_name_index: Dict[str, List[Symbol]] = {}
        self._symbol_type_index: Dict[SymbolType, List[Symbol]] = {}
        self._file_index: Dict[str, List[Symbol]] = {}
        
        # 索引是否已构建
        self._indexed = False
    
    def build_index(self, symbols: List[Symbol]) -> None:
        """
        构建内存索引
        
        Args:
            symbols: 符号列表
        """
        self._symbol_name_index.clear()
        self._symbol_type_index.clear()
        self._file_index.clear()
        
        for symbol in symbols:
            # 按名称索引
            if symbol.name not in self._symbol_name_index:
                self._symbol_name_index[symbol.name] = []
            self._symbol_name_index[symbol.name].append(symbol)
            
            # 按类型索引
            if symbol.symbol_type not in self._symbol_type_index:
                self._symbol_type_index[symbol.symbol_type] = []
            self._symbol_type_index[symbol.symbol_type].append(symbol)
            
            # 按文件索引
            if symbol.file_path not in self._file_index:
                self._file_index[symbol.file_path] = []
            self._file_index[symbol.file_path].append(symbol)
        
        self._indexed = True
    
    def query(self, query: SymbolQuery) -> List[Symbol]:
        """
        查询符号
        
        Args:
            query: 查询条件
            
        Returns:
            符号列表
        """
        # 优先使用内存索引
        if self._indexed:
            return self._query_from_index(query)
        else:
            return self._query_from_database(query)
    
    def _query_from_index(self, query: SymbolQuery) -> List[Symbol]:
        """从内存索引查询"""
        results: Set[Symbol] = set()
        
        # 按名称查询
        if query.name:
            if query.name_operator == QueryOperator.EQUALS:
                results.update(self._symbol_name_index.get(query.name, []))
            elif query.name_operator == QueryOperator.CONTAINS:
                for name, symbols in self._symbol_name_index.items():
                    if query.name in name:
                        results.update(symbols)
            elif query.name_operator == QueryOperator.STARTS_WITH:
                for name, symbols in self._symbol_name_index.items():
                    if name.startswith(query.name):
                        results.update(symbols)
            elif query.name_operator == QueryOperator.ENDS_WITH:
                for name, symbols in self._symbol_name_index.items():
                    if name.endswith(query.name):
                        results.update(symbols)
        else:
            # 如果没有名称过滤，从所有符号开始
            for symbols in self._symbol_name_index.values():
                results.update(symbols)
        
        # 按类型过滤
        if query.symbol_types:
            results = {s for s in results if s.symbol_type in query.symbol_types}
        
        # 按文件过滤
        if query.file_path:
            results = {s for s in results if s.file_path == query.file_path}
        
        # 按作用域过滤
        if query.scope_id is not None:
            results = {s for s in results if s.scope_id == query.scope_id}
        
        # 按可见性过滤
        if query.is_public is not None:
            from ..models import Visibility
            results = {s for s in results if (s.visibility == Visibility.PUBLIC) == query.is_public}
        
        # 按静态属性过滤
        if query.is_static is not None:
            results = {s for s in results if s.is_static == query.is_static}
        
        # 按抽象属性过滤
        if query.is_abstract is not None:
            results = {s for s in results if s.is_abstract == query.is_abstract}
        
        # 按类型信息过滤
        if query.has_type is not None:
            results = {s for s in results if (s.type_info is not None) == query.has_type}
        
        # 按继承过滤
        if query.extends:
            results = {s for s in results if query.extends in s.extends}
        
        # 按实现过滤
        if query.implements:
            results = {s for s in results if query.implements in s.implements}
        
        return list(results)
    
    def _query_from_database(self, query: SymbolQuery) -> List[Symbol]:
        """从数据库查询"""
        # 使用数据库仓库进行查询
        if query.name and query.name_operator == QueryOperator.EQUALS:
            return self.repository.get_symbols_by_name(query.name, query.file_path)
        elif query.symbol_types and len(query.symbol_types) == 1:
            return self.repository.get_symbols_by_type(query.symbol_types[0], query.file_path)
        elif query.file_path:
            return self.repository.get_symbols_by_file(query.file_path)
        else:
            # 复杂查询需要加载所有符号后过滤
            # 这里简化处理
            return []
    
    def find_symbol_by_name(self, name: str, file_path: Optional[str] = None) -> List[Symbol]:
        """
        按名称查找符号
        
        Args:
            name: 符号名称
            file_path: 文件路径（可选）
            
        Returns:
            符号列表
        """
        query = SymbolQuery()
        query.name = name
        query.name_operator = QueryOperator.EQUALS
        query.file_path = file_path
        return self.query(query)
    
    def find_symbols_by_prefix(self, prefix: str, file_path: Optional[str] = None) -> List[Symbol]:
        """
        按前缀查找符号（用于代码补全）
        
        Args:
            prefix: 名称前缀
            file_path: 文件路径（可选）
            
        Returns:
            符号列表
        """
        query = SymbolQuery()
        query.name = prefix
        query.name_operator = QueryOperator.STARTS_WITH
        query.file_path = file_path
        return self.query(query)
    
    def find_symbols_by_type(self, symbol_type: SymbolType, file_path: Optional[str] = None) -> List[Symbol]:
        """
        按类型查找符号
        
        Args:
            symbol_type: 符号类型
            file_path: 文件路径（可选）
            
        Returns:
            符号列表
        """
        query = SymbolQuery()
        query.symbol_types = [symbol_type]
        query.file_path = file_path
        return self.query(query)
    
    def find_classes(self, file_path: Optional[str] = None) -> List[Symbol]:
        """查找所有类"""
        return self.find_symbols_by_type(SymbolType.CLASS, file_path)
    
    def find_interfaces(self, file_path: Optional[str] = None) -> List[Symbol]:
        """查找所有接口"""
        return self.find_symbols_by_type(SymbolType.INTERFACE, file_path)
    
    def find_functions(self, file_path: Optional[str] = None) -> List[Symbol]:
        """查找所有函数"""
        return self.find_symbols_by_type(SymbolType.FUNCTION, file_path)
    
    def find_public_symbols(self, file_path: Optional[str] = None) -> List[Symbol]:
        """查找所有公开符号"""
        query = SymbolQuery()
        query.is_public = True
        query.file_path = file_path
        return self.query(query)
    
    def find_symbol_at_position(self, file_path: str, line: int, column: int) -> Optional[Symbol]:
        """
        查找指定位置的符号
        
        Args:
            file_path: 文件路径
            line: 行号
            column: 列号
            
        Returns:
            符号或None
        """
        return self.repository.get_symbol_at_position(file_path, line, column)
    
    def find_symbols_in_scope(self, scope: Scope) -> List[Symbol]:
        """
        查找作用域内的所有符号
        
        Args:
            scope: 作用域
            
        Returns:
            符号列表
        """
        return list(scope.symbols.values())
    
    def search_symbols(self, 
                      pattern: str, 
                      fuzzy: bool = False,
                      limit: int = 100) -> List[Symbol]:
        """
        模糊搜索符号
        
        Args:
            pattern: 搜索模式
            fuzzy: 是否使用模糊匹配
            limit: 结果数量限制
            
        Returns:
            符号列表
        """
        results: List[Symbol] = []
        
        if fuzzy:
            # 模糊匹配：检查模式字符是否按顺序出现
            pattern_lower = pattern.lower()
            for name, symbols in self._symbol_name_index.items():
                if self._fuzzy_match(pattern_lower, name.lower()):
                    results.extend(symbols)
                    if len(results) >= limit:
                        break
        else:
            # 包含匹配
            query = SymbolQuery()
            query.name = pattern
            query.name_operator = QueryOperator.CONTAINS
            results = self.query(query)
        
        return results[:limit]
    
    def _fuzzy_match(self, pattern: str, text: str) -> bool:
        """
        模糊匹配
        
        Args:
            pattern: 模式
            text: 文本
            
        Returns:
            是否匹配
        """
        pattern_idx = 0
        text_idx = 0
        
        while pattern_idx < len(pattern) and text_idx < len(text):
            if pattern[pattern_idx] == text[text_idx]:
                pattern_idx += 1
            text_idx += 1
        
        return pattern_idx == len(pattern)
    
    def get_symbol_hierarchy(self, symbol: Symbol) -> Dict[str, Any]:
        """
        获取符号层次结构
        
        Args:
            symbol: 符号
            
        Returns:
            层次结构字典
        """
        hierarchy = {
            "symbol": symbol,
            "extends": [],
            "implements": [],
            "members": []
        }
        
        # 获取继承的类
        for base_name in symbol.extends:
            base_symbols = self.find_symbol_by_name(base_name, symbol.file_path)
            if base_symbols:
                hierarchy["extends"].append(base_symbols[0])
        
        # 获取实现的接口
        for interface_name in symbol.implements:
            interface_symbols = self.find_symbol_by_name(interface_name, symbol.file_path)
            if interface_symbols:
                hierarchy["implements"].append(interface_symbols[0])
        
        # 获取成员
        hierarchy["members"] = symbol.members
        
        return hierarchy
    
    def get_statistics(self, file_path: Optional[str] = None) -> Dict[str, int]:
        """
        获取统计信息
        
        Args:
            file_path: 文件路径（可选）
            
        Returns:
            统计字典
        """
        stats = {}
        
        if file_path:
            symbols = self._file_index.get(file_path, [])
        else:
            symbols = []
            for symbol_list in self._symbol_name_index.values():
                symbols.extend(symbol_list)
        
        # 按类型统计
        for symbol_type in SymbolType:
            count = sum(1 for s in symbols if s.symbol_type == symbol_type)
            stats[symbol_type.value] = count
        
        stats["total"] = len(symbols)
        
        return stats

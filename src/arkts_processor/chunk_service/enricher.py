"""
上下文增强器

为 Chunk 添加层级上下文和元数据头，生成用于 embedding 的增强文本。
"""

from typing import List, Dict, Any, Optional
from ..models import Symbol, Scope, SymbolType
from ..chunk_models import CodeChunk, ChunkType


class ContextEnricher:
    """上下文增强器"""
    
    def __init__(self):
        """初始化上下文增强器"""
        pass
    
    def enrich_chunk(self, chunk: CodeChunk, symbol: Symbol, scope_map: Dict[int, Scope]) -> CodeChunk:
        """
        增强单个 Chunk，添加上下文信息
        
        Args:
            chunk: CodeChunk 对象
            symbol: 对应的符号对象
            scope_map: 作用域映射
            
        Returns:
            增强后的 CodeChunk
        """
        # 构造元数据头
        metadata_headers = self.format_metadata_headers(chunk, symbol)
        
        # 将元数据头添加到源代码前
        enriched_source = f"{metadata_headers}\n\n{chunk.source}"
        
        # 更新 chunk 的 source 字段
        chunk.source = enriched_source
        
        return chunk
    
    def enrich_chunks(self, chunks: List[CodeChunk], symbols: List[Symbol], 
                     scopes: List[Scope]) -> List[CodeChunk]:
        """
        批量增强 Chunk
        
        Args:
            chunks: CodeChunk 列表
            symbols: 符号列表
            scopes: 作用域列表
            
        Returns:
            增强后的 CodeChunk 列表
        """
        # 创建符号映射
        symbol_map = {symbol.id: symbol for symbol in symbols if symbol.id}
        scope_map = {scope.id: scope for scope in scopes}
        
        enriched_chunks = []
        for chunk in chunks:
            if chunk.symbol_id and chunk.symbol_id in symbol_map:
                symbol = symbol_map[chunk.symbol_id]
                enriched_chunk = self.enrich_chunk(chunk, symbol, scope_map)
                enriched_chunks.append(enriched_chunk)
            else:
                enriched_chunks.append(chunk)
        
        return enriched_chunks
    
    def format_metadata_headers(self, chunk: CodeChunk, symbol: Symbol) -> str:
        """
        格式化元数据头
        
        Args:
            chunk: CodeChunk 对象
            symbol: 符号对象
            
        Returns:
            元数据头字符串
        """
        headers = []
        
        # 根据 Chunk 类型选择不同的格式
        if chunk.type == ChunkType.COMPONENT:
            # ArkUI 组件格式
            headers = self._format_component_headers(chunk, symbol)
        else:
            # 通用格式
            headers = self._format_general_headers(chunk, symbol)
        
        return "\n".join(headers)
    
    def _format_general_headers(self, chunk: CodeChunk, symbol: Symbol) -> List[str]:
        """
        格式化通用元数据头
        
        Args:
            chunk: CodeChunk 对象
            symbol: 符号对象
            
        Returns:
            元数据头行列表
        """
        headers = []
        
        # 文件路径
        headers.append(f"# file: {chunk.path}")
        
        # 上下文路径
        if chunk.context:
            if chunk.type == ChunkType.FUNCTION:
                if "." in chunk.context or "/" in chunk.context:
                    headers.append(f"# class: {chunk.context}")
                else:
                    headers.append(f"# module: {chunk.context}")
            elif chunk.type == ChunkType.CLASS:
                if chunk.context:
                    headers.append(f"# module: {chunk.context}")
        
        # 符号类型和名称
        if chunk.type == ChunkType.FUNCTION:
            headers.append(f"# function: {chunk.name}")
        elif chunk.type == ChunkType.CLASS:
            headers.append(f"# class: {chunk.name}")
        elif chunk.type == ChunkType.INTERFACE:
            headers.append(f"# interface: {chunk.name}")
        elif chunk.type == ChunkType.ENUM:
            headers.append(f"# enum: {chunk.name}")
        
        # 导入列表
        if chunk.imports:
            imports_str = ", ".join(chunk.imports)
            headers.append(f"# imports: [{imports_str}]")
        
        # 装饰器
        if chunk.metadata and chunk.metadata.decorators:
            decorators_str = ", ".join(chunk.metadata.decorators)
            headers.append(f"# decorators: [{decorators_str}]")
        
        # 标签
        if chunk.metadata and chunk.metadata.tags:
            tags_str = ", ".join(chunk.metadata.tags)
            headers.append(f"# tags: [{tags_str}]")
        
        # 返回类型
        if chunk.metadata and chunk.metadata.return_type:
            headers.append(f"# type: {chunk.metadata.return_type.name}")
        
        return headers
    
    def _format_component_headers(self, chunk: CodeChunk, symbol: Symbol) -> List[str]:
        """
        格式化 ArkUI 组件元数据头
        
        Args:
            chunk: CodeChunk 对象
            symbol: 符号对象
            
        Returns:
            元数据头行列表
        """
        headers = []
        
        # 文件路径
        headers.append(f"# file: {chunk.path}")
        
        # 组件名称
        headers.append(f"# component: {chunk.name}")
        
        # 组件类型
        if chunk.metadata and chunk.metadata.component_type:
            headers.append(f"# component_type: {chunk.metadata.component_type}")
        
        # 装饰器
        if chunk.metadata and chunk.metadata.decorators:
            decorators_str = ", ".join(chunk.metadata.decorators)
            headers.append(f"# decorators: [{decorators_str}]")
        
        # 状态变量
        if chunk.metadata and chunk.metadata.state_vars:
            state_vars_str = ", ".join([
                f"{var['name']}: {var['type']}" for var in chunk.metadata.state_vars
            ])
            headers.append(f"# state_vars: [{state_vars_str}]")
        
        # 生命周期方法
        if chunk.metadata and chunk.metadata.lifecycle_hooks:
            hooks_str = ", ".join(chunk.metadata.lifecycle_hooks)
            headers.append(f"# lifecycle_hooks: [{hooks_str}]")
        
        # 导入列表
        if chunk.imports:
            imports_str = ", ".join(chunk.imports)
            headers.append(f"# imports: [{imports_str}]")
        
        # 标签
        if chunk.metadata and chunk.metadata.tags:
            tags_str = ", ".join(chunk.metadata.tags)
            headers.append(f"# tags: [{tags_str}]")
        
        return headers
    
    def build_context_path(self, symbol: Symbol, scope_map: Dict[int, Scope]) -> str:
        """
        构造符号的上下文路径
        
        Args:
            symbol: 符号对象
            scope_map: 作用域映射
            
        Returns:
            上下文路径字符串
        """
        if not symbol.scope_id:
            return ""
        
        scope = scope_map.get(symbol.scope_id)
        if not scope or not scope.parent_id:
            return ""
        
        # 查找父作用域
        parent_scope = scope_map.get(scope.parent_id)
        if not parent_scope:
            return ""
        
        # 查找父作用域对应的符号
        parent_symbol = self._find_scope_symbol(parent_scope)
        if parent_symbol:
            # 对于 ArkUI 组件，添加装饰器前缀
            if parent_symbol.symbol_type == SymbolType.COMPONENT:
                return f"@Component/{parent_symbol.name}"
            return parent_symbol.name
        
        return ""
    
    def _find_scope_symbol(self, scope: Scope) -> Optional[Symbol]:
        """
        查找作用域对应的主符号
        
        Args:
            scope: 作用域对象
            
        Returns:
            符号对象或 None
        """
        # 优先查找类、组件、函数等主符号
        priority_types = [
            SymbolType.COMPONENT,
            SymbolType.CLASS,
            SymbolType.FUNCTION,
            SymbolType.METHOD
        ]
        
        for symbol_type in priority_types:
            for symbol in scope.symbols.values():
                if symbol.symbol_type == symbol_type:
                    return symbol
        
        # 如果没有找到主符号，返回第一个符号
        if scope.symbols:
            return next(iter(scope.symbols.values()))
        
        return None

"""
Chunk 提取器

从符号表提取可分块的代码单元。
"""

from typing import List, Optional, Dict, Any
from ..models import Symbol, SymbolType, Scope
from ..chunk_models import (
    CodeChunk, ChunkType, PositionRange, 
    ChunkMetadata, Parameter, TypeInfo
)


class ChunkExtractor:
    """Chunk 提取器"""
    
    # 符号类型到 Chunk 类型的映射
    SYMBOL_TO_CHUNK_TYPE = {
        SymbolType.FUNCTION: ChunkType.FUNCTION,
        SymbolType.METHOD: ChunkType.FUNCTION,
        SymbolType.CLASS: ChunkType.CLASS,
        SymbolType.INTERFACE: ChunkType.INTERFACE,
        SymbolType.COMPONENT: ChunkType.COMPONENT,
        SymbolType.BUILD_METHOD: ChunkType.FUNCTION,
        SymbolType.STYLE_FUNCTION: ChunkType.FUNCTION,
        SymbolType.ENUM: ChunkType.ENUM,
        SymbolType.MODULE: ChunkType.MODULE,
        SymbolType.NAMESPACE: ChunkType.MODULE,
    }
    
    def __init__(self, file_path: str, source_code: bytes):
        """
        初始化提取器
        
        Args:
            file_path: 文件路径
            source_code: 源代码字节数组
        """
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.decode('utf-8').split('\n')
    
    def extract_chunks(self, symbols: List[Symbol], scopes: List[Scope]) -> List[CodeChunk]:
        """
        从符号列表提取所有 Chunk
        
        Args:
            symbols: 符号列表
            scopes: 作用域列表
            
        Returns:
            CodeChunk 列表
        """
        chunks = []
        scope_map = {scope.id: scope for scope in scopes}
        
        for symbol in symbols:
            # 检查是否为可分块类型
            if not self._is_chunkable(symbol):
                continue
            
            # 根据符号类型创建对应的 Chunk
            chunk = self._create_chunk(symbol, scope_map)
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def _is_chunkable(self, symbol: Symbol) -> bool:
        """
        判断符号是否可以创建 Chunk
        
        Args:
            symbol: 符号对象
            
        Returns:
            是否可分块
        """
        # 检查符号类型是否在映射表中
        if symbol.symbol_type not in self.SYMBOL_TO_CHUNK_TYPE:
            return False
        
        # 排除参数等不需要独立 Chunk 的符号
        if symbol.symbol_type in [SymbolType.PARAMETER, SymbolType.VARIABLE]:
            return False
        
        return True
    
    def _create_chunk(self, symbol: Symbol, scope_map: Dict[int, Scope]) -> Optional[CodeChunk]:
        """
        为符号创建 CodeChunk
        
        Args:
            symbol: 符号对象
            scope_map: 作用域ID到作用域对象的映射
            
        Returns:
            CodeChunk 对象或 None
        """
        # 获取 Chunk 类型
        chunk_type = self.SYMBOL_TO_CHUNK_TYPE.get(symbol.symbol_type)
        if not chunk_type:
            return None
        
        # 生成 chunk_id
        chunk_id = self.generate_chunk_id(symbol, scope_map)
        
        # 提取源代码文本
        source_text = self.extract_source_code(symbol)
        
        # 构造上下文路径
        context = self._build_context_path(symbol, scope_map)
        
        # 提取导入依赖
        imports = self._extract_imports(symbol)
        
        # 提取文档注释
        comments = symbol.documentation
        
        # 创建 Chunk
        chunk = CodeChunk(
            chunk_id=chunk_id,
            type=chunk_type,
            path=symbol.file_path,
            name=symbol.name,
            context=context,
            source=source_text,
            imports=imports,
            comments=comments,
            symbol_id=symbol.id
        )
        
        return chunk
    
    def generate_chunk_id(self, symbol: Symbol, scope_map: Dict[int, Scope]) -> str:
        """
        生成 Chunk 的唯一标识符
        
        格式：{文件路径}#{符号路径}
        例如：src/utils/score.ts#ScoreUtils.calculateUserScore
        
        Args:
            symbol: 符号对象
            scope_map: 作用域ID到作用域对象的映射
            
        Returns:
            chunk_id 字符串
        """
        # 构造符号路径
        symbol_path = self._build_symbol_path(symbol, scope_map)
        
        # 返回完整 chunk_id
        return f"{symbol.file_path}#{symbol_path}"
    
    def _build_symbol_path(self, symbol: Symbol, scope_map: Dict[int, Scope]) -> str:
        """
        构造符号的层级路径
        
        Args:
            symbol: 符号对象
            scope_map: 作用域ID到作用域对象的映射
            
        Returns:
            符号路径字符串
        """
        path_parts = [symbol.name]
        
        # 向上遍历作用域，构造路径
        current_scope_id = symbol.scope_id
        while current_scope_id is not None:
            scope = scope_map.get(current_scope_id)
            if not scope:
                break
            
            # 查找该作用域对应的符号
            parent_symbol = self._find_scope_symbol(scope, scope_map)
            if parent_symbol and parent_symbol.name:
                path_parts.insert(0, parent_symbol.name)
            
            current_scope_id = scope.parent_id
        
        return ".".join(path_parts)
    
    def _find_scope_symbol(self, scope: Scope, scope_map: Dict[int, Scope]) -> Optional[Symbol]:
        """
        查找作用域对应的符号（类、函数等）
        
        Args:
            scope: 作用域对象
            scope_map: 作用域映射
            
        Returns:
            符号对象或 None
        """
        # 对于类和函数作用域，查找同名符号
        for symbol in scope.symbols.values():
            if symbol.symbol_type in [SymbolType.CLASS, SymbolType.FUNCTION, 
                                     SymbolType.METHOD, SymbolType.COMPONENT]:
                return symbol
        return None
    
    def _build_context_path(self, symbol: Symbol, scope_map: Dict[int, Scope]) -> str:
        """
        构造上下文路径
        
        Args:
            symbol: 符号对象
            scope_map: 作用域映射
            
        Returns:
            上下文路径字符串
        """
        # 获取父作用域
        if not symbol.scope_id:
            return ""
        
        scope = scope_map.get(symbol.scope_id)
        if not scope or not scope.parent_id:
            return ""
        
        # 查找父作用域的符号
        parent_scope = scope_map.get(scope.parent_id)
        if not parent_scope:
            return ""
        
        parent_symbol = self._find_scope_symbol(parent_scope, scope_map)
        if parent_symbol:
            # 对于 ArkUI 组件，添加装饰器前缀
            if parent_symbol.symbol_type == SymbolType.COMPONENT:
                return f"@Component/{parent_symbol.name}"
            return parent_symbol.name
        
        return ""
    
    def extract_source_code(self, symbol: Symbol) -> str:
        """
        提取符号对应的源代码文本
        
        Args:
            symbol: 符号对象
            
        Returns:
            源代码字符串
        """
        start_line = symbol.range.start.line
        end_line = symbol.range.end.line
        
        # 提取源代码行
        if start_line == end_line:
            # 单行代码
            line = self.source_lines[start_line]
            return line[symbol.range.start.column:symbol.range.end.column]
        else:
            # 多行代码
            lines = []
            for i in range(start_line, end_line + 1):
                if i < len(self.source_lines):
                    if i == start_line:
                        # 第一行，从起始列开始
                        lines.append(self.source_lines[i][symbol.range.start.column:])
                    elif i == end_line:
                        # 最后一行，到结束列结束
                        lines.append(self.source_lines[i][:symbol.range.end.column])
                    else:
                        # 中间行，完整保留
                        lines.append(self.source_lines[i])
            return '\n'.join(lines)
    
    def _extract_imports(self, symbol: Symbol) -> List[str]:
        """
        提取符号的导入依赖
        
        Args:
            symbol: 符号对象
            
        Returns:
            导入符号列表
        """
        imports = []
        
        # 从符号的类型信息中提取
        if symbol.type_info and not symbol.type_info.is_primitive:
            imports.append(symbol.type_info.name)
        
        if symbol.return_type and not symbol.return_type.is_primitive:
            imports.append(symbol.return_type.name)
        
        # 从参数中提取
        for param in symbol.parameters:
            if param.type_info and not param.type_info.is_primitive:
                imports.append(param.type_info.name)
        
        # 从继承和实现中提取
        imports.extend(symbol.extends)
        imports.extend(symbol.implements)
        
        # 去重并返回
        return list(set(imports))

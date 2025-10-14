"""
引用解析器

建立符号间的引用关系，支持查找定义、查找引用等功能。
"""

from typing import List, Optional, Dict, Set
from tree_sitter import Node, Tree

from ..models import (
    Symbol, Reference, ReferenceType, Position, 
    SymbolRelation, Scope
)
from .ast_traverser import ASTVisitor, ASTTraverser, NodeHelper
from .scope_analyzer import ScopeAnalyzer


class ReferenceResolver(ASTVisitor):
    """引用解析器"""
    
    def __init__(self, file_path: str, source_code: bytes):
        """
        初始化引用解析器
        
        Args:
            file_path: 文件路径
            source_code: 源代码字节
        """
        self.file_path = file_path
        self.source_code = source_code
        self.traverser = ASTTraverser(source_code)
        
        # 符号表和作用域
        self.symbols: Dict[str, Symbol] = {}
        self.symbol_by_id: Dict[int, Symbol] = {}
        self.scopes: List[Scope] = []
        self.scope_analyzer: Optional[ScopeAnalyzer] = None
        
        # 引用列表
        self.references: List[Reference] = []
        
        # 符号关系
        self.relations: List[SymbolRelation] = []
        
        # 当前作用域
        self.current_scope: Optional[Scope] = None
    
    def resolve(self, 
                tree: Tree, 
                symbols: List[Symbol], 
                scopes: List[Scope],
                scope_analyzer: ScopeAnalyzer) -> tuple[List[Reference], List[SymbolRelation]]:
        """
        解析引用关系
        
        Args:
            tree: 语法树
            symbols: 符号列表
            scopes: 作用域列表
            scope_analyzer: 作用域分析器
            
        Returns:
            (引用列表, 符号关系列表)
        """
        self.symbols = {s.name: s for s in symbols}
        self.symbol_by_id = {s.id: s for s in symbols if s.id is not None}
        self.scopes = scopes
        self.scope_analyzer = scope_analyzer
        self.references = []
        self.relations = []
        
        # 遍历AST查找引用
        self._resolve_references(tree.root_node)
        
        # 建立符号关系
        self._build_symbol_relations(symbols)
        
        return self.references, self.relations
    
    def _resolve_references(self, node: Node) -> None:
        """
        递归解析引用
        
        Args:
            node: AST节点
        """
        # 处理不同类型的引用
        if node.type == "identifier":
            self._resolve_identifier_reference(node)
        elif node.type == "type_identifier":
            self._resolve_type_reference(node)
        elif node.type == "call_expression":
            self._resolve_call_reference(node)
        elif node.type == "member_expression":
            self._resolve_member_reference(node)
        elif node.type == "import_statement":
            self._resolve_import_reference(node)
        elif node.type == "export_statement":
            self._resolve_export_reference(node)
        
        # 递归处理子节点
        for child in node.children:
            self._resolve_references(child)
    
    def _resolve_identifier_reference(self, node: Node) -> None:
        """解析标识符引用"""
        name = self.traverser.get_node_text(node)
        
        # 获取当前位置的作用域
        position = Position(
            line=node.start_point[0],
            column=node.start_point[1],
            offset=node.start_byte
        )
        
        if self.scope_analyzer:
            current_scope = self.scope_analyzer.get_scope_by_position(position)
            if current_scope:
                # 在作用域链中查找符号
                symbol = self.scope_analyzer.lookup_symbol(name, current_scope)
                if symbol and symbol.id is not None:
                    # 判断引用类型（读取还是写入）
                    ref_type = self._determine_reference_type(node)
                    
                    # 创建引用记录
                    reference = Reference(
                        id=None,
                        symbol_id=symbol.id,
                        file_path=self.file_path,
                        position=position,
                        reference_type=ref_type,
                        context=self._get_reference_context(node)
                    )
                    
                    self.references.append(reference)
    
    def _resolve_type_reference(self, node: Node) -> None:
        """解析类型引用"""
        type_name = self.traverser.get_node_text(node)
        
        # 查找类型符号
        if type_name in self.symbols:
            symbol = self.symbols[type_name]
            if symbol.id is not None:
                position = Position(
                    line=node.start_point[0],
                    column=node.start_point[1],
                    offset=node.start_byte
                )
                
                reference = Reference(
                    id=None,
                    symbol_id=symbol.id,
                    file_path=self.file_path,
                    position=position,
                    reference_type=ReferenceType.TYPE_REFERENCE,
                    context=self._get_reference_context(node)
                )
                
                self.references.append(reference)
    
    def _resolve_call_reference(self, node: Node) -> None:
        """解析函数调用引用"""
        function_node = NodeHelper.get_field_by_name(node, "function")
        if not function_node:
            return
        
        # 获取函数名
        if function_node.type == "identifier":
            func_name = self.traverser.get_node_text(function_node)
            
            # 查找函数符号
            if func_name in self.symbols:
                symbol = self.symbols[func_name]
                if symbol.id is not None:
                    position = Position(
                        line=function_node.start_point[0],
                        column=function_node.start_point[1],
                        offset=function_node.start_byte
                    )
                    
                    reference = Reference(
                        id=None,
                        symbol_id=symbol.id,
                        file_path=self.file_path,
                        position=position,
                        reference_type=ReferenceType.CALL,
                        context=self._get_reference_context(node)
                    )
                    
                    self.references.append(reference)
    
    def _resolve_member_reference(self, node: Node) -> None:
        """解析成员访问引用"""
        property_node = NodeHelper.get_field_by_name(node, "property")
        if not property_node:
            return
        
        property_name = self.traverser.get_node_text(property_node)
        
        # 查找属性符号（简化实现）
        if property_name in self.symbols:
            symbol = self.symbols[property_name]
            if symbol.id is not None:
                position = Position(
                    line=property_node.start_point[0],
                    column=property_node.start_point[1],
                    offset=property_node.start_byte
                )
                
                ref_type = self._determine_reference_type(node)
                
                reference = Reference(
                    id=None,
                    symbol_id=symbol.id,
                    file_path=self.file_path,
                    position=position,
                    reference_type=ref_type,
                    context=self._get_reference_context(node)
                )
                
                self.references.append(reference)
    
    def _resolve_import_reference(self, node: Node) -> None:
        """解析导入引用"""
        # 提取导入的符号
        for child in node.children:
            if child.type == "import_clause":
                self._process_import_clause(child)
    
    def _process_import_clause(self, node: Node) -> None:
        """处理导入子句"""
        for child in node.children:
            if child.type == "identifier":
                name = self.traverser.get_node_text(child)
                if name in self.symbols:
                    symbol = self.symbols[name]
                    if symbol.id is not None:
                        position = Position(
                            line=child.start_point[0],
                            column=child.start_point[1],
                            offset=child.start_byte
                        )
                        
                        reference = Reference(
                            id=None,
                            symbol_id=symbol.id,
                            file_path=self.file_path,
                            position=position,
                            reference_type=ReferenceType.IMPORT,
                            context=self._get_reference_context(node)
                        )
                        
                        self.references.append(reference)
    
    def _resolve_export_reference(self, node: Node) -> None:
        """解析导出引用"""
        # 提取导出的符号
        declaration = NodeHelper.get_field_by_name(node, "declaration")
        if declaration:
            name_node = NodeHelper.get_field_by_name(declaration, "name")
            if name_node:
                name = self.traverser.get_node_text(name_node)
                if name in self.symbols:
                    symbol = self.symbols[name]
                    if symbol.id is not None:
                        position = Position(
                            line=name_node.start_point[0],
                            column=name_node.start_point[1],
                            offset=name_node.start_byte
                        )
                        
                        reference = Reference(
                            id=None,
                            symbol_id=symbol.id,
                            file_path=self.file_path,
                            position=position,
                            reference_type=ReferenceType.EXPORT,
                            context=self._get_reference_context(node)
                        )
                        
                        self.references.append(reference)
    
    def _determine_reference_type(self, node: Node) -> ReferenceType:
        """
        确定引用类型（读取或写入）
        
        Args:
            node: AST节点
            
        Returns:
            引用类型
        """
        # 检查父节点
        parent = node.parent
        if not parent:
            return ReferenceType.READ
        
        # 赋值表达式左侧
        if parent.type == "assignment_expression":
            left = NodeHelper.get_field_by_name(parent, "left")
            if left == node:
                return ReferenceType.WRITE
        
        # 变量声明
        if parent.type == "variable_declarator":
            return ReferenceType.DEFINITION
        
        # 函数调用
        if parent.type == "call_expression":
            function = NodeHelper.get_field_by_name(parent, "function")
            if function == node:
                return ReferenceType.CALL
        
        # 默认为读取
        return ReferenceType.READ
    
    def _get_reference_context(self, node: Node) -> str:
        """
        获取引用上下文（所在行的代码）
        
        Args:
            node: AST节点
            
        Returns:
            上下文字符串
        """
        line_start = node.start_point[0]
        line_end = node.end_point[0]
        
        # 获取所在行的代码
        lines = self.source_code.decode('utf-8').split('\n')
        if line_start < len(lines):
            if line_start == line_end:
                return lines[line_start].strip()
            else:
                return '\n'.join(lines[line_start:line_end+1]).strip()
        
        return ""
    
    def _build_symbol_relations(self, symbols: List[Symbol]) -> None:
        """
        建立符号关系
        
        Args:
            symbols: 符号列表
        """
        for symbol in symbols:
            if symbol.id is None:
                continue
            
            # 继承关系
            for base_class in symbol.extends:
                if base_class in self.symbols:
                    base_symbol = self.symbols[base_class]
                    if base_symbol.id is not None:
                        relation = SymbolRelation(
                            from_symbol_id=symbol.id,
                            to_symbol_id=base_symbol.id,
                            relation_type="extends"
                        )
                        self.relations.append(relation)
            
            # 实现关系
            for interface in symbol.implements:
                if interface in self.symbols:
                    interface_symbol = self.symbols[interface]
                    if interface_symbol.id is not None:
                        relation = SymbolRelation(
                            from_symbol_id=symbol.id,
                            to_symbol_id=interface_symbol.id,
                            relation_type="implements"
                        )
                        self.relations.append(relation)
    
    def find_definition(self, file_path: str, line: int, column: int) -> Optional[Symbol]:
        """
        查找定义
        
        Args:
            file_path: 文件路径
            line: 行号
            column: 列号
            
        Returns:
            符号定义或None
        """
        # 查找该位置的引用
        position = Position(line=line, column=column, offset=0)
        
        for ref in self.references:
            if (ref.file_path == file_path and 
                ref.position.line == line and 
                ref.position.column <= column):
                # 返回引用的符号
                return self.symbol_by_id.get(ref.symbol_id)
        
        return None
    
    def find_references(self, symbol: Symbol) -> List[Reference]:
        """
        查找符号的所有引用
        
        Args:
            symbol: 符号
            
        Returns:
            引用列表
        """
        if symbol.id is None:
            return []
        
        return [ref for ref in self.references if ref.symbol_id == symbol.id]
    
    def find_callers(self, symbol: Symbol) -> List[Reference]:
        """
        查找调用者
        
        Args:
            symbol: 符号（函数或方法）
            
        Returns:
            调用引用列表
        """
        if symbol.id is None:
            return []
        
        return [
            ref for ref in self.references 
            if ref.symbol_id == symbol.id and ref.reference_type == ReferenceType.CALL
        ]

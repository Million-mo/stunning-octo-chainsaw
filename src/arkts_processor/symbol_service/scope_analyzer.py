"""
作用域分析器

构建嵌套作用域层次结构，管理符号的可见性和生命周期。
"""

from typing import List, Optional, Dict, Set, Any
from tree_sitter import Node, Tree

from ..models import Scope, ScopeType, Symbol, Position, Range
from .ast_traverser import ASTVisitor, ASTTraverser, NodeHelper


class ScopeAnalyzer(ASTVisitor):
    """作用域分析器"""
    
    # 节点类型到作用域类型的映射
    SCOPE_TYPE_MAPPING = {
        "program": ScopeType.GLOBAL,
        "module": ScopeType.MODULE,
        "class_declaration": ScopeType.CLASS,
        "interface_declaration": ScopeType.CLASS,
        "method_definition": ScopeType.FUNCTION,
        "function_declaration": ScopeType.FUNCTION,
        "arrow_function": ScopeType.FUNCTION,
        "function_expression": ScopeType.FUNCTION,
        "block": ScopeType.BLOCK,
        "namespace_declaration": ScopeType.NAMESPACE,
    }
    
    def __init__(self, file_path: str, source_code: bytes):
        """
        初始化作用域分析器
        
        Args:
            file_path: 文件路径
            source_code: 源代码字节
        """
        self.file_path = file_path
        self.source_code = source_code
        self.traverser = ASTTraverser(source_code)
        
        # 作用域相关
        self.scopes: List[Scope] = []
        self.scope_stack: List[Scope] = []  # 作用域栈
        self.current_scope: Optional[Scope] = None
        
        # 符号到作用域的映射
        self.symbol_scope_map: Dict[Symbol, Scope] = {}
        
    def analyze(self, tree: Tree, symbols: List[Symbol]) -> List[Scope]:
        """
        分析作用域
        
        Args:
            tree: 语法树
            symbols: 符号列表
            
        Returns:
            作用域列表
        """
        self.scopes = []
        self.scope_stack = []
        self.current_scope = None
        
        # 创建全局作用域
        global_scope = self._create_scope(tree.root_node, ScopeType.GLOBAL)
        self._enter_scope(global_scope)
        
        # 遍历AST构建作用域树
        self._build_scope_tree(tree.root_node)
        
        # 将符号分配到作用域
        self._assign_symbols_to_scopes(symbols)
        
        return self.scopes
    
    def _build_scope_tree(self, node: Node) -> None:
        """
        构建作用域树
        
        Args:
            node: AST节点
        """
        # 检查是否需要创建新作用域
        scope_type = self.SCOPE_TYPE_MAPPING.get(node.type)
        
        if scope_type:
            # 创建新作用域
            new_scope = self._create_scope(node, scope_type)
            self._enter_scope(new_scope)
            
            # 递归处理子节点
            for child in node.children:
                self._build_scope_tree(child)
            
            # 退出作用域
            self._exit_scope()
        else:
            # 不创建新作用域，继续遍历子节点
            for child in node.children:
                self._build_scope_tree(child)
    
    def _create_scope(self, node: Node, scope_type: ScopeType) -> Scope:
        """
        创建作用域
        
        Args:
            node: AST节点
            scope_type: 作用域类型
            
        Returns:
            作用域对象
        """
        parent_id = self.current_scope.id if self.current_scope else None
        
        scope = Scope(
            id=len(self.scopes),  # 临时ID，后续会在数据库中分配真实ID
            scope_type=scope_type,
            file_path=self.file_path,
            range=Range(
                start=Position(
                    line=node.start_point[0],
                    column=node.start_point[1],
                    offset=node.start_byte
                ),
                end=Position(
                    line=node.end_point[0],
                    column=node.end_point[1],
                    offset=node.end_byte
                )
            ),
            parent_id=parent_id
        )
        
        # 添加到作用域列表
        self.scopes.append(scope)
        
        # 如果有父作用域，添加到父作用域的子列表
        if self.current_scope:
            self.current_scope.children.append(scope)
        
        return scope
    
    def _enter_scope(self, scope: Scope) -> None:
        """
        进入作用域
        
        Args:
            scope: 作用域对象
        """
        self.scope_stack.append(scope)
        self.current_scope = scope
    
    def _exit_scope(self) -> None:
        """退出当前作用域"""
        if self.scope_stack:
            self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1] if self.scope_stack else None
    
    def _assign_symbols_to_scopes(self, symbols: List[Symbol]) -> None:
        """
        将符号分配到合适的作用域
        
        Args:
            symbols: 符号列表
        """
        for symbol in symbols:
            # 查找包含该符号的最小作用域
            scope = self._find_containing_scope(symbol.range.start)
            if scope:
                scope.add_symbol(symbol)
                self.symbol_scope_map[symbol] = scope
    
    def _find_containing_scope(self, position: Position) -> Optional[Scope]:
        """
        查找包含指定位置的最小作用域
        
        Args:
            position: 位置
            
        Returns:
            作用域对象或None
        """
        # 从所有作用域中查找
        containing_scopes = [
            scope for scope in self.scopes
            if scope.range.contains(position)
        ]
        
        # 返回最小的作用域（即最深层的作用域）
        if containing_scopes:
            return min(containing_scopes, key=lambda s: self._scope_size(s))
        
        return None
    
    def _scope_size(self, scope: Scope) -> int:
        """
        计算作用域大小（用于比较）
        
        Args:
            scope: 作用域
            
        Returns:
            作用域大小
        """
        start = scope.range.start
        end = scope.range.end
        return (end.line - start.line) * 1000 + (end.column - start.column)
    
    def get_scope_chain(self, scope: Scope) -> List[Scope]:
        """
        获取作用域链
        
        Args:
            scope: 起始作用域
            
        Returns:
            从当前作用域到全局作用域的作用域链
        """
        chain = [scope]
        current = scope
        
        while current.parent_id is not None:
            # 查找父作用域
            parent = next((s for s in self.scopes if s.id == current.parent_id), None)
            if parent:
                chain.append(parent)
                current = parent
            else:
                break
        
        return chain
    
    def lookup_symbol(self, name: str, scope: Scope) -> Optional[Symbol]:
        """
        在作用域链中查找符号
        
        Args:
            name: 符号名称
            scope: 起始作用域
            
        Returns:
            找到的符号或None
        """
        # 获取作用域链
        scope_chain = self.get_scope_chain(scope)
        
        # 在作用域链中查找
        for s in scope_chain:
            if name in s.symbols:
                return s.symbols[name]
        
        return None
    
    def get_visible_symbols(self, scope: Scope) -> List[Symbol]:
        """
        获取在指定作用域中可见的所有符号
        
        Args:
            scope: 作用域
            
        Returns:
            可见符号列表
        """
        visible_symbols = []
        seen_names: Set[str] = set()
        
        # 获取作用域链
        scope_chain = self.get_scope_chain(scope)
        
        # 从内到外收集符号（内层符号会遮蔽外层同名符号）
        for s in scope_chain:
            for symbol in s.symbols.values():
                if symbol.name not in seen_names:
                    visible_symbols.append(symbol)
                    seen_names.add(symbol.name)
        
        return visible_symbols
    
    def get_scope_by_position(self, position: Position) -> Optional[Scope]:
        """
        根据位置获取作用域
        
        Args:
            position: 位置
            
        Returns:
            作用域或None
        """
        return self._find_containing_scope(position)
    
    def get_scope_hierarchy(self, scope: Scope) -> Dict[str, Any]:
        """
        获取作用域层次结构的字典表示
        
        Args:
            scope: 根作用域
            
        Returns:
            层次结构字典
        """
        return {
            "id": scope.id,
            "type": scope.scope_type.value,
            "range": {
                "start": {"line": scope.range.start.line, "column": scope.range.start.column},
                "end": {"line": scope.range.end.line, "column": scope.range.end.column}
            },
            "symbols": [s.name for s in scope.symbols.values()],
            "children": [self.get_scope_hierarchy(child) for child in scope.children]
        }
    
    def print_scope_tree(self, scope: Optional[Scope] = None, indent: int = 0) -> None:
        """
        打印作用域树（用于调试）
        
        Args:
            scope: 根作用域（None表示从全局作用域开始）
            indent: 缩进级别
        """
        if scope is None:
            # 查找全局作用域
            global_scopes = [s for s in self.scopes if s.scope_type == ScopeType.GLOBAL]
            if global_scopes:
                scope = global_scopes[0]
            else:
                return
        
        prefix = "  " * indent
        symbol_names = ", ".join([s.name for s in scope.symbols.values()])
        print(f"{prefix}{scope.scope_type.value} [{scope.id}] - Symbols: {symbol_names or 'none'}")
        
        for child in scope.children:
            self.print_scope_tree(child, indent + 1)

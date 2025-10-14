"""
AST遍历器

提供tree-sitter AST遍历的基础框架。
"""

from typing import Callable, Any, Optional, List
from tree_sitter import Node, Tree


class ASTVisitor:
    """AST访问者基类"""
    
    def visit(self, node: Node) -> Any:
        """
        访问节点
        
        Args:
            node: AST节点
            
        Returns:
            访问结果
        """
        method_name = f"visit_{node.type}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node: Node) -> Any:
        """
        通用访问方法
        
        当没有为特定节点类型定义 visit_* 方法时，
        将调用此方法作为默认处理。
        
        默认行为是遍历所有子节点，这确保了即使没有
        专门的处理方法，也不会遗漏子节点的遍历。
        
        Args:
            node: AST节点
        """
        # 遍历所有子节点
        for child in node.children:
            self.visit(child)
    
    def visit_children(self, node: Node) -> List[Any]:
        """
        访问所有子节点
        
        Args:
            node: 父节点
            
        Returns:
            子节点访问结果列表
        """
        results = []
        for child in node.children:
            result = self.visit(child)
            if result is not None:
                results.append(result)
        return results


class ASTTraverser:
    """AST遍历器"""
    
    def __init__(self, source_code: bytes):
        """
        初始化遍历器
        
        Args:
            source_code: 源代码字节
        """
        self.source_code = source_code
        
    def traverse(self, 
                 tree: Tree, 
                 visitor: Optional[ASTVisitor] = None,
                 pre_order: bool = True) -> None:
        """
        遍历AST
        
        Args:
            tree: 语法树
            visitor: 访问者对象
            pre_order: 是否前序遍历
        """
        if visitor:
            self._traverse_with_visitor(tree.root_node, visitor, pre_order)
        else:
            self._simple_traverse(tree.root_node)
    
    def _traverse_with_visitor(self, 
                                node: Node, 
                                visitor: ASTVisitor,
                                pre_order: bool) -> None:
        """
        使用访问者模式遍历
        
        Args:
            node: 当前节点
            visitor: 访问者对象
            pre_order: 是否前序遍历
        """
        if pre_order:
            visitor.visit(node)
            
        for child in node.children:
            self._traverse_with_visitor(child, visitor, pre_order)
            
        if not pre_order:
            visitor.visit(node)
    
    def _simple_traverse(self, node: Node, depth: int = 0) -> None:
        """
        简单遍历（用于调试）
        
        Args:
            node: 当前节点
            depth: 深度
        """
        indent = "  " * depth
        text = self.get_node_text(node)
        print(f"{indent}{node.type}: {text[:50] if text else ''}")
        
        for child in node.children:
            self._simple_traverse(child, depth + 1)
    
    def get_node_text(self, node: Node) -> str:
        """
        获取节点文本
        
        Args:
            node: AST节点
            
        Returns:
            节点对应的源代码文本
        """
        return self.source_code[node.start_byte:node.end_byte].decode('utf-8')
    
    def find_nodes_by_type(self, 
                           tree: Tree, 
                           node_type: str) -> List[Node]:
        """
        查找指定类型的所有节点
        
        Args:
            tree: 语法树
            node_type: 节点类型
            
        Returns:
            匹配的节点列表
        """
        results = []
        self._find_nodes_recursive(tree.root_node, node_type, results)
        return results
    
    def _find_nodes_recursive(self, 
                               node: Node, 
                               node_type: str, 
                               results: List[Node]) -> None:
        """
        递归查找节点
        
        Args:
            node: 当前节点
            node_type: 要查找的节点类型
            results: 结果列表
        """
        if node.type == node_type:
            results.append(node)
            
        for child in node.children:
            self._find_nodes_recursive(child, node_type, results)
    
    def find_node_at_position(self, 
                               tree: Tree, 
                               line: int, 
                               column: int) -> Optional[Node]:
        """
        查找指定位置的节点
        
        Args:
            tree: 语法树
            line: 行号（从0开始）
            column: 列号（从0开始）
            
        Returns:
            匹配的节点或None
        """
        return self._find_deepest_node(tree.root_node, line, column)
    
    def _find_deepest_node(self, 
                            node: Node, 
                            line: int, 
                            column: int) -> Optional[Node]:
        """
        查找最深层的包含该位置的节点
        
        Args:
            node: 当前节点
            line: 行号
            column: 列号
            
        Returns:
            最深层节点
        """
        # 检查当前节点是否包含该位置
        if not (node.start_point[0] <= line <= node.end_point[0]):
            return None
            
        if node.start_point[0] == line and node.start_point[1] > column:
            return None
            
        if node.end_point[0] == line and node.end_point[1] < column:
            return None
        
        # 递归查找子节点
        for child in node.children:
            result = self._find_deepest_node(child, line, column)
            if result:
                return result
        
        # 如果没有子节点匹配，返回当前节点
        return node
    
    def get_parent_of_type(self, 
                           node: Node, 
                           parent_type: str) -> Optional[Node]:
        """
        查找指定类型的父节点
        
        Args:
            node: 当前节点
            parent_type: 父节点类型
            
        Returns:
            匹配的父节点或None
        """
        current = node.parent
        while current:
            if current.type == parent_type:
                return current
            current = current.parent
        return None
    
    def get_siblings(self, node: Node) -> List[Node]:
        """
        获取兄弟节点
        
        Args:
            node: 当前节点
            
        Returns:
            兄弟节点列表（不包括自己）
        """
        if not node.parent:
            return []
        
        return [child for child in node.parent.children if child != node]
    
    def get_next_sibling(self, node: Node) -> Optional[Node]:
        """
        获取下一个兄弟节点
        
        Args:
            node: 当前节点
            
        Returns:
            下一个兄弟节点或None
        """
        return node.next_sibling
    
    def get_previous_sibling(self, node: Node) -> Optional[Node]:
        """
        获取前一个兄弟节点
        
        Args:
            node: 当前节点
            
        Returns:
            前一个兄弟节点或None
        """
        return node.prev_sibling


class NodeHelper:
    """节点辅助工具"""
    
    @staticmethod
    def is_named_node(node: Node) -> bool:
        """检查是否为命名节点"""
        return node.is_named
    
    @staticmethod
    def has_error(node: Node) -> bool:
        """检查节点是否包含错误"""
        return node.has_error
    
    @staticmethod
    def get_field_by_name(node: Node, field_name: str) -> Optional[Node]:
        """
        通过字段名获取子节点
        
        Args:
            node: 父节点
            field_name: 字段名
            
        Returns:
            子节点或None
        """
        return node.child_by_field_name(field_name)
    
    @staticmethod
    def get_children_by_field(node: Node, field_name: str) -> List[Node]:
        """
        获取指定字段的所有子节点
        
        Args:
            node: 父节点
            field_name: 字段名
            
        Returns:
            子节点列表
        """
        results = []
        for child in node.children:
            if child.type == field_name:
                results.append(child)
        return results
    
    @staticmethod
    def get_named_children(node: Node) -> List[Node]:
        """
        获取所有命名子节点
        
        Args:
            node: 父节点
            
        Returns:
            命名子节点列表
        """
        return [child for child in node.children if child.is_named]

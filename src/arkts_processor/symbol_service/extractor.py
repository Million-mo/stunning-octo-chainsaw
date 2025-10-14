"""
符号提取器

从ArkTS AST中提取类、方法、变量、接口和模块等符号信息。
"""

from typing import List, Optional, Dict, Any
from tree_sitter import Node, Tree

from ..models import (
    Symbol, SymbolType, Position, Range, TypeInfo, Visibility
)
from .ast_traverser import ASTVisitor, ASTTraverser, NodeHelper


class SymbolExtractor(ASTVisitor):
    """符号提取器"""
    
    # ArkTS节点类型映射到符号类型
    NODE_TYPE_MAPPING = {
        "class_declaration": SymbolType.CLASS,
        "interface_declaration": SymbolType.INTERFACE,
        "method_definition": SymbolType.METHOD,
        "function_declaration": SymbolType.FUNCTION,
        "variable_declaration": SymbolType.VARIABLE,
        "lexical_declaration": SymbolType.VARIABLE,
        "property_identifier": SymbolType.PROPERTY,
        "enum_declaration": SymbolType.ENUM,
        "enum_assignment": SymbolType.ENUM_MEMBER,
        "module": SymbolType.MODULE,
        "namespace_declaration": SymbolType.NAMESPACE,
        "type_alias_declaration": SymbolType.TYPE_ALIAS,
    }
    
    def __init__(self, file_path: str, source_code: bytes):
        """
        初始化符号提取器
        
        Args:
            file_path: 文件路径
            source_code: 源代码字节
        """
        self.file_path = file_path
        self.source_code = source_code
        self.traverser = ASTTraverser(source_code)
        self.symbols: List[Symbol] = []
        self.current_scope_id: Optional[int] = None
        
    def extract(self, tree: Tree) -> List[Symbol]:
        """
        提取所有符号
        
        Args:
            tree: 语法树
            
        Returns:
            符号列表
        """
        self.symbols = []
        self.visit(tree.root_node)
        return self.symbols
    
    # ========== 根节点和通用节点处理 ==========
    
    def visit_source_file(self, node: Node) -> None:
        """
        访问源文件根节点
        
        source_file 是 ArkTS 文件的根节点，包含整个文件的内容。
        我们需要遍历其所有子节点来提取符号。
        
        Args:
            node: source_file 节点
        """
        # 遍历所有子节点
        for child in node.children:
            self.visit(child)
    
    def visit_program(self, node: Node) -> None:
        """
        访问程序根节点
        
        某些解析器可能使用 'program' 作为根节点类型。
        
        Args:
            node: program 节点
        """
        # 遍历所有子节点
        for child in node.children:
            self.visit(child)
    
    # ========== 类声明 ==========
    
    def visit_class_declaration(self, node: Node) -> None:
        """访问类声明"""
        name_node = NodeHelper.get_field_by_name(node, "name")
        if not name_node:
            return
            
        name = self.traverser.get_node_text(name_node)
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.CLASS,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 提取修饰符
        self._extract_modifiers(node, symbol)
        
        # 提取继承信息
        heritage_clause = NodeHelper.get_field_by_name(node, "heritage")
        if heritage_clause:
            self._extract_heritage(heritage_clause, symbol)
        
        # 提取装饰器
        self._extract_decorators(node, symbol)
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
        
        # 访问类成员
        body = NodeHelper.get_field_by_name(node, "body")
        if body:
            # 保存当前作用域
            parent_scope = self.current_scope_id
            # 设置新的作用域（类作用域）
            # 注意：实际的scope_id需要在作用域分析阶段确定
            
            for child in body.children:
                self.visit(child)
            
            # 恢复作用域
            self.current_scope_id = parent_scope
    
    # ========== 接口声明 ==========
    
    def visit_interface_declaration(self, node: Node) -> None:
        """访问接口声明"""
        name_node = NodeHelper.get_field_by_name(node, "name")
        if not name_node:
            return
            
        name = self.traverser.get_node_text(name_node)
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.INTERFACE,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 提取继承信息
        heritage_clause = NodeHelper.get_field_by_name(node, "heritage")
        if heritage_clause:
            self._extract_heritage(heritage_clause, symbol)
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
        
        # 访问接口成员
        body = NodeHelper.get_field_by_name(node, "body")
        if body:
            for child in body.children:
                self.visit(child)
    
    # ========== 方法定义 ==========
    
    def visit_method_definition(self, node: Node) -> None:
        """访问方法定义"""
        name_node = NodeHelper.get_field_by_name(node, "name")
        if not name_node:
            return
            
        name = self.traverser.get_node_text(name_node)
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.METHOD,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 提取修饰符
        self._extract_modifiers(node, symbol)
        
        # 提取参数
        parameters = NodeHelper.get_field_by_name(node, "parameters")
        if parameters:
            symbol.parameters = self._extract_parameters(parameters)
        
        # 提取返回类型
        return_type = NodeHelper.get_field_by_name(node, "return_type")
        if return_type:
            symbol.return_type = self._extract_type_info(return_type)
        
        # 提取装饰器
        self._extract_decorators(node, symbol)
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
    
    # ========== 函数声明 ==========
    
    def visit_function_declaration(self, node: Node) -> None:
        """访问函数声明"""
        name_node = NodeHelper.get_field_by_name(node, "name")
        if not name_node:
            return
            
        name = self.traverser.get_node_text(name_node)
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.FUNCTION,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 检查是否为async函数
        if self._has_modifier(node, "async"):
            symbol.is_async = True
        
        # 提取参数
        parameters = NodeHelper.get_field_by_name(node, "parameters")
        if parameters:
            symbol.parameters = self._extract_parameters(parameters)
        
        # 提取返回类型
        return_type = NodeHelper.get_field_by_name(node, "return_type")
        if return_type:
            symbol.return_type = self._extract_type_info(return_type)
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
    
    # ========== 变量声明 ==========
    
    def visit_variable_declaration(self, node: Node) -> None:
        """访问变量声明"""
        self._extract_variable_declarators(node)
    
    def visit_lexical_declaration(self, node: Node) -> None:
        """访问词法声明（let/const）"""
        self._extract_variable_declarators(node)
    
    def _extract_variable_declarators(self, node: Node) -> None:
        """提取变量声明器"""
        # 查找所有变量声明器
        for child in node.children:
            if child.type == "variable_declarator":
                name_node = NodeHelper.get_field_by_name(child, "name")
                if not name_node:
                    continue
                
                name = self.traverser.get_node_text(name_node)
                symbol = Symbol(
                    id=None,
                    name=name,
                    symbol_type=SymbolType.VARIABLE,
                    file_path=self.file_path,
                    range=self._create_range(child),
                    scope_id=self.current_scope_id
                )
                
                # 提取类型
                type_node = NodeHelper.get_field_by_name(child, "type")
                if type_node:
                    symbol.type_info = self._extract_type_info(type_node)
                
                # 检查是否为const
                parent_text = self.traverser.get_node_text(node)
                if parent_text.startswith("const"):
                    symbol.is_readonly = True
                
                self.symbols.append(symbol)
    
    # ========== 枚举声明 ==========
    
    def visit_enum_declaration(self, node: Node) -> None:
        """访问枚举声明"""
        name_node = NodeHelper.get_field_by_name(node, "name")
        if not name_node:
            return
            
        name = self.traverser.get_node_text(name_node)
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.ENUM,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
        
        # 提取枚举成员
        body = NodeHelper.get_field_by_name(node, "body")
        if body:
            for child in body.children:
                if child.type == "enum_assignment" or child.type == "property_identifier":
                    member_name_node = NodeHelper.get_field_by_name(child, "name")
                    if not member_name_node:
                        member_name_node = child
                    
                    member_name = self.traverser.get_node_text(member_name_node)
                    member_symbol = Symbol(
                        id=None,
                        name=member_name,
                        symbol_type=SymbolType.ENUM_MEMBER,
                        file_path=self.file_path,
                        range=self._create_range(child),
                        scope_id=self.current_scope_id
                    )
                    
                    self.symbols.append(member_symbol)
    
    # ========== 类型别名 ==========
    
    def visit_type_alias_declaration(self, node: Node) -> None:
        """访问类型别名声明"""
        name_node = NodeHelper.get_field_by_name(node, "name")
        if not name_node:
            return
            
        name = self.traverser.get_node_text(name_node)
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.TYPE_ALIAS,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 提取类型定义
        type_node = NodeHelper.get_field_by_name(node, "value")
        if type_node:
            symbol.type_info = self._extract_type_info(type_node)
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
    
    # ========== 辅助方法 ==========
    
    def _create_range(self, node: Node) -> Range:
        """创建范围对象"""
        return Range(
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
        )
    
    def _extract_modifiers(self, node: Node, symbol: Symbol) -> None:
        """提取修饰符"""
        # 查找修饰符节点
        for child in node.children:
            if child.type in ["public", "private", "protected"]:
                text = self.traverser.get_node_text(child)
                if text == "public":
                    symbol.visibility = Visibility.PUBLIC
                elif text == "private":
                    symbol.visibility = Visibility.PRIVATE
                elif text == "protected":
                    symbol.visibility = Visibility.PROTECTED
            elif child.type == "static":
                symbol.is_static = True
            elif child.type == "abstract":
                symbol.is_abstract = True
            elif child.type == "readonly":
                symbol.is_readonly = True
            elif child.type == "async":
                symbol.is_async = True
    
    def _has_modifier(self, node: Node, modifier: str) -> bool:
        """检查是否有指定修饰符"""
        for child in node.children:
            if child.type == modifier:
                return True
        return False
    
    def _extract_heritage(self, heritage_node: Node, symbol: Symbol) -> None:
        """提取继承和实现信息"""
        for child in heritage_node.children:
            if child.type == "extends_clause":
                # 提取extends
                for type_node in child.children:
                    if type_node.is_named:
                        type_name = self.traverser.get_node_text(type_node)
                        if type_name not in ["extends", ","]:
                            symbol.extends.append(type_name)
            elif child.type == "implements_clause":
                # 提取implements
                for type_node in child.children:
                    if type_node.is_named:
                        type_name = self.traverser.get_node_text(type_node)
                        if type_name not in ["implements", ","]:
                            symbol.implements.append(type_name)
    
    def _extract_parameters(self, parameters_node: Node) -> List[Symbol]:
        """提取参数列表"""
        params = []
        
        for child in parameters_node.children:
            if child.type in ["required_parameter", "optional_parameter"]:
                name_node = NodeHelper.get_field_by_name(child, "pattern")
                if not name_node:
                    continue
                
                param_name = self.traverser.get_node_text(name_node)
                param_symbol = Symbol(
                    id=None,
                    name=param_name,
                    symbol_type=SymbolType.PARAMETER,
                    file_path=self.file_path,
                    range=self._create_range(child),
                    scope_id=self.current_scope_id
                )
                
                # 提取参数类型
                type_node = NodeHelper.get_field_by_name(child, "type")
                if type_node:
                    param_symbol.type_info = self._extract_type_info(type_node)
                
                params.append(param_symbol)
        
        return params
    
    def _extract_type_info(self, type_node: Node) -> TypeInfo:
        """提取类型信息"""
        type_text = self.traverser.get_node_text(type_node)
        
        # 基本类型信息
        type_info = TypeInfo(name=type_text)
        
        # 检查是否为原始类型
        primitive_types = ["number", "string", "boolean", "void", "null", "undefined", "any"]
        type_info.is_primitive = type_text in primitive_types
        
        # 检查是否为数组
        if type_node.type == "array_type" or type_text.endswith("[]"):
            type_info.is_array = True
            # 尝试提取元素类型
            element_type_node = NodeHelper.get_field_by_name(type_node, "element")
            if element_type_node:
                element_type_text = self.traverser.get_node_text(element_type_node)
                type_info.element_type = TypeInfo(name=element_type_text)
        
        # 检查是否可空
        if "?" in type_text or " | null" in type_text or " | undefined" in type_text:
            type_info.nullable = True
        
        # 检查是否为泛型
        if "<" in type_text and ">" in type_text:
            type_info.is_generic = True
            # 简单的泛型参数提取
            start = type_text.index("<")
            end = type_text.rindex(">")
            params_text = type_text[start+1:end]
            type_info.generic_params = [p.strip() for p in params_text.split(",")]
        
        return type_info
    
    def _extract_decorators(self, node: Node, symbol: Symbol) -> None:
        """提取装饰器"""
        # 查找装饰器节点
        prev = node.prev_sibling
        while prev and prev.type == "decorator":
            decorator_text = self.traverser.get_node_text(prev)
            symbol.decorators.insert(0, decorator_text)
            prev = prev.prev_sibling
    
    def _extract_documentation(self, node: Node) -> Optional[str]:
        """提取文档注释"""
        # 查找前面的注释节点
        prev = node.prev_sibling
        
        # 跳过装饰器
        while prev and prev.type == "decorator":
            prev = prev.prev_sibling
        
        # 检查是否为注释
        if prev and prev.type == "comment":
            comment_text = self.traverser.get_node_text(prev)
            # 清理注释符号
            if comment_text.startswith("/**") and comment_text.endswith("*/"):
                # JSDoc风格注释
                return comment_text[3:-2].strip()
            elif comment_text.startswith("//"):
                # 单行注释
                return comment_text[2:].strip()
        
        return None

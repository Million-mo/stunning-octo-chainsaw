"""
类型推导引擎

分析和推导符号的类型信息，处理隐式类型和复杂类型表达式。
"""

from typing import Optional, Dict, List, Set
from tree_sitter import Node

from ..models import Symbol, TypeInfo, SymbolType, Scope
from .ast_traverser import ASTTraverser, NodeHelper


class TypeInferenceEngine:
    """类型推导引擎"""
    
    # 内置类型映射
    BUILT_IN_TYPES = {
        "number", "string", "boolean", "void", "null", "undefined", 
        "any", "unknown", "never", "object"
    }
    
    # 字面量类型映射
    LITERAL_TYPE_MAPPING = {
        "number": "number",
        "string": "string",
        "true": "boolean",
        "false": "boolean",
        "null": "null",
        "undefined": "undefined",
    }
    
    def __init__(self, source_code: bytes):
        """
        初始化类型推导引擎
        
        Args:
            source_code: 源代码字节
        """
        self.source_code = source_code
        self.traverser = ASTTraverser(source_code)
        
        # 类型缓存
        self.type_cache: Dict[str, TypeInfo] = {}
        
        # 符号表引用
        self.symbols: Dict[str, Symbol] = {}
        self.scopes: List[Scope] = []
    
    def infer_types(self, symbols: List[Symbol], scopes: List[Scope]) -> None:
        """
        推导符号类型
        
        Args:
            symbols: 符号列表
            scopes: 作用域列表
        """
        self.symbols = {s.name: s for s in symbols}
        self.scopes = scopes
        
        # 第一遍：处理显式类型声明
        for symbol in symbols:
            if symbol.type_info is None and symbol.symbol_type == SymbolType.VARIABLE:
                # 尝试从初始化表达式推导类型
                # 这里需要AST节点，实际实现中需要保存节点引用
                pass
        
        # 第二遍：处理类型引用和泛型
        for symbol in symbols:
            if symbol.type_info:
                self._resolve_type_references(symbol.type_info)
    
    def infer_from_literal(self, literal_node: Node) -> Optional[TypeInfo]:
        """
        从字面量推导类型
        
        Args:
            literal_node: 字面量节点
            
        Returns:
            类型信息
        """
        node_type = literal_node.type
        
        if node_type == "number":
            return TypeInfo(name="number", is_primitive=True)
        elif node_type == "string":
            return TypeInfo(name="string", is_primitive=True)
        elif node_type in ["true", "false"]:
            return TypeInfo(name="boolean", is_primitive=True)
        elif node_type == "null":
            return TypeInfo(name="null", is_primitive=True)
        elif node_type == "undefined":
            return TypeInfo(name="undefined", is_primitive=True)
        elif node_type == "array":
            # 数组字面量
            return self._infer_array_type(literal_node)
        elif node_type == "object":
            # 对象字面量
            return self._infer_object_type(literal_node)
        
        return None
    
    def infer_from_expression(self, expr_node: Node) -> Optional[TypeInfo]:
        """
        从表达式推导类型
        
        Args:
            expr_node: 表达式节点
            
        Returns:
            类型信息
        """
        node_type = expr_node.type
        
        # 字面量
        if node_type in self.LITERAL_TYPE_MAPPING:
            type_name = self.LITERAL_TYPE_MAPPING[node_type]
            return TypeInfo(name=type_name, is_primitive=True)
        
        # 二元表达式
        if node_type == "binary_expression":
            return self._infer_binary_expression(expr_node)
        
        # 一元表达式
        if node_type == "unary_expression":
            return self._infer_unary_expression(expr_node)
        
        # 函数调用
        if node_type == "call_expression":
            return self._infer_call_expression(expr_node)
        
        # 成员访问
        if node_type == "member_expression":
            return self._infer_member_expression(expr_node)
        
        # 标识符引用
        if node_type == "identifier":
            return self._infer_identifier(expr_node)
        
        # 三元表达式
        if node_type == "ternary_expression":
            return self._infer_ternary_expression(expr_node)
        
        # 数组字面量
        if node_type == "array":
            return self._infer_array_type(expr_node)
        
        # 对象字面量
        if node_type == "object":
            return self._infer_object_type(expr_node)
        
        return None
    
    def _infer_binary_expression(self, node: Node) -> Optional[TypeInfo]:
        """推导二元表达式类型"""
        operator_node = NodeHelper.get_field_by_name(node, "operator")
        if not operator_node:
            return None
        
        operator = self.traverser.get_node_text(operator_node)
        
        # 算术运算符
        if operator in ["+", "-", "*", "/", "%", "**"]:
            # 特殊处理 + 运算符（可能是字符串连接）
            if operator == "+":
                left = NodeHelper.get_field_by_name(node, "left")
                right = NodeHelper.get_field_by_name(node, "right")
                
                if left and right:
                    left_type = self.infer_from_expression(left)
                    right_type = self.infer_from_expression(right)
                    
                    # 如果任一操作数是字符串，结果是字符串
                    if (left_type and left_type.name == "string") or \
                       (right_type and right_type.name == "string"):
                        return TypeInfo(name="string", is_primitive=True)
            
            return TypeInfo(name="number", is_primitive=True)
        
        # 比较运算符
        if operator in ["==", "!=", "===", "!==", "<", ">", "<=", ">="]:
            return TypeInfo(name="boolean", is_primitive=True)
        
        # 逻辑运算符
        if operator in ["&&", "||"]:
            return TypeInfo(name="boolean", is_primitive=True)
        
        # 位运算符
        if operator in ["&", "|", "^", "<<", ">>", ">>>"]:
            return TypeInfo(name="number", is_primitive=True)
        
        return None
    
    def _infer_unary_expression(self, node: Node) -> Optional[TypeInfo]:
        """推导一元表达式类型"""
        operator_node = NodeHelper.get_field_by_name(node, "operator")
        if not operator_node:
            return None
        
        operator = self.traverser.get_node_text(operator_node)
        
        # 逻辑非
        if operator == "!":
            return TypeInfo(name="boolean", is_primitive=True)
        
        # 数值运算符
        if operator in ["+", "-", "~"]:
            return TypeInfo(name="number", is_primitive=True)
        
        # typeof
        if operator == "typeof":
            return TypeInfo(name="string", is_primitive=True)
        
        return None
    
    def _infer_call_expression(self, node: Node) -> Optional[TypeInfo]:
        """推导函数调用表达式类型"""
        function_node = NodeHelper.get_field_by_name(node, "function")
        if not function_node:
            return None
        
        # 获取函数名
        func_name = self.traverser.get_node_text(function_node)
        
        # 查找函数符号
        if func_name in self.symbols:
            func_symbol = self.symbols[func_name]
            if func_symbol.return_type:
                return func_symbol.return_type
        
        # 内置函数类型推导
        builtin_return_types = {
            "parseInt": TypeInfo(name="number", is_primitive=True),
            "parseFloat": TypeInfo(name="number", is_primitive=True),
            "String": TypeInfo(name="string", is_primitive=True),
            "Number": TypeInfo(name="number", is_primitive=True),
            "Boolean": TypeInfo(name="boolean", is_primitive=True),
            "Array": TypeInfo(name="Array", is_array=True, is_generic=True),
        }
        
        if func_name in builtin_return_types:
            return builtin_return_types[func_name]
        
        return None
    
    def _infer_member_expression(self, node: Node) -> Optional[TypeInfo]:
        """推导成员访问表达式类型"""
        object_node = NodeHelper.get_field_by_name(node, "object")
        property_node = NodeHelper.get_field_by_name(node, "property")
        
        if not object_node or not property_node:
            return None
        
        # 获取对象类型
        object_type = self.infer_from_expression(object_node)
        if not object_type:
            return None
        
        # 获取属性名
        property_name = self.traverser.get_node_text(property_node)
        
        # 查找类型定义中的属性
        # 这里需要类型系统支持，简化实现
        
        # 特殊处理一些常见属性
        if property_name == "length" and object_type.is_array:
            return TypeInfo(name="number", is_primitive=True)
        
        return None
    
    def _infer_identifier(self, node: Node) -> Optional[TypeInfo]:
        """推导标识符类型"""
        name = self.traverser.get_node_text(node)
        
        # 查找符号
        if name in self.symbols:
            symbol = self.symbols[name]
            return symbol.type_info
        
        return None
    
    def _infer_ternary_expression(self, node: Node) -> Optional[TypeInfo]:
        """推导三元表达式类型"""
        consequence = NodeHelper.get_field_by_name(node, "consequence")
        alternative = NodeHelper.get_field_by_name(node, "alternative")
        
        if not consequence or not alternative:
            return None
        
        # 推导两个分支的类型
        consequence_type = self.infer_from_expression(consequence)
        alternative_type = self.infer_from_expression(alternative)
        
        # 如果两个分支类型相同，返回该类型
        if consequence_type and alternative_type:
            if consequence_type.name == alternative_type.name:
                return consequence_type
            
            # 否则返回联合类型（简化实现，返回any）
            return TypeInfo(name="any", is_primitive=True)
        
        return consequence_type or alternative_type
    
    def _infer_array_type(self, node: Node) -> TypeInfo:
        """推导数组类型"""
        # 检查数组元素类型
        element_types: Set[str] = set()
        
        for child in node.children:
            if child.is_named:
                element_type = self.infer_from_expression(child)
                if element_type:
                    element_types.add(element_type.name)
        
        # 如果所有元素类型相同
        if len(element_types) == 1:
            element_type_name = list(element_types)[0]
            return TypeInfo(
                name=f"{element_type_name}[]",
                is_array=True,
                element_type=TypeInfo(name=element_type_name, is_primitive=True)
            )
        
        # 否则返回any[]
        return TypeInfo(
            name="any[]",
            is_array=True,
            element_type=TypeInfo(name="any", is_primitive=True)
        )
    
    def _infer_object_type(self, node: Node) -> TypeInfo:
        """推导对象类型"""
        # 简化实现，返回object类型
        return TypeInfo(name="object", is_primitive=True)
    
    def _resolve_type_references(self, type_info: TypeInfo) -> None:
        """
        解析类型引用
        
        Args:
            type_info: 类型信息
        """
        # 检查是否为用户定义类型
        if type_info.name not in self.BUILT_IN_TYPES:
            # 查找类型定义
            if type_info.name in self.symbols:
                type_symbol = self.symbols[type_info.name]
                # 可以在这里添加更多类型信息
                pass
        
        # 处理泛型参数
        if type_info.is_generic:
            for param in type_info.generic_params:
                # 递归解析泛型参数类型
                pass
        
        # 处理数组元素类型
        if type_info.element_type:
            self._resolve_type_references(type_info.element_type)
    
    def unify_types(self, type1: TypeInfo, type2: TypeInfo) -> Optional[TypeInfo]:
        """
        类型统一（找到两个类型的最小公共超类型）
        
        Args:
            type1: 类型1
            type2: 类型2
            
        Returns:
            统一后的类型
        """
        # 如果类型相同
        if type1.name == type2.name:
            return type1
        
        # 如果其中一个是any
        if type1.name == "any" or type2.name == "any":
            return TypeInfo(name="any", is_primitive=True)
        
        # 如果一个是null/undefined，另一个不是
        if type1.name in ["null", "undefined"]:
            type2.nullable = True
            return type2
        
        if type2.name in ["null", "undefined"]:
            type1.nullable = True
            return type1
        
        # 否则返回any（简化实现）
        return TypeInfo(name="any", is_primitive=True)
    
    def is_assignable(self, from_type: TypeInfo, to_type: TypeInfo) -> bool:
        """
        检查类型是否可赋值
        
        Args:
            from_type: 源类型
            to_type: 目标类型
            
        Returns:
            是否可赋值
        """
        # any可以赋值给任何类型
        if from_type.name == "any" or to_type.name == "any":
            return True
        
        # 相同类型
        if from_type.name == to_type.name:
            return True
        
        # null/undefined可以赋值给可空类型
        if from_type.name in ["null", "undefined"] and to_type.nullable:
            return True
        
        # 这里可以添加更多类型兼容性规则
        
        return False

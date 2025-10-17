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
        "method_declaration": SymbolType.METHOD,  # 修正：原为 method_definition
        "function_declaration": SymbolType.FUNCTION,
        "variable_declaration": SymbolType.VARIABLE,
        "lexical_declaration": SymbolType.VARIABLE,
        "property_declaration": SymbolType.PROPERTY,  # 修正：原为 property_identifier
        "enum_declaration": SymbolType.ENUM,
        "enum_assignment": SymbolType.ENUM_MEMBER,
        "module": SymbolType.MODULE,
        "namespace_declaration": SymbolType.NAMESPACE,
        "type_declaration": SymbolType.TYPE_ALIAS,  # 修正：原为 type_alias_declaration
        "constructor_declaration": SymbolType.CONSTRUCTOR,  # 新增：构造函数
        
        # ArkUI 特有节点类型
        "component_declaration": SymbolType.COMPONENT,  # ArkUI 组件 (struct)
        "build_method": SymbolType.BUILD_METHOD,  # build() 方法
    }
    
    # ArkUI 装饰器类型
    ARKUI_DECORATORS = {
        # 组件装饰器
        "Entry", "Component", "Preview", "CustomDialog",
        # 状态管理装饰器
        "State", "Prop", "Link", "Provide", "Consume",
        "ObjectLink", "Observed", "Watch",
        "StorageLink", "StorageProp", "LocalStorageLink", "LocalStorageProp",
        # 样式装饰器
        "Styles", "Extend", "AnimatableExtend",
        # 并发装饰器
        "Concurrent", "Sendable",
    }
    
    # ArkUI 生命周期方法
    LIFECYCLE_METHODS = {
        "aboutToAppear", "aboutToDisappear",
        "onPageShow", "onPageHide",
        "onBackPress", "onLayout", "onMeasure",
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
        
        # Export 状态跟踪
        self._current_is_exported = False
        self._current_is_export_default = False
    
    # ========== 辅助方法 ==========
    
    def _get_child_by_type(self, node: Node, type_name: str) -> Optional[Node]:
        """通过类型获取第一个匹配的子节点"""
        for child in node.children:
            if child.type == type_name:
                return child
        return None
    
    def _get_children_by_type(self, node: Node, type_name: str) -> List[Node]:
        """通过类型获取所有匹配的子节点"""
        return [child for child in node.children if child.type == type_name]
    
    def _get_identifier_name(self, node: Node) -> Optional[str]:
        """获取节点的 identifier 子节点的文本"""
        id_node = self._get_child_by_type(node, "identifier")
        if id_node:
            return self.traverser.get_node_text(id_node)
        return None
    
    def _has_child_type(self, node: Node, type_name: str) -> bool:
        """检查节点是否有指定类型的子节点"""
        return self._get_child_by_type(node, type_name) is not None
        
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
    
    # ========== Export 声明处理 ==========
    
    def visit_export_declaration(self, node: Node) -> None:
        """
        访问 export 声明
        
        export_declaration 是包装节点，结构如下：
        export_declaration
          ├── export (关键字)
          ├── default (可选，用于 export default)
          └── 实际声明（class_declaration、function_declaration 等）
        
        Args:
            node: export_declaration 节点
        """
        # 检查是否为 export default
        is_export_default = self._has_child_type(node, "default")
        
        # 遍历子节点，找到实际的声明节点
        for child in node.children:
            # 跳过 export 和 default 关键字
            if child.type in ["export", "default"]:
                continue
            
            # 处理实际的声明节点
            if child.is_named:
                # 保存 export 状态
                original_export_state = getattr(self, '_current_is_exported', False)
                original_export_default_state = getattr(self, '_current_is_export_default', False)
                
                self._current_is_exported = True
                self._current_is_export_default = is_export_default
                
                # 访问实际声明
                self.visit(child)
                
                # 恢复状态
                self._current_is_exported = original_export_state
                self._current_is_export_default = original_export_default_state
    
    # ========== ArkUI 组件声明 ==========
    
    def visit_component_declaration(self, node: Node) -> None:
        """
        访问 ArkUI 组件声明 (struct)
        
        ArkUI 组件使用 struct 关键字声明，通常带有 @Component 装饰器。
        结构：
        component_declaration
          ├── decorator (@Entry, @Component, @Preview 等)
          ├── struct (关键字)
          ├── identifier (组件名)
          └── component_body (组件体)
        """
        # 获取组件名
        name = self._get_identifier_name(node)
        if not name:
            return
        
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.COMPONENT,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 标记 export 状态
        symbol.is_exported = getattr(self, '_current_is_exported', False)
        symbol.is_export_default = getattr(self, '_current_is_export_default', False)
        
        # 提取 ArkUI 装饰器（@Entry, @Component, @Preview 等）
        self._extract_arkui_decorators(node, symbol)
        
        # 确定组件类型
        if "Entry" in symbol.arkui_decorators:
            symbol.component_type = "Entry"
        elif "Preview" in symbol.arkui_decorators:
            symbol.component_type = "Preview"
        elif "Component" in symbol.arkui_decorators:
            symbol.component_type = "Component"
        elif "CustomDialog" in symbol.arkui_decorators:
            symbol.component_type = "CustomDialog"
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
        
        # 访问组件成员：查找 component_body 子节点
        component_body = self._get_child_by_type(node, "component_body")
        if component_body:
            # 保存当前作用域
            parent_scope = self.current_scope_id
            
            for child in component_body.children:
                self.visit(child)
            
            # 恢复作用域
            self.current_scope_id = parent_scope
    
    # ========== 类声明 ==========
    
    def visit_class_declaration(self, node: Node) -> None:
        """访问类声明"""
        # 获取类名：identifier 是直接子节点
        name = self._get_identifier_name(node)
        if not name:
            return
            
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.CLASS,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 标记 export 状态
        symbol.is_exported = getattr(self, '_current_is_exported', False)
        symbol.is_export_default = getattr(self, '_current_is_export_default', False)
        
        # 提取修饰符（public/private/protected/static/abstract）
        self._extract_modifiers(node, symbol)
        
        # 提取继承信息：查找 extends 关键字后的 type_annotation
        self._extract_class_heritage(node, symbol)
        
        # 提取装饰器
        self._extract_decorators(node, symbol)
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
        
        # 访问类成员：查找 class_body 子节点
        class_body = self._get_child_by_type(node, "class_body")
        if class_body:
            # 保存当前作用域
            parent_scope = self.current_scope_id
            # 设置新的作用域（类作用域）
            # 注意：实际的scope_id需要在作用域分析阶段确定
            
            for child in class_body.children:
                self.visit(child)
            
            # 恢复作用域
            self.current_scope_id = parent_scope
    
    # ========== 接口声明 ==========
    
    def visit_interface_declaration(self, node: Node) -> None:
        """访问接口声明"""
        # 获取接口名：identifier 是直接子节点
        name = self._get_identifier_name(node)
        if not name:
            return
            
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.INTERFACE,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 标记 export 状态
        symbol.is_exported = getattr(self, '_current_is_exported', False)
        symbol.is_export_default = getattr(self, '_current_is_export_default', False)
        
        # 提取继承信息（接口可以 extends 其他接口）
        self._extract_interface_heritage(node, symbol)
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
        
        # 访问接口成员：查找 object_type 子节点（不是 body）
        object_type = self._get_child_by_type(node, "object_type")
        if object_type:
            for child in object_type.children:
                self.visit(child)
    
    # ========== 方法定义 ==========
    
    def visit_method_declaration(self, node: Node) -> None:
        """访问方法声明（增强版，支持 ArkUI 特性）"""
        # 获取方法名：identifier 是直接子节点
        name = self._get_identifier_name(node)
        if not name:
            return
        
        # 检查是否为 ArkUI 样式函数 (@Styles 装饰器)
        decorators = self._get_decorators(node)
        is_styles = "Styles" in [d.get("name") for d in decorators]
        
        # 检查是否为生命周期方法
        is_lifecycle = name in self.LIFECYCLE_METHODS
        
        # 确定符号类型
        if is_styles:
            symbol_type = SymbolType.STYLE_FUNCTION
        elif is_lifecycle:
            symbol_type = SymbolType.LIFECYCLE_METHOD
        else:
            symbol_type = SymbolType.METHOD
            
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=symbol_type,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 提取修饰符
        self._extract_modifiers(node, symbol)
        
        # 提取 ArkUI 装饰器
        self._extract_arkui_decorators(node, symbol)
        
        # 提取参数：查找 parameter_list 子节点
        parameter_list = self._get_child_by_type(node, "parameter_list")
        if parameter_list:
            symbol.parameters = self._extract_parameters(parameter_list)
        
        # 提取返回类型：查找 ":" 后的 type_annotation 子节点
        symbol.return_type = self._extract_return_type(node)
        
        # 提取装饰器
        self._extract_decorators(node, symbol)
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
    
    # ========== 构造函数声明 ==========
    
    def visit_constructor_declaration(self, node: Node) -> None:
        """访问构造函数声明"""
        symbol = Symbol(
            id=None,
            name="constructor",
            symbol_type=SymbolType.CONSTRUCTOR,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 提取参数
        parameter_list = self._get_child_by_type(node, "parameter_list")
        if parameter_list:
            symbol.parameters = self._extract_parameters(parameter_list)
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
    
    # ========== 属性声明 ==========
    
    def visit_property_declaration(self, node: Node) -> None:
        """访问属性声明（增强版，支持 ArkUI 装饰器）"""
        # 获取属性名：identifier 是直接子节点
        name = self._get_identifier_name(node)
        if not name:
            return
            
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.PROPERTY,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 提取修饰符
        self._extract_modifiers(node, symbol)
        
        # 提取 ArkUI 装饰器（@State, @Prop, @Link 等）
        self._extract_arkui_decorators(node, symbol)
        
        # 提取类型：查找 ":" 后的 type_annotation 子节点
        found_colon = False
        for child in node.children:
            if child.type == ":":
                found_colon = True
            elif found_colon and child.type == "type_annotation":
                symbol.type_info = self._extract_type_info(child)
                break
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
    
    # ========== ArkUI build 方法 ==========
    
    def visit_build_method(self, node: Node) -> None:
        """
        访问 ArkUI build 方法
        
        build() 是 ArkUI 组件的核心方法，用于构建 UI 结构。
        结构：
        build_method
          ├── build (关键字)
          ├── ( (左括号)
          ├── ) (右括号)
          └── build_body (UI 构建体)
        """
        symbol = Symbol(
            id=None,
            name="build",
            symbol_type=SymbolType.BUILD_METHOD,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        # 提取 UI 组件调用和样式绑定（在 build_body 中）
        build_body = self._get_child_by_type(node, "build_body")
        if build_body:
            # 提取样式绑定和事件处理器
            self._extract_ui_bindings(build_body, symbol)
        
        self.symbols.append(symbol)
    
    # ========== 函数声明 ==========
    
    def visit_function_declaration(self, node: Node) -> None:
        """访问函数声明"""
        # 获取函数名：identifier 是直接子节点
        name = self._get_identifier_name(node)
        if not name:
            return
            
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.FUNCTION,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 标记 export 状态
        symbol.is_exported = getattr(self, '_current_is_exported', False)
        symbol.is_export_default = getattr(self, '_current_is_export_default', False)
        
        # 检查是否为async函数
        if self._has_child_type(node, "async"):
            symbol.is_async = True
        
        # 提取参数：查找 parameter_list 子节点
        parameter_list = self._get_child_by_type(node, "parameter_list")
        if parameter_list:
            symbol.parameters = self._extract_parameters(parameter_list)
        
        # 提取返回类型：查找 ":" 后的 type_annotation 子节点
        symbol.return_type = self._extract_return_type(node)
        
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
                # 获取变量名：identifier 是直接子节点
                name = self._get_identifier_name(child)
                if not name:
                    continue
                
                symbol = Symbol(
                    id=None,
                    name=name,
                    symbol_type=SymbolType.VARIABLE,
                    file_path=self.file_path,
                    range=self._create_range(child),
                    scope_id=self.current_scope_id
                )
                
                # 标记 export 状态
                symbol.is_exported = getattr(self, '_current_is_exported', False)
                symbol.is_export_default = getattr(self, '_current_is_export_default', False)
                
                # 提取类型：查找 type_annotation 子节点
                type_annotation = self._get_child_by_type(child, "type_annotation")
                if type_annotation:
                    symbol.type_info = self._extract_type_info(type_annotation)
                
                # 检查是否为const：检查父节点是否有 const 关键字
                if self._has_child_type(node, "const"):
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
        
        # 标记 export 状态
        symbol.is_exported = getattr(self, '_current_is_exported', False)
        symbol.is_export_default = getattr(self, '_current_is_export_default', False)
        
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
    
    def visit_type_declaration(self, node: Node) -> None:
        """访问类型别名声明（修正：节点类型为 type_declaration）"""
        # 获取类型名：identifier 是直接子节点
        name = self._get_identifier_name(node)
        if not name:
            return
            
        symbol = Symbol(
            id=None,
            name=name,
            symbol_type=SymbolType.TYPE_ALIAS,
            file_path=self.file_path,
            range=self._create_range(node),
            scope_id=self.current_scope_id
        )
        
        # 标记 export 状态
        symbol.is_exported = getattr(self, '_current_is_exported', False)
        symbol.is_export_default = getattr(self, '_current_is_export_default', False)
        
        # 提取类型定义：查找 "=" 后的 type_annotation 子节点
        # 需要找到 "=" 之后的 type_annotation
        found_equals = False
        for child in node.children:
            if child.type == "=":
                found_equals = True
            elif found_equals and child.type == "type_annotation":
                symbol.type_info = self._extract_type_info(child)
                break
        
        # 提取文档注释
        symbol.documentation = self._extract_documentation(node)
        
        self.symbols.append(symbol)
    
    # 为了兼容性，保留旧名称
    def visit_type_alias_declaration(self, node: Node) -> None:
        """访问类型别名声明（旧名称，转发到新方法）"""
        self.visit_type_declaration(node)
    
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
        """提取继承和实现信息（旧版本，保留以免兼容性问题）"""
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
    
    def _extract_class_heritage(self, node: Node, symbol: Symbol) -> None:
        """
        提取类的继承信息
        根据 tree-sitter-arkts 实际解析结果：
        - extends 关键字后跟 type_annotation
        - implements 子句可能被解析为 ERROR 节点
        """
        # 查找 extends 关键字
        found_extends = False
        for i, child in enumerate(node.children):
            if child.type == "extends":
                found_extends = True
                # 下一个 type_annotation 就是继承的基类
                if i + 1 < len(node.children):
                    next_node = node.children[i + 1]
                    if next_node.type == "type_annotation":
                        # 获取 type_annotation 中的 identifier
                        base_class_node = self._get_child_by_type(next_node, "identifier")
                        if base_class_node:
                            base_class = self.traverser.get_node_text(base_class_node)
                            symbol.extends.append(base_class)
        
        # 注意：implements 可能被解析为 ERROR 节点，暂时无法准确提取
    
    def _extract_interface_heritage(self, node: Node, symbol: Symbol) -> None:
        """
        提取接口的继承信息
        接口可以 extends 其他接口
        """
        # 查找 extends 关键字
        found_extends = False
        for i, child in enumerate(node.children):
            if child.type == "extends":
                found_extends = True
                # 下一个 type_annotation 就是继承的接口
                if i + 1 < len(node.children):
                    next_node = node.children[i + 1]
                    if next_node.type == "type_annotation":
                        # 获取 type_annotation 中的 identifier
                        base_interface_node = self._get_child_by_type(next_node, "identifier")
                        if base_interface_node:
                            base_interface = self.traverser.get_node_text(base_interface_node)
                            symbol.extends.append(base_interface)
    
    def _extract_return_type(self, node: Node) -> Optional[TypeInfo]:
        """
        提取返回类型
        根据 tree-sitter-arkts 实际解析结果：
        - 查找 ":" 后的 type_annotation 子节点
        """
        found_colon = False
        for child in node.children:
            if child.type == ":":
                found_colon = True
            elif found_colon and child.type == "type_annotation":
                return self._extract_type_info(child)
        return None
    
    def _extract_parameters(self, parameters_node: Node) -> List[Symbol]:
        """
        提取参数列表
        根据 tree-sitter-arkts 实际解析结果：
        - parameter_list 包含多个 parameter 子节点
        - parameter 包含 identifier、":"、type_annotation
        """
        params = []
        
        for child in parameters_node.children:
            # 只处理 parameter 类型的子节点
            if child.type == "parameter":
                # 获取参数名：identifier 是直接子节点
                param_name = self._get_identifier_name(child)
                if not param_name:
                    continue
                
                param_symbol = Symbol(
                    id=None,
                    name=param_name,
                    symbol_type=SymbolType.PARAMETER,
                    file_path=self.file_path,
                    range=self._create_range(child),
                    scope_id=self.current_scope_id
                )
                
                # 提取参数类型：查找 ":" 后的 type_annotation
                found_colon = False
                for param_child in child.children:
                    if param_child.type == ":":
                        found_colon = True
                    elif found_colon and param_child.type == "type_annotation":
                        param_symbol.type_info = self._extract_type_info(param_child)
                        break
                
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
            element_type_node = self._get_child_by_type(type_node, "identifier")
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
    
    # ========== ArkUI 特有辅助方法 ==========
    
    def _get_decorators(self, node: Node) -> List[Dict[str, Any]]:
        """
        获取节点的所有装饰器信息
        
        Returns:
            装饰器列表，每个装饰器包含 name 和可选的 arguments
        """
        decorators = []
        
        # 查找节点的所有 decorator 子节点（对于 property_declaration）
        for child in node.children:
            if child.type == "decorator":
                decorator_info = self._parse_decorator(child)
                if decorator_info:
                    decorators.append(decorator_info)
        
        # 如果没有找到子节点装饰器，查找前面的 decorator 兄弟节点（对于 class/method）
        if not decorators:
            prev = node.prev_sibling
            while prev and prev.type == "decorator":
                decorator_info = self._parse_decorator(prev)
                if decorator_info:
                    decorators.insert(0, decorator_info)
                prev = prev.prev_sibling
        
        return decorators
    
    def _parse_decorator(self, decorator_node: Node) -> Optional[Dict[str, Any]]:
        """
        解析装饰器节点
        
        decorator 节点结构：
        decorator
          ├── @ (符号)
          ├── State/Component/identifier 等 (装饰器名)
          └── call_expression (可选，带参数的装饰器)
        
        Returns:
            {"name": "装饰器名", "arguments": [参数列表]}
        """
        # 获取装饰器名
        name = None
        arguments = []
        
        for child in decorator_node.children:
            # 跳过 @ 符号
            if child.type == "@":
                continue
            
            # 装饰器名可能是 identifier 或者直接的文本节点（如 State, Component）
            # 注意：State, Component 等节点 is_named=False
            if not name and child.type not in ["(", ")", "@"]:
                # 如果是 call_expression，需要特殊处理
                if child.type == "call_expression":
                    # 带参数的装饰器，如 @Extend(Text)
                    # 首先获取装饰器名
                    for call_child in child.children:
                        if call_child.type == "identifier" or (call_child.type not in ["(", ")", "arguments"]):
                            name = self.traverser.get_node_text(call_child)
                            break
                    # 然后提取参数
                    for call_child in child.children:
                        if call_child.type == "arguments":
                            for arg_child in call_child.children:
                                if arg_child.type not in ["(", ")", ","]:
                                    arg_text = self.traverser.get_node_text(arg_child)
                                    arguments.append(arg_text)
                else:
                    # 普通装饰器，直接获取文本
                    name = self.traverser.get_node_text(child)
        
        if name:
            result: Dict[str, Any] = {"name": name}
            if arguments:
                result["arguments"] = arguments
            return result
        
        return None
    
    def _extract_arkui_decorators(self, node: Node, symbol: Symbol) -> None:
        """
        提取 ArkUI 特有装饰器
        
        将 ArkUI 装饰器（@State, @Prop, @Link 等）保存到 symbol.arkui_decorators
        """
        decorators = self._get_decorators(node)
        
        for decorator in decorators:
            decorator_name = decorator.get("name")
            if decorator_name in self.ARKUI_DECORATORS:
                # 保存 ArkUI 装饰器详情
                symbol.arkui_decorators[decorator_name] = decorator.get("arguments", [])
    
    def _extract_ui_bindings(self, build_body_node: Node, symbol: Symbol) -> None:
        """
        提取 build() 方法中的 UI 绑定
        
        包括：
        - 样式绑定（如 .width(), .height()）
        - 事件处理器（如 .onClick()）
        - 资源引用（如 $r('app.media.icon')）
        """
        # 遍历 build_body 查找链式调用和资源引用
        self._traverse_ui_tree(build_body_node, symbol)
    
    def _traverse_ui_tree(self, node: Node, symbol: Symbol) -> None:
        """
        递归遍历 UI 树，提取样式和事件绑定
        """
        # 检查当前节点
        node_text = self.traverser.get_node_text(node)
        
        # 提取样式绑定（以 . 开头的方法调用）
        if node.type == "member_expression":
            # 检查是否为样式方法（如 .width(), .height()）
            member_name = self._get_member_name(node)
            if member_name and self._is_style_method(member_name):
                if member_name not in symbol.style_bindings:
                    symbol.style_bindings.append(member_name)
        
        # 提取事件处理器（如 .onClick(handler)）
        elif node.type == "call_expression":
            call_text = self.traverser.get_node_text(node)
            if ".on" in call_text or ".onClick" in call_text:
                # 提取事件名和处理器
                event_info = self._extract_event_handler(node)
                if event_info:
                    event_name, handler = event_info
                    symbol.event_handlers[event_name] = handler
        
        # 提取资源引用（$r('app.media.icon')）
        if "$r(" in node_text or "$rawfile(" in node_text:
            resource_ref = self._extract_resource_reference(node)
            if resource_ref and resource_ref not in symbol.resource_refs:
                symbol.resource_refs.append(resource_ref)
        
        # 递归遍历子节点
        for child in node.children:
            self._traverse_ui_tree(child, symbol)
    
    def _get_member_name(self, member_expression_node: Node) -> Optional[str]:
        """获取成员表达式的成员名"""
        # member_expression 结构：expression . identifier
        for child in member_expression_node.children:
            if child.type == "identifier" and child.prev_sibling and child.prev_sibling.type == ".":
                return self.traverser.get_node_text(child)
        return None
    
    def _is_style_method(self, method_name: str) -> bool:
        """检查是否为样式方法"""
        # ArkUI 常见样式方法
        style_methods = {
            "width", "height", "backgroundColor", "fontSize", "fontColor",
            "fontWeight", "margin", "padding", "border", "borderRadius",
            "opacity", "visibility", "position", "zIndex", "rotate",
            "scale", "translate", "animation", "transition"
        }
        return method_name in style_methods
    
    def _extract_event_handler(self, call_expression_node: Node) -> Optional[tuple]:
        """
        提取事件处理器
        
        Returns:
            (event_name, handler) 或 None
        """
        call_text = self.traverser.get_node_text(call_expression_node)
        
        # 提取事件名（如 onClick, onTouch）
        event_name = None
        handler = None
        
        for child in call_expression_node.children:
            if child.type == "member_expression":
                member_name = self._get_member_name(child)
                if member_name and member_name.startswith("on"):
                    event_name = member_name
            elif child.type == "arguments":
                # 提取处理器函数
                for arg_child in child.children:
                    if arg_child.type in ["arrow_function", "function", "identifier"]:
                        handler = self.traverser.get_node_text(arg_child)
                        # 限制长度，避免太长
                        if len(handler) > 50:
                            handler = handler[:50] + "..."
                        break
        
        if event_name and handler:
            return (event_name, handler)
        return None
    
    def _extract_resource_reference(self, node: Node) -> Optional[str]:
        """
        提取资源引用
        
        ArkUI 资源引用格式：
        - $r('app.media.icon')
        - $rawfile('image.png')
        """
        node_text = self.traverser.get_node_text(node)
        
        # 提取 $r() 或 $rawfile() 中的资源路径
        if "$r(" in node_text:
            # 简单的正则提取
            import re
            match = re.search(r"\$r\(['\"]([^'\"]+)['\"]\)", node_text)
            if match:
                return match.group(1)
        elif "$rawfile(" in node_text:
            import re
            match = re.search(r"\$rawfile\(['\"]([^'\"]+)['\"]\)", node_text)
            if match:
                return match.group(1)
        
        return None

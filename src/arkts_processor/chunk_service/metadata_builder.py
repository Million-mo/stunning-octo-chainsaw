"""
Chunk 元数据构建器

构建 Chunk 的扩展元数据。
"""

from typing import List, Optional, Dict, Any
from ..models import Symbol, SymbolType, Visibility
from ..chunk_models import ChunkMetadata, PositionRange, Parameter, TypeInfo


class ChunkMetadataBuilder:
    """Chunk 元数据构建器"""
    
    # ArkUI 生命周期方法列表
    LIFECYCLE_HOOKS = [
        "aboutToAppear",
        "aboutToDisappear",
        "onPageShow",
        "onPageHide",
        "onBackPress",
        "onWillApplyTheme",
        "onDidBuild"
    ]
    
    def __init__(self):
        """初始化元数据构建器"""
        pass
    
    def build_metadata(self, symbol: Symbol, source_text: str) -> ChunkMetadata:
        """
        构建完整的 Chunk 元数据
        
        Args:
            symbol: 符号对象
            source_text: 源代码文本
            
        Returns:
            ChunkMetadata 对象
        """
        # 提取位置范围
        position_range = self._extract_position_range(symbol)
        
        # 提取装饰器
        decorators = self.extract_decorators(symbol)
        
        # 提取可见性
        visibility = self._extract_visibility(symbol)
        
        # 提取参数列表
        parameters = self.extract_parameters(symbol)
        
        # 提取返回类型
        return_type = self.extract_return_type(symbol)
        
        # 计算依赖关系
        dependencies = self.calculate_dependencies(symbol)
        
        # 提取语义标签
        tags = self.extract_tags(symbol)
        
        # 创建基础元数据
        metadata = ChunkMetadata(
            range=position_range,
            decorators=decorators,
            visibility=visibility,
            parameters=parameters,
            return_type=return_type,
            dependencies=dependencies,
            tags=tags
        )
        
        # 如果是 ArkUI 组件，添加特有元数据
        if symbol.symbol_type == SymbolType.COMPONENT:
            self._add_arkui_metadata(metadata, symbol, source_text)
        
        return metadata
    
    def _extract_position_range(self, symbol: Symbol) -> PositionRange:
        """
        提取位置范围
        
        Args:
            symbol: 符号对象
            
        Returns:
            PositionRange 对象
        """
        return PositionRange(
            start_line=symbol.range.start.line,
            end_line=symbol.range.end.line,
            start_column=symbol.range.start.column,
            end_column=symbol.range.end.column
        )
    
    def extract_decorators(self, symbol: Symbol) -> List[str]:
        """
        提取装饰器列表
        
        Args:
            symbol: 符号对象
            
        Returns:
            装饰器列表
        """
        decorators = symbol.decorators.copy() if symbol.decorators else []
        
        # 添加 ArkUI 特有装饰器
        if symbol.arkui_decorators:
            for decorator_name in symbol.arkui_decorators.keys():
                if decorator_name not in decorators:
                    decorators.append(f"@{decorator_name}")
        
        return decorators
    
    def _extract_visibility(self, symbol: Symbol) -> str:
        """
        提取可见性
        
        Args:
            symbol: 符号对象
            
        Returns:
            可见性字符串
        """
        if isinstance(symbol.visibility, Visibility):
            return symbol.visibility.value
        return "public"
    
    def extract_parameters(self, symbol: Symbol) -> List[Parameter]:
        """
        提取参数列表
        
        Args:
            symbol: 符号对象
            
        Returns:
            Parameter 列表
        """
        parameters = []
        
        for param_symbol in symbol.parameters:
            param = Parameter(
                name=param_symbol.name,
                type=param_symbol.type_info.to_string() if param_symbol.type_info else "any",
                default_value=param_symbol.metadata.get("default_value")
            )
            parameters.append(param)
        
        return parameters
    
    def extract_return_type(self, symbol: Symbol) -> Optional[TypeInfo]:
        """
        提取返回类型
        
        Args:
            symbol: 符号对象
            
        Returns:
            TypeInfo 对象或 None
        """
        if not symbol.return_type:
            return None
        
        return TypeInfo(
            name=symbol.return_type.name,
            is_primitive=symbol.return_type.is_primitive,
            is_array=symbol.return_type.is_array,
            generic_params=symbol.return_type.generic_params.copy()
        )
    
    def calculate_dependencies(self, symbol: Symbol) -> List[str]:
        """
        计算符号的依赖关系
        
        从多个来源提取依赖：
        1. 类型信息 (type_info)
        2. 返回类型 (return_type)
        3. 参数类型 (parameters)
        4. 继承 (extends)
        5. 实现 (implements)
        6. 成员类型 (members)
        7. ArkUI 资源引用 (resource_refs)
        
        Args:
            symbol: 符号对象
            
        Returns:
            依赖符号列表
        """
        dependencies = set()
        
        # Primitive 类型列表（不包含 Promise, Map, Set, Array 等集合类型）
        primitive_types = {
            "string", "number", "boolean", "void", "any", "unknown", "never",
            "Date", "Object", "Function",
            "int", "float", "double", "char", "byte"
        }
        
        # 1. 从类型信息中提取
        if symbol.type_info and not symbol.type_info.is_primitive:
            type_name = symbol.type_info.name
            if type_name not in primitive_types:
                dependencies.add(type_name)
            
            # 从泛型参数中提取
            if symbol.type_info.generic_params:
                for param in symbol.type_info.generic_params:
                    if param not in primitive_types:
                        dependencies.add(param)
        
        # 2. 从返回类型中提取
        if symbol.return_type and not symbol.return_type.is_primitive:
            return_type_name = symbol.return_type.name
            if return_type_name not in primitive_types:
                dependencies.add(return_type_name)
            
            # 从泛型参数中提取
            if symbol.return_type.generic_params:
                for param in symbol.return_type.generic_params:
                    if param not in primitive_types:
                        dependencies.add(param)
        
        # 3. 从参数中提取
        for param in symbol.parameters:
            if param.type_info and not param.type_info.is_primitive:
                param_type_name = param.type_info.name
                if param_type_name not in primitive_types:
                    dependencies.add(param_type_name)
                
                # 从泛型参数中提取
                if param.type_info.generic_params:
                    for gen_param in param.type_info.generic_params:
                        if gen_param not in primitive_types:
                            dependencies.add(gen_param)
        
        # 4. 从继承中提取
        if symbol.extends:
            dependencies.update(symbol.extends)
        
        # 5. 从实现中提取
        if symbol.implements:
            dependencies.update(symbol.implements)
        
        # 6. 从成员中提取
        for member in symbol.members:
            if member.type_info and not member.type_info.is_primitive:
                member_type_name = member.type_info.name
                if member_type_name not in primitive_types:
                    dependencies.add(member_type_name)
                
                # 从泛型参数中提取
                if member.type_info.generic_params:
                    for param in member.type_info.generic_params:
                        if param not in primitive_types:
                            dependencies.add(param)
        
        # 7. 从 ArkUI 资源引用中提取
        if symbol.resource_refs:
            dependencies.update(symbol.resource_refs)
        
        # 排序并返回
        return sorted(list(dependencies))
    
    def extract_tags(self, symbol: Symbol) -> List[str]:
        """
        提取语义标签（5 维度）
        
        维度 1: 符号属性标签 (async, static, abstract, readonly)
        维度 2: 可见性标签 (public, private, protected)
        维度 3: 符号类型标签 (ui-component, entry, preview, function, class)
        维度 4: 函数纯度标签 (pure-function, has-side-effects)
        维度 5: ArkUI 特有标签 (lifecycle, event-handler, has-state)
        
        Args:
            symbol: 符号对象
            
        Returns:
            标签列表
        """
        tags = []
        
        # 维度 3: 符号类型标签（优先级最高）
        if symbol.symbol_type == SymbolType.COMPONENT:
            tags.append("ui-component")
            
            # 组件类型标签
            if symbol.component_type:
                tags.append(symbol.component_type.lower())
            
            # 检查装饰器
            if "@Entry" in symbol.decorators or any("Entry" in d for d in symbol.decorators):
                tags.append("entry")
            if "@Preview" in symbol.decorators or any("Preview" in d for d in symbol.decorators):
                tags.append("preview")
        
        elif symbol.symbol_type in [SymbolType.FUNCTION, SymbolType.METHOD]:
            tags.append("function")
        
        elif symbol.symbol_type == SymbolType.CLASS:
            tags.append("class")
        
        elif symbol.symbol_type == SymbolType.INTERFACE:
            tags.append("interface")
        
        elif symbol.symbol_type == SymbolType.ENUM:
            tags.append("enum")
        
        # 维度 5: ArkUI 特有标签
        if symbol.symbol_type == SymbolType.STYLE_FUNCTION:
            tags.append("style")
        
        if symbol.symbol_type == SymbolType.BUILD_METHOD:
            tags.append("build")
        
        # 生命周期方法标签
        if symbol.name in self.LIFECYCLE_HOOKS:
            tags.append("lifecycle")
        
        # 事件处理器标签
        if symbol.event_handlers:
            tags.append("event-handler")
        
        # 状态管理标签
        has_state = False
        for member in symbol.members:
            if member.symbol_type == SymbolType.PROPERTY:
                if any("State" in d for d in member.decorators):
                    has_state = True
                    break
        if has_state:
            tags.append("has-state")
        
        # 维度 1: 符号属性标签
        if symbol.is_async:
            tags.append("async")
        
        if symbol.is_static:
            tags.append("static")
        
        if symbol.is_abstract:
            tags.append("abstract")
        
        if symbol.is_readonly:
            tags.append("readonly")
        
        # 维度 2: 可见性标签
        if symbol.visibility == Visibility.PUBLIC:
            tags.append("public")
        elif symbol.visibility == Visibility.PRIVATE:
            tags.append("private")
        elif symbol.visibility == Visibility.PROTECTED:
            tags.append("protected")
        
        # 维度 4: 函数纯度标签
        if symbol.symbol_type in [SymbolType.FUNCTION, SymbolType.METHOD]:
            if self._has_side_effects(symbol):
                tags.append("has-side-effects")
            else:
                tags.append("pure-function")
        
        return tags
    
    def _has_side_effects(self, symbol: Symbol) -> bool:
        """
        判断函数是否有副作用（简化版）
        
        Args:
            symbol: 符号对象
            
        Returns:
            是否有副作用
        """
        # 简化判断：如果函数有返回值且没有修改外部状态的明显标志，认为是纯函数
        # 实际实现需要更复杂的分析
        
        # 如果没有返回值，可能有副作用
        if not symbol.return_type:
            return True
        
        # 如果是 async 函数，通常有副作用（I/O 操作）
        if symbol.is_async:
            return True
        
        # 默认认为有副作用
        return True
    
    def _add_arkui_metadata(self, metadata: ChunkMetadata, symbol: Symbol, source_text: str):
        """
        为 ArkUI 组件添加特有元数据
        
        Args:
            metadata: ChunkMetadata 对象
            symbol: 符号对象
            source_text: 源代码文本
        """
        # 设置组件类型
        if symbol.component_type:
            metadata.component_type = symbol.component_type
        elif "@Entry" in symbol.decorators:
            metadata.component_type = "Entry"
        elif "@Component" in symbol.decorators:
            metadata.component_type = "Component"
        elif "@Preview" in symbol.decorators:
            metadata.component_type = "Preview"
        
        # 提取 @State 变量
        metadata.state_vars = self._extract_state_vars(symbol, source_text)
        
        # 提取生命周期方法
        metadata.lifecycle_hooks = self._extract_lifecycle_hooks(symbol)
        
        # 提取事件处理器
        metadata.event_handlers = self._extract_event_handlers(source_text)
        
        # 提取资源引用
        metadata.resource_refs = symbol.resource_refs.copy() if symbol.resource_refs else []
    
    def _extract_state_vars(self, symbol: Symbol, source_text: str) -> List[Dict[str, str]]:
        """
        提取 @State 状态变量
        
        Args:
            symbol: 符号对象
            source_text: 源代码文本
            
        Returns:
            状态变量列表
        """
        state_vars = []
        
        # 从成员中查找带 @State 装饰器的属性
        for member in symbol.members:
            if member.symbol_type == SymbolType.PROPERTY:
                if "@State" in member.decorators or any("State" in d for d in member.decorators):
                    state_vars.append({
                        "name": member.name,
                        "type": member.type_info.to_string() if member.type_info else "any"
                    })
        
        return state_vars
    
    def _extract_lifecycle_hooks(self, symbol: Symbol) -> List[str]:
        """
        提取使用的生命周期方法
        
        Args:
            symbol: 符号对象
            
        Returns:
            生命周期方法列表
        """
        hooks = []
        
        # 从成员方法中查找生命周期方法
        for member in symbol.members:
            if member.symbol_type == SymbolType.METHOD:
                if member.name in self.LIFECYCLE_HOOKS:
                    hooks.append(member.name)
        
        return hooks
    
    def _extract_event_handlers(self, source_text: str) -> List[str]:
        """
        提取事件处理器（简化版）
        
        Args:
            source_text: 源代码文本
            
        Returns:
            事件处理器列表
        """
        event_handlers = []
        
        # 常见的事件处理器关键字
        event_keywords = [
            "onClick", "onChange", "onTouch", "onHover",
            "onFocus", "onBlur", "onAppear", "onDisappear",
            "onAreaChange", "onSizeChange"
        ]
        
        for keyword in event_keywords:
            if keyword in source_text:
                event_handlers.append(keyword)
        
        return event_handlers

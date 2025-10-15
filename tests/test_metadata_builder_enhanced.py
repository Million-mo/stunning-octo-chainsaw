"""
ChunkMetadataBuilder 增强功能单元测试

测试动态上下文控制方案中的元数据构建功能：
1. 依赖关系计算
2. 5 维度标签提取
3. 函数元数据构建
4. 组件元数据构建
5. 装饰器提取
"""

import pytest
from src.arkts_processor.chunk_service.metadata_builder import ChunkMetadataBuilder
from src.arkts_processor.models import (
    Symbol, SymbolType, Visibility, TypeInfo, Position, Range
)


class TestChunkMetadataBuilder:
    """ChunkMetadataBuilder 测试类"""
    
    @pytest.fixture
    def builder(self):
        """创建 ChunkMetadataBuilder 实例"""
        return ChunkMetadataBuilder()
    
    @pytest.fixture
    def sample_function_symbol(self):
        """创建示例函数符号"""
        # 创建参数符号
        param1 = Symbol(
            id=1,
            name="userId",
            symbol_type=SymbolType.PARAMETER,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=10, offset=10),
                end=Position(line=1, column=16, offset=16)
            ),
            type_info=TypeInfo(name="string", is_primitive=True)
        )
        
        param2 = Symbol(
            id=2,
            name="options",
            symbol_type=SymbolType.PARAMETER,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=18, offset=18),
                end=Position(line=1, column=25, offset=25)
            ),
            type_info=TypeInfo(name="UserOptions", is_primitive=False)
        )
        
        # 创建函数符号
        func = Symbol(
            id=3,
            name="fetchUser",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=0, offset=0),
                end=Position(line=10, column=0, offset=100)
            ),
            return_type=TypeInfo(
                name="Promise",
                is_primitive=False,
                generic_params=["User"]
            ),
            parameters=[param1, param2],
            is_async=True,
            visibility=Visibility.PUBLIC
        )
        
        return func
    
    @pytest.fixture
    def sample_component_symbol(self):
        """创建示例 ArkUI 组件符号"""
        # 创建状态变量
        state_var = Symbol(
            id=10,
            name="username",
            symbol_type=SymbolType.PROPERTY,
            file_path="test.ets",
            range=Range(
                start=Position(line=3, column=2, offset=30),
                end=Position(line=3, column=20, offset=48)
            ),
            type_info=TypeInfo(name="string", is_primitive=True),
            decorators=["@State"]
        )
        
        # 创建生命周期方法
        lifecycle_method = Symbol(
            id=11,
            name="aboutToAppear",
            symbol_type=SymbolType.METHOD,
            file_path="test.ets",
            range=Range(
                start=Position(line=5, column=2, offset=50),
                end=Position(line=7, column=2, offset=70)
            )
        )
        
        # 创建组件符号
        component = Symbol(
            id=12,
            name="UserCard",
            symbol_type=SymbolType.COMPONENT,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=0, offset=0),
                end=Position(line=20, column=0, offset=200)
            ),
            component_type="Entry",
            decorators=["@Entry", "@Component"],
            members=[state_var, lifecycle_method],
            event_handlers={"onClick": "handleClick"},
            resource_refs=["$r('app.string.title')"],
            visibility=Visibility.PUBLIC
        )
        
        return component
    
    def test_calculate_dependencies_function(self, builder, sample_function_symbol):
        """测试函数依赖关系计算"""
        dependencies = builder.calculate_dependencies(sample_function_symbol)
        
        # 应该包含参数类型和返回类型
        assert "UserOptions" in dependencies
        assert "Promise" in dependencies
        assert "User" in dependencies
        
        # 不应该包含 primitive 类型
        assert "string" not in dependencies
        
        # 应该是排序后的列表
        assert dependencies == sorted(dependencies)
    
    def test_calculate_dependencies_component(self, builder, sample_component_symbol):
        """测试组件依赖关系计算"""
        dependencies = builder.calculate_dependencies(sample_component_symbol)
        
        # 应该包含资源引用
        assert "$r('app.string.title')" in dependencies
        
        # 应该是排序后的列表
        assert dependencies == sorted(dependencies)
    
    def test_calculate_dependencies_with_generics(self, builder):
        """测试带泛型参数的依赖计算"""
        symbol = Symbol(
            id=20,
            name="processData",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=0, offset=0),
                end=Position(line=5, column=0, offset=50)
            ),
            return_type=TypeInfo(
                name="Map",
                is_primitive=False,
                generic_params=["string", "UserData"]
            )
        )
        
        dependencies = builder.calculate_dependencies(symbol)
        
        # 应该包含泛型参数中的非 primitive 类型
        assert "UserData" in dependencies
        assert "Map" in dependencies
        
        # 不应该包含 primitive 类型的泛型参数
        assert "string" not in dependencies
    
    def test_extract_tags_general(self, builder, sample_function_symbol):
        """测试通用标签提取（5 个维度）"""
        tags = builder.extract_tags(sample_function_symbol)
        
        # 维度 1: 符号属性标签
        assert "async" in tags
        
        # 维度 2: 可见性标签
        assert "public" in tags
        
        # 维度 3: 符号类型标签
        assert "function" in tags
        
        # 维度 4: 函数纯度标签
        assert "has-side-effects" in tags or "pure-function" in tags
    
    def test_extract_tags_arkui(self, builder, sample_component_symbol):
        """测试 ArkUI 标签提取"""
        tags = builder.extract_tags(sample_component_symbol)
        
        # 维度 3: ArkUI 组件标签
        assert "ui-component" in tags
        assert "entry" in tags
        
        # 维度 5: ArkUI 特有标签
        assert "has-state" in tags
        assert "event-handler" in tags
        
        # 维度 2: 可见性
        assert "public" in tags
    
    def test_extract_tags_lifecycle(self, builder):
        """测试生命周期方法标签"""
        symbol = Symbol(
            id=30,
            name="aboutToAppear",
            symbol_type=SymbolType.METHOD,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=0, offset=0),
                end=Position(line=3, column=0, offset=30)
            )
        )
        
        tags = builder.extract_tags(symbol)
        
        # 应该包含生命周期标签
        assert "lifecycle" in tags
    
    def test_extract_decorators(self, builder, sample_component_symbol):
        """测试装饰器提取"""
        decorators = builder.extract_decorators(sample_component_symbol)
        
        # 应该包含标准装饰器
        assert "@Entry" in decorators
        assert "@Component" in decorators
    
    def test_extract_decorators_with_arkui(self, builder):
        """测试 ArkUI 装饰器合并"""
        symbol = Symbol(
            id=40,
            name="CustomButton",
            symbol_type=SymbolType.COMPONENT,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=0, offset=0),
                end=Position(line=10, column=0, offset=100)
            ),
            decorators=["@Component"],
            arkui_decorators={"Preview": {}}
        )
        
        decorators = builder.extract_decorators(symbol)
        
        # 应该包含标准装饰器和 ArkUI 装饰器
        assert "@Component" in decorators
        assert "@Preview" in decorators
    
    def test_build_metadata_function(self, builder, sample_function_symbol):
        """测试函数元数据构建"""
        source_text = """async function fetchUser(userId: string, options: UserOptions): Promise<User> {
    return await getUserData(userId, options);
}"""
        
        metadata = builder.build_metadata(sample_function_symbol, source_text)
        
        # 验证基本字段
        assert metadata.range is not None
        assert metadata.visibility == "public"
        
        # 验证参数
        assert len(metadata.parameters) == 2
        assert metadata.parameters[0].name == "userId"
        assert metadata.parameters[1].name == "options"
        
        # 验证返回类型
        assert metadata.return_type is not None
        assert metadata.return_type.name == "Promise"
        
        # 验证依赖
        assert "UserOptions" in metadata.dependencies
        assert "Promise" in metadata.dependencies
        assert "User" in metadata.dependencies
        
        # 验证标签
        assert "async" in metadata.tags
        assert "function" in metadata.tags
    
    def test_build_metadata_component(self, builder, sample_component_symbol):
        """测试组件元数据构建"""
        source_text = """@Entry
@Component
struct UserCard {
  @State username: string = 'test';
  
  aboutToAppear() {
    console.log('Component appeared');
  }
  
  build() {
    Text(this.username).onClick(() => this.handleClick());
  }
}"""
        
        metadata = builder.build_metadata(sample_component_symbol, source_text)
        
        # 验证组件特有字段
        assert metadata.component_type == "Entry"
        
        # 验证状态变量
        assert len(metadata.state_vars) > 0
        assert metadata.state_vars[0]["name"] == "username"
        
        # 验证生命周期方法
        assert "aboutToAppear" in metadata.lifecycle_hooks
        
        # 验证标签
        assert "ui-component" in metadata.tags
        assert "entry" in metadata.tags
        assert "has-state" in metadata.tags


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
ChunkMetadataBuilder 单元测试

测试元数据构建器的各项功能。
"""

import unittest
from arkts_processor.chunk_service.metadata_builder import ChunkMetadataBuilder
from arkts_processor.models import Symbol, SymbolType, Range, Position, Visibility, TypeInfo


class TestChunkMetadataBuilder(unittest.TestCase):
    """ChunkMetadataBuilder 单元测试"""
    
    def setUp(self):
        """测试前准备"""
        self.builder = ChunkMetadataBuilder()
    
    def test_build_metadata_basic(self):
        """测试基本元数据构建"""
        symbol = Symbol(
            id=1,
            name="testFunc",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(10, 0, 100)),
            visibility=Visibility.PUBLIC,
            is_async=True
        )
        
        metadata = self.builder.build_metadata(symbol, "function testFunc() {}")
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.visibility, "public")
        self.assertIn("async", metadata.tags)
        self.assertIn("public", metadata.tags)
    
    def test_extract_decorators(self):
        """测试装饰器提取"""
        symbol = Symbol(
            id=1,
            name="MyComponent",
            symbol_type=SymbolType.COMPONENT,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(20, 0, 200)),
            decorators=["@Component", "@Entry"]
        )
        
        decorators = self.builder.extract_decorators(symbol)
        
        self.assertIn("@Component", decorators)
        self.assertIn("@Entry", decorators)
    
    def test_extract_parameters(self):
        """测试参数提取"""
        param1 = Symbol(
            id=2,
            name="x",
            symbol_type=SymbolType.PARAMETER,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(0, 1, 1)),
            type_info=TypeInfo(name="number", is_primitive=True)
        )
        
        param2 = Symbol(
            id=3,
            name="y",
            symbol_type=SymbolType.PARAMETER,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(0, 1, 1)),
            type_info=TypeInfo(name="string", is_primitive=True)
        )
        
        symbol = Symbol(
            id=1,
            name="add",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(5, 0, 50)),
            parameters=[param1, param2]
        )
        
        params = self.builder.extract_parameters(symbol)
        
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0].name, "x")
        self.assertEqual(params[0].type, "number")
        self.assertEqual(params[1].name, "y")
        self.assertEqual(params[1].type, "string")
    
    def test_extract_return_type(self):
        """测试返回类型提取"""
        symbol = Symbol(
            id=1,
            name="getValue",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(5, 0, 50)),
            return_type=TypeInfo(name="number", is_primitive=True)
        )
        
        return_type = self.builder.extract_return_type(symbol)
        
        self.assertIsNotNone(return_type)
        self.assertEqual(return_type.name, "number")
        self.assertTrue(return_type.is_primitive)
    
    def test_calculate_dependencies(self):
        """测试依赖关系计算"""
        symbol = Symbol(
            id=1,
            name="processData",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(10, 0, 100)),
            type_info=TypeInfo(name="CustomType", is_primitive=False),
            return_type=TypeInfo(name="Result", is_primitive=False),
            extends=["BaseProcessor"],
            implements=["IProcessor"]
        )
        
        dependencies = self.builder.calculate_dependencies(symbol)
        
        self.assertIn("CustomType", dependencies)
        self.assertIn("Result", dependencies)
        self.assertIn("BaseProcessor", dependencies)
        self.assertIn("IProcessor", dependencies)
    
    def test_extract_tags_function(self):
        """测试函数标签提取"""
        symbol = Symbol(
            id=1,
            name="calculate",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(5, 0, 50)),
            visibility=Visibility.PUBLIC,
            is_async=True,
            is_static=True
        )
        
        tags = self.builder._extract_tags(symbol)
        
        self.assertIn("async", tags)
        self.assertIn("static", tags)
        self.assertIn("public", tags)
        self.assertIn("function", tags)
    
    def test_extract_tags_component(self):
        """测试组件标签提取"""
        symbol = Symbol(
            id=1,
            name="LoginView",
            symbol_type=SymbolType.COMPONENT,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(20, 0, 200)),
            component_type="Entry"
        )
        
        tags = self.builder._extract_tags(symbol)
        
        self.assertIn("ui-component", tags)
        self.assertIn("entry", tags)
    
    def test_add_arkui_metadata(self):
        """测试 ArkUI 元数据添加"""
        from arkts_processor.chunk_models import ChunkMetadata, PositionRange
        
        metadata = ChunkMetadata(
            range=PositionRange(0, 20, 0, 200)
        )
        
        member1 = Symbol(
            id=2,
            name="username",
            symbol_type=SymbolType.PROPERTY,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(0, 10, 10)),
            decorators=["@State"],
            type_info=TypeInfo(name="string", is_primitive=True)
        )
        
        member2 = Symbol(
            id=3,
            name="aboutToAppear",
            symbol_type=SymbolType.METHOD,
            file_path="test.ets",
            range=Range(Position(5, 0, 50), Position(8, 0, 80))
        )
        
        symbol = Symbol(
            id=1,
            name="MyComponent",
            symbol_type=SymbolType.COMPONENT,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(20, 0, 200)),
            decorators=["@Component", "@Entry"],
            members=[member1, member2]
        )
        
        source_text = """
@Component
struct MyComponent {
  @State username: string = ''
  
  aboutToAppear() {}
  
  build() {
    Column() {
      Text(this.username).onClick(() => {})
    }
  }
}
"""
        
        self.builder._add_arkui_metadata(metadata, symbol, source_text)
        
        self.assertEqual(metadata.component_type, "Entry")
        self.assertEqual(len(metadata.state_vars), 1)
        self.assertEqual(metadata.state_vars[0]["name"], "username")
        self.assertIn("aboutToAppear", metadata.lifecycle_hooks)
        self.assertIn("onClick", metadata.event_handlers)
    
    def test_extract_state_vars(self):
        """测试状态变量提取"""
        state_member = Symbol(
            id=2,
            name="count",
            symbol_type=SymbolType.PROPERTY,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(0, 10, 10)),
            decorators=["@State"],
            type_info=TypeInfo(name="number", is_primitive=True)
        )
        
        normal_member = Symbol(
            id=3,
            name="title",
            symbol_type=SymbolType.PROPERTY,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(0, 10, 10)),
            type_info=TypeInfo(name="string", is_primitive=True)
        )
        
        symbol = Symbol(
            id=1,
            name="MyComponent",
            symbol_type=SymbolType.COMPONENT,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(10, 0, 100)),
            members=[state_member, normal_member]
        )
        
        state_vars = self.builder._extract_state_vars(symbol, "")
        
        self.assertEqual(len(state_vars), 1)
        self.assertEqual(state_vars[0]["name"], "count")
        self.assertEqual(state_vars[0]["type"], "number")
    
    def test_extract_lifecycle_hooks(self):
        """测试生命周期方法提取"""
        lifecycle_method = Symbol(
            id=2,
            name="aboutToAppear",
            symbol_type=SymbolType.METHOD,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(5, 0, 50))
        )
        
        normal_method = Symbol(
            id=3,
            name="handleClick",
            symbol_type=SymbolType.METHOD,
            file_path="test.ets",
            range=Range(Position(6, 0, 60), Position(10, 0, 100))
        )
        
        symbol = Symbol(
            id=1,
            name="MyComponent",
            symbol_type=SymbolType.COMPONENT,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(20, 0, 200)),
            members=[lifecycle_method, normal_method]
        )
        
        hooks = self.builder._extract_lifecycle_hooks(symbol)
        
        self.assertEqual(len(hooks), 1)
        self.assertEqual(hooks[0], "aboutToAppear")
    
    def test_extract_event_handlers(self):
        """测试事件处理器提取"""
        source_text = """
build() {
  Column() {
    Button('Click').onClick(() => {})
    TextInput().onChange((value) => {})
    Text('Hover').onHover((isHover) => {})
  }
}
"""
        
        handlers = self.builder._extract_event_handlers(source_text)
        
        self.assertIn("onClick", handlers)
        self.assertIn("onChange", handlers)
        self.assertIn("onHover", handlers)
    
    def test_visibility_extraction(self):
        """测试可见性提取"""
        symbol = Symbol(
            id=1,
            name="privateFunc",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(0, 0, 0), Position(5, 0, 50)),
            visibility=Visibility.PRIVATE
        )
        
        visibility = self.builder._extract_visibility(symbol)
        
        self.assertEqual(visibility, "private")
    
    def test_position_range_extraction(self):
        """测试位置范围提取"""
        symbol = Symbol(
            id=1,
            name="test",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(Position(10, 5, 100), Position(20, 10, 200))
        )
        
        position_range = self.builder._extract_position_range(symbol)
        
        self.assertEqual(position_range.start_line, 10)
        self.assertEqual(position_range.start_column, 5)
        self.assertEqual(position_range.end_line, 20)
        self.assertEqual(position_range.end_column, 10)


if __name__ == "__main__":
    unittest.main()

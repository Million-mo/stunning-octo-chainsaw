"""
ContextEnricher 增强功能单元测试

测试动态上下文控制方案中的上下文增强功能：
1. Token 预算计算
2. 分层元数据头生成
3. Chunk 增强
4. 批量增强
"""

import pytest
from src.arkts_processor.chunk_service.enricher import ContextEnricher
from src.arkts_processor.chunk_models import (
    CodeChunk, ChunkType, ChunkMetadata, PositionRange, Parameter, TypeInfo
)
from src.arkts_processor.models import (
    Symbol, SymbolType, Visibility, Position, Range, Scope, ScopeType,
    TypeInfo as ModelTypeInfo
)


class TestContextEnricher:
    """ContextEnricher 测试类"""
    
    @pytest.fixture
    def enricher(self):
        """创建 ContextEnricher 实例"""
        return ContextEnricher()
    
    @pytest.fixture
    def small_function_chunk(self):
        """创建小型函数 Chunk（< 100 tokens）"""
        metadata = ChunkMetadata(
            range=PositionRange(start_line=1, end_line=3, start_column=0, end_column=0),
            tags=["async", "public", "function"],
            return_type=TypeInfo(name="number", is_primitive=True)
        )
        
        chunk = CodeChunk(
            chunk_id="test.ets#add",
            type=ChunkType.FUNCTION,
            path="test.ets",
            name="add",
            context="MathUtils",
            source="function add(a: number, b: number): number {\n  return a + b;\n}",
            imports=["Math"],
            metadata=metadata,
            symbol_id=1
        )
        
        return chunk
    
    @pytest.fixture
    def medium_function_chunk(self):
        """创建中型函数 Chunk（100-500 tokens）"""
        # 生成足够长的代码以达到 100+ tokens
        base_code = """async function fetchUserData(userId: string): Promise<User> {
  const response = await fetch(`/api/users/${userId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch user');
  }
  const data = await response.json();
  return transformUser(data);
}"""
        
        # 每行注释大约 10 tokens，添加 20 行达到 ~200 tokens
        additional_lines = "\n  // Additional implementation details and logic here" * 20
        source = base_code + additional_lines
        
        metadata = ChunkMetadata(
            range=PositionRange(start_line=10, end_line=20, start_column=0, end_column=0),
            tags=["async", "public", "function"],
            decorators=["@deprecated"],
            return_type=TypeInfo(name="Promise", is_primitive=False)
        )
        
        chunk = CodeChunk(
            chunk_id="test.ets#fetchUserData",
            type=ChunkType.FUNCTION,
            path="test.ets",
            name="fetchUserData",
            context="UserService",
            source=source,
            imports=["User", "transformUser"],
            metadata=metadata,
            symbol_id=2
        )
        
        return chunk
    
    @pytest.fixture
    def large_class_chunk(self):
        """创建大型类 Chunk（> 500 tokens）"""
        base_code = """class UserManager {
  private users: Map<string, User> = new Map();
  
  constructor() {
    this.loadUsers();
  }
  
  public getUser(id: string): User | null {
    return this.users.get(id) || null;
  }
  
  public addUser(user: User): void {
    this.users.set(user.id, user);
  }
}"""
        
        # 每行方法大约 20 tokens，添加 60 个方法达到 ~1200 tokens
        method_template = "\n  public method{}(param: string): void {{ console.log(param); }}"
        additional_methods = "".join([method_template.format(i) for i in range(60)])
        source = base_code + additional_methods + "\n}"
        
        metadata = ChunkMetadata(
            range=PositionRange(start_line=1, end_line=100, start_column=0, end_column=0),
            tags=["class", "public"]
        )
        
        chunk = CodeChunk(
            chunk_id="test.ets#UserManager",
            type=ChunkType.CLASS,
            path="test.ets",
            name="UserManager",
            context="services",
            source=source,
            imports=["User"],
            metadata=metadata,
            symbol_id=3
        )
        
        return chunk
    
    @pytest.fixture
    def component_chunk(self):
        """创建 ArkUI 组件 Chunk"""
        metadata = ChunkMetadata(
            range=PositionRange(start_line=1, end_line=30, start_column=0, end_column=0),
            component_type="Entry",
            decorators=["@Entry", "@Component"],
            state_vars=[{"name": "username", "type": "string"}],
            lifecycle_hooks=["aboutToAppear"],
            event_handlers=["onClick"],
            tags=["ui-component", "entry", "has-state"]
        )
        
        source = """@Entry
@Component
struct UserCard {
  @State username: string = 'test';
  
  aboutToAppear() {
    console.log('appeared');
  }
  
  build() {
    Text(this.username);
  }
}"""
        
        chunk = CodeChunk(
            chunk_id="test.ets#UserCard",
            type=ChunkType.COMPONENT,
            path="test.ets",
            name="UserCard",
            context="",
            source=source,
            imports=["Text"],
            metadata=metadata,
            symbol_id=4
        )
        
        return chunk
    
    @pytest.fixture
    def sample_symbol(self):
        """创建示例符号"""
        return Symbol(
            id=1,
            name="add",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=0, offset=0),
                end=Position(line=3, column=0, offset=30)
            )
        )
    
    def test_estimate_tokens(self, enricher):
        """测试 Token 估算"""
        # 简单文本
        text1 = "function add(a, b) { return a + b; }"
        tokens1 = enricher.estimate_tokens(text1)
        
        # 应该大约是单词数 * 1.3
        word_count = len(text1.split())
        expected = int(word_count * enricher.TOKEN_ESTIMATION_MULTIPLIER)
        assert tokens1 == expected
        
        # 空文本
        assert enricher.estimate_tokens("") == 0
        assert enricher.estimate_tokens(None) == 0
    
    def test_calculate_context_budget_small(self, enricher, small_function_chunk):
        """测试小型 Chunk 的预算计算"""
        budget = enricher.calculate_context_budget(
            small_function_chunk.source,
            small_function_chunk.type
        )
        
        assert budget["detail_level"] == "high"
        assert budget["max_context_tokens"] == enricher.MAX_CONTEXT_TOKENS_HIGH
        assert budget["include_siblings"] is True
        assert budget["include_parents"] is True
    
    def test_calculate_context_budget_medium(self, enricher, medium_function_chunk):
        """测试中型 Chunk 的预算计算"""
        budget = enricher.calculate_context_budget(
            medium_function_chunk.source,
            medium_function_chunk.type
        )
        
        assert budget["detail_level"] == "medium"
        assert budget["max_context_tokens"] == enricher.MAX_CONTEXT_TOKENS_MEDIUM
        assert budget["include_siblings"] is False
        assert budget["include_parents"] is True
    
    def test_calculate_context_budget_large(self, enricher, large_class_chunk):
        """测试大型 Chunk 的预算计算"""
        budget = enricher.calculate_context_budget(
            large_class_chunk.source,
            large_class_chunk.type
        )
        
        assert budget["detail_level"] == "low"
        assert budget["max_context_tokens"] == enricher.MAX_CONTEXT_TOKENS_LOW
        assert budget["include_siblings"] is False
        assert budget["include_parents"] is False
    
    def test_calculate_context_budget_component_min_medium(self, enricher):
        """测试组件至少使用 medium 等级"""
        # 创建一个大型组件（正常会是 low）
        large_component_source = "struct LargeComponent {}" + "\n// code..." * 100
        
        budget = enricher.calculate_context_budget(
            large_component_source,
            ChunkType.COMPONENT
        )
        
        # 应该提升到 medium
        assert budget["detail_level"] == "medium"
        assert budget["enable_l4"] is True
    
    def test_format_metadata_headers_general_high(self, enricher, small_function_chunk, sample_symbol):
        """测试通用元数据头格式（high 等级）"""
        budget = {
            "detail_level": "high",
            "include_parents": True,
            "include_siblings": True
        }
        
        headers = enricher.format_metadata_headers(small_function_chunk, sample_symbol, budget)
        
        # L1 层必须包含
        assert "# file: test.ets" in headers
        assert "# function: add" in headers
        
        # L2 层应该包含
        assert "# class: MathUtils" in headers or "# module:" in headers
        assert "# tags:" in headers
        
        # L3 层应该包含
        assert "# type:" in headers
    
    def test_format_metadata_headers_general_medium(self, enricher, medium_function_chunk, sample_symbol):
        """测试通用元数据头格式（medium 等级）"""
        budget = {
            "detail_level": "medium",
            "include_parents": True,
            "include_siblings": False
        }
        
        headers = enricher.format_metadata_headers(medium_function_chunk, sample_symbol, budget)
        
        # L1 层必须包含
        assert "# file: test.ets" in headers
        assert "# function: fetchUserData" in headers
        
        # L2 层应该包含
        assert "# class: UserService" in headers or "# module:" in headers
        assert "# tags:" in headers
        
        # L3 层不应该包含装饰器（medium 不包含）
        # 注意：返回类型可能在 L2 或不包含
    
    def test_format_metadata_headers_general_low(self, enricher, large_class_chunk, sample_symbol):
        """测试通用元数据头格式（low 等级）"""
        budget = {
            "detail_level": "low",
            "include_parents": False,
            "include_siblings": False
        }
        
        headers = enricher.format_metadata_headers(large_class_chunk, sample_symbol, budget)
        
        # L1 层必须包含
        assert "# file: test.ets" in headers
        assert "# class: UserManager" in headers
        
        # L2 和 L3 层不应该包含
        assert "# imports:" not in headers
        assert "# tags:" not in headers
        assert "# decorators:" not in headers
    
    def test_format_metadata_headers_component(self, enricher, component_chunk):
        """测试组件元数据头格式（L4 层）"""
        symbol = Symbol(
            id=4,
            name="UserCard",
            symbol_type=SymbolType.COMPONENT,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=0, offset=0),
                end=Position(line=30, column=0, offset=300)
            )
        )
        
        budget = {
            "detail_level": "high",
            "enable_l4": True
        }
        
        headers = enricher.format_metadata_headers(component_chunk, symbol, budget)
        
        # L1 层
        assert "# file: test.ets" in headers
        assert "# component: UserCard" in headers
        
        # L4 层（ArkUI 特有）
        assert "# component_type: Entry" in headers
        assert "# decorators:" in headers
        assert "# state_vars:" in headers
        assert "# lifecycle_hooks:" in headers
    
    def test_enrich_chunk_function(self, enricher, small_function_chunk, sample_symbol):
        """测试函数 Chunk 增强"""
        scope_map = {}
        
        original_source = small_function_chunk.source
        enriched_chunk = enricher.enrich_chunk(small_function_chunk, sample_symbol, scope_map)
        
        # 源代码应该被增强
        assert enriched_chunk.source != original_source
        assert "# file:" in enriched_chunk.source
        assert original_source in enriched_chunk.source
        
        # 元数据头应该在源代码之前
        lines = enriched_chunk.source.split("\n")
        assert lines[0].startswith("#")
    
    def test_enrich_chunk_component(self, enricher, component_chunk):
        """测试组件 Chunk 增强"""
        symbol = Symbol(
            id=4,
            name="UserCard",
            symbol_type=SymbolType.COMPONENT,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=0, offset=0),
                end=Position(line=30, column=0, offset=300)
            )
        )
        
        scope_map = {}
        
        original_source = component_chunk.source
        enriched_chunk = enricher.enrich_chunk(component_chunk, symbol, scope_map)
        
        # 应该包含组件特有的元数据头
        assert "# component:" in enriched_chunk.source
        assert "# component_type:" in enriched_chunk.source
        assert original_source in enriched_chunk.source
    
    def test_enrich_chunks_batch(self, enricher, small_function_chunk, component_chunk):
        """测试批量增强"""
        chunks = [small_function_chunk, component_chunk]
        
        symbols = [
            Symbol(
                id=1,
                name="add",
                symbol_type=SymbolType.FUNCTION,
                file_path="test.ets",
                range=Range(
                    start=Position(line=1, column=0, offset=0),
                    end=Position(line=3, column=0, offset=30)
                )
            ),
            Symbol(
                id=4,
                name="UserCard",
                symbol_type=SymbolType.COMPONENT,
                file_path="test.ets",
                range=Range(
                    start=Position(line=1, column=0, offset=0),
                    end=Position(line=30, column=0, offset=300)
                )
            )
        ]
        
        scopes = []
        
        enriched_chunks = enricher.enrich_chunks(chunks, symbols, scopes)
        
        # 应该返回相同数量的 chunks
        assert len(enriched_chunks) == 2
        
        # 每个 chunk 都应该被增强
        for chunk in enriched_chunks:
            assert "# file:" in chunk.source
    
    def test_build_context_path(self, enricher):
        """测试上下文路径构建"""
        # 创建父级作用域和符号
        parent_symbol = Symbol(
            id=10,
            name="MathUtils",
            symbol_type=SymbolType.CLASS,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=0, offset=0),
                end=Position(line=20, column=0, offset=200)
            )
        )
        
        parent_scope = Scope(
            id=1,
            scope_type=ScopeType.CLASS,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=0, offset=0),
                end=Position(line=20, column=0, offset=200)
            ),
            symbols={"MathUtils": parent_symbol}
        )
        
        child_scope = Scope(
            id=2,
            scope_type=ScopeType.FUNCTION,
            file_path="test.ets",
            range=Range(
                start=Position(line=5, column=0, offset=50),
                end=Position(line=10, column=0, offset=100)
            ),
            parent_id=1
        )
        
        child_symbol = Symbol(
            id=11,
            name="add",
            symbol_type=SymbolType.METHOD,
            file_path="test.ets",
            range=Range(
                start=Position(line=5, column=0, offset=50),
                end=Position(line=10, column=0, offset=100)
            ),
            scope_id=2
        )
        
        scope_map = {1: parent_scope, 2: child_scope}
        
        context_path = enricher.build_context_path(child_symbol, scope_map)
        
        # 应该返回父级类名
        assert context_path == "MathUtils"
    
    def test_empty_metadata(self, enricher):
        """测试空元数据处理"""
        chunk = CodeChunk(
            chunk_id="test.ets#simple",
            type=ChunkType.FUNCTION,
            path="test.ets",
            name="simple",
            context="",
            source="function simple() {}",
            imports=[],
            metadata=None,
            symbol_id=99
        )
        
        symbol = Symbol(
            id=99,
            name="simple",
            symbol_type=SymbolType.FUNCTION,
            file_path="test.ets",
            range=Range(
                start=Position(line=1, column=0, offset=0),
                end=Position(line=1, column=20, offset=20)
            )
        )
        
        scope_map = {}
        
        enriched_chunk = enricher.enrich_chunk(chunk, symbol, scope_map)
        
        # 应该能够处理空元数据，至少包含基本字段
        assert "# file:" in enriched_chunk.source
        assert "# function:" in enriched_chunk.source


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

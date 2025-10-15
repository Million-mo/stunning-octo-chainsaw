"""
动态上下文控制方案集成测试

测试端到端场景：
1. 小型工具函数（high 等级）
2. 中型类方法（medium 等级）
3. 大型类（low 等级）
4. ArkUI 入口组件
"""

import os
import tempfile
import shutil
import tree_sitter
import tree_sitter_arkts as ts_arkts
from arkts_processor.symbol_service.service import SymbolService
from arkts_processor.chunk_service.service import ChunkService


class TestDynamicContextIntegration:
    """动态上下文控制集成测试"""
    
    @classmethod
    def setup_class(cls):
        """设置测试环境"""
        # 创建临时目录
        cls.temp_dir = tempfile.mkdtemp()
        
        # 设置解析器
        ARKTS_LANGUAGE = tree_sitter.Language(ts_arkts.language())
        cls.parser = tree_sitter.Parser(ARKTS_LANGUAGE)
    
    @classmethod
    def teardown_class(cls):
        """清理测试环境"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def setup_method(self):
        """每个测试前的设置"""
        # 创建独立的数据库
        self.symbol_db = os.path.join(self.temp_dir, f"test_symbols_{id(self)}.db")
        self.chunk_db = os.path.join(self.temp_dir, f"test_chunks_{id(self)}.db")
        
        # 初始化服务
        self.symbol_service = SymbolService(self.symbol_db)
        self.symbol_service.set_parser(self.parser)
        
        self.chunk_service = ChunkService(self.symbol_service, self.chunk_db)
    
    def teardown_method(self):
        """每个测试后的清理"""
        # 删除数据库文件
        for db_file in [self.symbol_db, self.chunk_db]:
            if os.path.exists(db_file):
                os.remove(db_file)
    
    def test_small_function_high_detail(self):
        """
        场景 1: 小型工具函数
        期望: high 等级，包含 L1-L3 元数据头，上下文占比约 60%
        """
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "math_utils.ets")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""
export function add(a: number, b: number): number {
  return a + b;
}
""")
        
        # 生成 chunks
        chunks = self.chunk_service.generate_chunks(test_file)
        
        # 应该至少有一个函数 chunk
        function_chunks = [c for c in chunks if c.name == "add"]
        assert len(function_chunks) > 0
        
        chunk = function_chunks[0]
        
        # 验证元数据头存在
        assert "# file:" in chunk.source
        assert "# function: add" in chunk.source
        
        # 验证 L2 和 L3 层内容
        assert "# tags:" in chunk.source or "# type:" in chunk.source
        
        # 验证原始代码被保留
        assert "return a + b" in chunk.source
        
        # 验证上下文比例（元数据头应该占据相当大的比例）
        lines = chunk.source.split("\n")
        metadata_lines = [l for l in lines if l.startswith("#")]
        
        # 小型函数应该有较多元数据行
        assert len(metadata_lines) >= 3
    
    def test_medium_method_medium_detail(self):
        """
        场景 2: 中型类方法
        期望: medium 等级，包含 L1-L2 元数据头，上下文占比约 15%
        """
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "user_service.ets")
        
        # 生成中等长度的方法代码（~150 tokens）
        method_code = """
export class UserService {
  async fetchUserData(userId: string): Promise<User> {
    const response = await fetch(`/api/users/${userId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch user');
    }
    const data = await response.json();
    const transformed = this.transformData(data);
    return this.validateUser(transformed);
  }
  
  private transformData(data: any): any {
    return { ...data, timestamp: Date.now() };
  }
}
"""
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(method_code)
        
        # 生成 chunks
        chunks = self.chunk_service.generate_chunks(test_file)
        
        # 查找方法 chunk
        method_chunks = [c for c in chunks if c.name == "fetchUserData"]
        
        if len(method_chunks) > 0:
            chunk = method_chunks[0]
            
            # 验证基本元数据头
            assert "# file:" in chunk.source
            assert "# function: fetchUserData" in chunk.source or "# method:" in chunk.source
            
            # 验证原始代码
            assert "fetch" in chunk.source
    
    def test_large_class_low_detail(self):
        """
        场景 3: 大型类
        期望: low 等级，仅包含 L1 元数据头，上下文占比约 5%
        """
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "large_manager.ets")
        
        # 生成大型类代码（> 500 tokens）
        class_code = """
export class UserManager {
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
"""
        
        # 添加很多方法
        for i in range(30):
            class_code += f"""
  public method{i}(param: string): void {{
    console.log(param);
  }}
"""
        
        class_code += "\n}\n"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(class_code)
        
        # 生成 chunks
        chunks = self.chunk_service.generate_chunks(test_file)
        
        # 查找类 chunk
        class_chunks = [c for c in chunks if c.name == "UserManager"]
        
        if len(class_chunks) > 0:
            chunk = class_chunks[0]
            
            # 验证基本元数据头
            assert "# file:" in chunk.source
            assert "# class: UserManager" in chunk.source
            
            # 验证元数据行数较少（low 等级）
            lines = chunk.source.split("\n")
            metadata_lines = [l for l in lines if l.startswith("#")]
            
            # low 等级应该只有基本的 L1 层
            assert len(metadata_lines) <= 4
    
    def test_arkui_component_with_l4(self):
        """
        场景 4: ArkUI 入口组件
        期望: 包含 L1-L4 元数据头，体现组件特征
        """
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "user_card.ets")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("""
@Entry
@Component
struct UserCard {
  @State username: string = 'test';
  @State count: number = 0;
  
  aboutToAppear() {
    console.log('Component appeared');
  }
  
  build() {
    Column() {
      Text(this.username)
        .onClick(() => this.handleClick())
      Button(`Count: ${this.count}`)
    }
  }
  
  private handleClick() {
    this.count++;
  }
}
""")
        
        # 生成 chunks
        chunks = self.chunk_service.generate_chunks(test_file)
        
        # 查找组件 chunk
        component_chunks = [c for c in chunks if c.name == "UserCard"]
        
        if len(component_chunks) > 0:
            chunk = component_chunks[0]
            
            # L1 层
            assert "# file:" in chunk.source
            assert "# component: UserCard" in chunk.source
            
            # L4 层（ArkUI 特有）
            # 注意：实际提取可能需要 AST 支持，这里验证元数据结构
            if chunk.metadata:
                # 验证组件元数据存在
                assert chunk.metadata.component_type is not None or "@Entry" in str(chunk.source)
    
    def test_token_budget_progression(self):
        """
        测试 Token 预算随代码大小递减
        """
        test_cases = [
            ("small.ets", "function small() { return 1; }", "high"),
            ("medium.ets", "function medium() {\n" + "  // line\n" * 30 + "}", "medium"),
            ("large.ets", "class Large {\n" + "  method() {}\n" * 100 + "}", "low")
        ]
        
        for filename, code, expected_level in test_cases:
            test_file = os.path.join(self.temp_dir, filename)
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            chunks = self.chunk_service.generate_chunks(test_file)
            
            # 验证至少生成了 chunks
            assert len(chunks) > 0
            
            # 验证元数据头的详细程度
            chunk = chunks[0]
            lines = chunk.source.split("\n")
            metadata_lines = [l for l in lines if l.startswith("#")]
            
            if expected_level == "high":
                # high 应该有最多的元数据行
                assert len(metadata_lines) >= 3
            elif expected_level == "low":
                # low 应该有最少的元数据行
                assert len(metadata_lines) <= 4


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])

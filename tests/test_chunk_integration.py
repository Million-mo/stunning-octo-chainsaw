"""
代码 Chunk 服务集成测试

测试 Chunk 生成的端到端流程。
"""

import unittest
import os
import tempfile
import shutil
from pathlib import Path

import tree_sitter
import tree_sitter_arkts as ts_arkts

from arkts_processor.symbol_service.service import SymbolService
from arkts_processor.chunk_service.service import ChunkService
from arkts_processor.chunk_models import ChunkType


class TestChunkIntegration(unittest.TestCase):
    """Chunk 服务集成测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试环境"""
        # 创建临时目录
        cls.temp_dir = tempfile.mkdtemp()
        
        # 设置解析器
        ARKTS_LANGUAGE = tree_sitter.Language(ts_arkts.language())
        cls.parser = tree_sitter.Parser(ARKTS_LANGUAGE)
        
        # 创建测试文件
        cls.test_file = os.path.join(cls.temp_dir, "test.ets")
        cls._create_test_file()
    
    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    @classmethod
    def _create_test_file(cls):
        """创建测试 ArkTS 文件"""
        content = """
/**
 * 用户服务类
 */
@Component
struct UserProfile {
  @State username: string = ''
  @State age: number = 0
  
  /**
   * 组件即将出现
   */
  aboutToAppear() {
    this.loadUserData()
  }
  
  /**
   * 加载用户数据
   */
  loadUserData() {
    console.log('Loading user data')
  }
  
  build() {
    Column() {
      Text(this.username)
        .fontSize(20)
        .onClick(() => {
          console.log('Clicked')
        })
      Text(`Age: ${this.age}`)
    }
  }
}

/**
 * 计算用户得分
 */
function calculateScore(base: number, bonus: number): number {
  return base + bonus
}

/**
 * 用户数据类
 */
class UserData {
  name: string
  score: number
  
  constructor(name: string, score: number) {
    this.name = name
    this.score = score
  }
  
  /**
   * 获取显示名称
   */
  getDisplayName(): string {
    return `User: ${this.name}`
  }
}

interface UserInfo {
  id: string
  name: string
  email: string
}
"""
        with open(cls.test_file, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def setUp(self):
        """每个测试前的设置"""
        # 创建独立的数据库
        self.symbol_db = os.path.join(self.temp_dir, f"test_symbols_{id(self)}.db")
        self.chunk_db = os.path.join(self.temp_dir, f"test_chunks_{id(self)}.db")
        
        # 初始化服务
        self.symbol_service = SymbolService(self.symbol_db)
        self.symbol_service.set_parser(self.parser)
        
        self.chunk_service = ChunkService(self.symbol_service, self.chunk_db)
    
    def tearDown(self):
        """每个测试后的清理"""
        # 删除数据库文件
        for db_file in [self.symbol_db, self.chunk_db]:
            if os.path.exists(db_file):
                os.remove(db_file)
    
    def test_generate_chunks(self):
        """测试生成 Chunk"""
        chunks = self.chunk_service.generate_chunks(self.test_file)
        
        # 验证生成了 Chunk
        self.assertGreater(len(chunks), 0, "应该生成至少一个 Chunk")
        
        # 验证 Chunk 类型
        chunk_types = {chunk.type for chunk in chunks}
        self.assertIn(ChunkType.COMPONENT, chunk_types, "应该包含组件类型")
        self.assertIn(ChunkType.FUNCTION, chunk_types, "应该包含函数类型")
        self.assertIn(ChunkType.CLASS, chunk_types, "应该包含类类型")
        
        # 验证 Chunk 属性
        for chunk in chunks:
            self.assertIsNotNone(chunk.chunk_id, "chunk_id 不应为空")
            self.assertIsNotNone(chunk.name, "name 不应为空")
            self.assertIsNotNone(chunk.source, "source 不应为空")
            self.assertEqual(chunk.path, self.test_file, "path 应匹配测试文件")
    
    def test_component_chunk(self):
        """测试 ArkUI 组件 Chunk"""
        chunks = self.chunk_service.generate_chunks(self.test_file)
        
        # 查找组件 Chunk
        component_chunks = [c for c in chunks if c.type == ChunkType.COMPONENT]
        self.assertGreater(len(component_chunks), 0, "应该有组件 Chunk")
        
        component = component_chunks[0]
        self.assertEqual(component.name, "UserProfile")
        
        # 验证元数据
        self.assertIsNotNone(component.metadata, "应该有元数据")
        self.assertIn("@Component", component.metadata.decorators)
        
        # 验证状态变量
        self.assertGreater(len(component.metadata.state_vars), 0, "应该有状态变量")
        state_names = [var['name'] for var in component.metadata.state_vars]
        self.assertIn("username", state_names)
        self.assertIn("age", state_names)
        
        # 验证生命周期方法
        self.assertIn("aboutToAppear", component.metadata.lifecycle_hooks)
        
        # 验证标签
        self.assertIn("ui-component", component.metadata.tags)
    
    def test_function_chunk(self):
        """测试函数 Chunk"""
        chunks = self.chunk_service.generate_chunks(self.test_file)
        
        # 查找函数 Chunk
        function_chunks = [c for c in chunks if c.type == ChunkType.FUNCTION and c.name == "calculateScore"]
        self.assertEqual(len(function_chunks), 1, "应该有一个 calculateScore 函数")
        
        func = function_chunks[0]
        
        # 验证元数据
        self.assertIsNotNone(func.metadata)
        self.assertEqual(len(func.metadata.parameters), 2, "应该有2个参数")
        
        param_names = [p.name for p in func.metadata.parameters]
        self.assertIn("base", param_names)
        self.assertIn("bonus", param_names)
        
        # 验证返回类型
        self.assertIsNotNone(func.metadata.return_type)
        self.assertEqual(func.metadata.return_type.name, "number")
    
    def test_class_chunk(self):
        """测试类 Chunk"""
        chunks = self.chunk_service.generate_chunks(self.test_file)
        
        # 查找类 Chunk
        class_chunks = [c for c in chunks if c.type == ChunkType.CLASS]
        self.assertGreater(len(class_chunks), 0, "应该有类 Chunk")
        
        user_data_class = next((c for c in class_chunks if c.name == "UserData"), None)
        self.assertIsNotNone(user_data_class, "应该有 UserData 类")
        
        # 验证元数据
        self.assertIsNotNone(user_data_class.metadata)
    
    def test_context_enrichment(self):
        """测试上下文增强"""
        chunks = self.chunk_service.generate_chunks(self.test_file)
        
        # 检查增强后的源代码
        for chunk in chunks:
            enriched_source = chunk.get_enriched_source()
            
            # 验证包含元数据头
            self.assertIn("# file:", enriched_source, "应该包含文件路径头")
            
            if chunk.type == ChunkType.COMPONENT:
                self.assertIn("# component:", enriched_source, "组件应该有 component 头")
            elif chunk.type == ChunkType.FUNCTION:
                self.assertIn("# function:", enriched_source, "函数应该有 function 头")
            elif chunk.type == ChunkType.CLASS:
                self.assertIn("# class:", enriched_source, "类应该有 class 头")
    
    def test_chunk_persistence(self):
        """测试 Chunk 持久化"""
        # 生成并保存 Chunk
        chunks = self.chunk_service.generate_chunks(self.test_file, save_to_db=True)
        chunk_count = len(chunks)
        
        # 从数据库读取
        loaded_chunks = self.chunk_service.get_chunks_by_file(self.test_file)
        
        self.assertEqual(len(loaded_chunks), chunk_count, "加载的 Chunk 数量应该相同")
        
        # 验证每个 Chunk 都能正确加载
        for chunk in chunks:
            loaded = self.chunk_service.get_chunk_by_id(chunk.chunk_id)
            self.assertIsNotNone(loaded, f"应该能加载 {chunk.chunk_id}")
            self.assertEqual(loaded.name, chunk.name)
            self.assertEqual(loaded.type, chunk.type)
    
    def test_search_chunks(self):
        """测试搜索功能"""
        self.chunk_service.generate_chunks(self.test_file, save_to_db=True)
        
        # 按名称搜索
        results = self.chunk_service.search_chunks("User")
        self.assertGreater(len(results), 0, "应该找到包含 'User' 的 Chunk")
        
        # 验证搜索结果
        names = [chunk.name for chunk in results]
        self.assertTrue(any("User" in name for name in names))
    
    def test_get_related_chunks(self):
        """测试获取相关 Chunk"""
        chunks = self.chunk_service.generate_chunks(self.test_file, save_to_db=True)
        
        if chunks:
            # 获取第一个 Chunk 的相关 Chunk
            related = self.chunk_service.get_related_chunks(chunks[0].chunk_id)
            
            # 相关 Chunk 应该是列表（可能为空）
            self.assertIsInstance(related, list)
    
    def test_refresh_file(self):
        """测试刷新文件"""
        # 第一次生成
        chunks1 = self.chunk_service.generate_chunks(self.test_file, save_to_db=True)
        count1 = len(chunks1)
        
        # 刷新
        chunks2 = self.chunk_service.refresh_file(self.test_file)
        count2 = len(chunks2)
        
        # 数量应该相同
        self.assertEqual(count1, count2, "刷新后 Chunk 数量应该相同")
        
        # 验证没有重复
        loaded = self.chunk_service.get_chunks_by_file(self.test_file)
        self.assertEqual(len(loaded), count2, "数据库中不应有重复")
    
    def test_statistics(self):
        """测试统计功能"""
        self.chunk_service.generate_chunks(self.test_file, save_to_db=True)
        
        # 获取统计信息
        stats = self.chunk_service.get_statistics()
        
        self.assertIn("total_chunks", stats)
        self.assertIn("by_type", stats)
        self.assertGreater(stats["total_chunks"], 0)
        
        # 验证按类型统计
        type_stats = stats["by_type"]
        self.assertIsInstance(type_stats, dict)
    
    def test_export_json(self):
        """测试导出 JSON"""
        self.chunk_service.generate_chunks(self.test_file, save_to_db=True)
        
        # 导出
        output_file = os.path.join(self.temp_dir, "chunks.json")
        self.chunk_service.export_chunks_to_json(self.test_file, output_file)
        
        # 验证文件存在
        self.assertTrue(os.path.exists(output_file), "应该创建导出文件")
        
        # 验证文件内容
        import json
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        
        # 验证结构
        first = data[0]
        self.assertIn("chunk_id", first)
        self.assertIn("type", first)
        self.assertIn("name", first)
        self.assertIn("source", first)
    
    def test_embedable_texts(self):
        """测试获取可嵌入文本"""
        self.chunk_service.generate_chunks(self.test_file, save_to_db=True)
        
        # 获取可嵌入文本
        embedable = self.chunk_service.get_embedable_texts(self.test_file)
        
        self.assertGreater(len(embedable), 0, "应该有可嵌入文本")
        
        # 验证结构
        for item in embedable:
            self.assertIn("chunk_id", item)
            self.assertIn("text", item)
            self.assertIn("metadata", item)
            
            # 验证文本包含元数据头
            self.assertIn("# file:", item["text"])


def run_tests():
    """运行所有测试"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    run_tests()

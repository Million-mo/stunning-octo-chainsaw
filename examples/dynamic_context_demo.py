"""
动态上下文控制方案演示

展示如何使用动态上下文控制功能增强代码 Chunk。
"""

import os
import tempfile
import tree_sitter
import tree_sitter_arkts as ts_arkts
from arkts_processor.symbol_service.service import SymbolService
from arkts_processor.chunk_service.service import ChunkService


def main():
    """主函数"""
    # 创建临时目录和数据库
    temp_dir = tempfile.mkdtemp()
    symbol_db = os.path.join(temp_dir, "symbols.db")
    chunk_db = os.path.join(temp_dir, "chunks.db")
    
    # 设置解析器
    ARKTS_LANGUAGE = tree_sitter.Language(ts_arkts.language())
    parser = tree_sitter.Parser(ARKTS_LANGUAGE)
    
    # 初始化服务
    symbol_service = SymbolService(symbol_db)
    symbol_service.set_parser(parser)
    chunk_service = ChunkService(symbol_service, chunk_db)
    
    # 创建测试文件
    test_cases = [
        ("small_function.ets", """
// 小型工具函数 - 期望 high 等级元数据
export function add(a: number, b: number): number {
  return a + b;
}
"""),
        ("medium_service.ets", """
// 中型服务类 - 期望 medium 等级元数据
export class DataService {
  private cache: Map<string, any> = new Map();
  
  async fetchData(id: string): Promise<any> {
    if (this.cache.has(id)) {
      return this.cache.get(id);
    }
    const data = await this.loadFromServer(id);
    this.cache.set(id, data);
    return data;
  }
  
  private async loadFromServer(id: string): Promise<any> {
    return fetch(`/api/data/${id}`).then(r => r.json());
  }
}
"""),
        ("arkui_component.ets", """
// ArkUI 组件 - 期望包含 L4 层元数据
@Entry
@Component
struct UserProfile {
  @State username: string = 'Guest';
  @State score: number = 0;
  
  aboutToAppear() {
    this.loadUserData();
  }
  
  build() {
    Column() {
      Text(this.username).fontSize(24)
      Text(`Score: ${this.score}`)
        .onClick(() => this.incrementScore())
    }
  }
  
  private incrementScore() {
    this.score++;
  }
  
  private loadUserData() {
    console.log('Loading user data...');
  }
}
""")
    ]
    
    print("=" * 80)
    print("动态上下文控制方案演示")
    print("=" * 80)
    print()
    
    for filename, code in test_cases:
        # 创建测试文件
        test_file = os.path.join(temp_dir, filename)
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # 生成 Chunks
        print(f"📄 文件: {filename}")
        print("-" * 80)
        
        chunks = chunk_service.generate_chunks(test_file)
        
        for i, chunk in enumerate(chunks):
            print(f"\n🔹 Chunk {i+1}: {chunk.name} ({chunk.type.value})")
            print(f"   ID: {chunk.chunk_id}")
            
            # 分析元数据头
            lines = chunk.source.split("\n")
            metadata_lines = [l for l in lines if l.startswith("#")]
            
            print(f"   元数据头行数: {len(metadata_lines)}")
            print(f"   总行数: {len(lines)}")
            print(f"   元数据占比: {len(metadata_lines) / len(lines) * 100:.1f}%")
            
            # 显示元数据头
            if metadata_lines:
                print(f"\n   📋 元数据头:")
                for line in metadata_lines:
                    print(f"      {line}")
            
            # 显示标签
            if chunk.metadata and chunk.metadata.tags:
                print(f"\n   🏷️  标签: {', '.join(chunk.metadata.tags)}")
            
            # 显示依赖
            if chunk.metadata and chunk.metadata.dependencies:
                print(f"   🔗 依赖: {', '.join(chunk.metadata.dependencies)}")
            
            # 对于组件，显示特殊信息
            if chunk.metadata and chunk.metadata.component_type:
                print(f"\n   ⚡ 组件类型: {chunk.metadata.component_type}")
                if chunk.metadata.state_vars:
                    print(f"   📊 状态变量: {len(chunk.metadata.state_vars)} 个")
                if chunk.metadata.lifecycle_hooks:
                    print(f"   🔄 生命周期: {', '.join(chunk.metadata.lifecycle_hooks)}")
        
        print()
        print("=" * 80)
        print()
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir)
    
    print("✅ 演示完成！")
    print()
    print("关键特性:")
    print("  • 小型代码块（<100 tokens）：high 等级，包含 L1-L3 元数据头")
    print("  • 中型代码块（100-500 tokens）：medium 等级，包含 L1-L2 元数据头")
    print("  • 大型代码块（>500 tokens）：low 等级，仅包含 L1 元数据头")
    print("  • ArkUI 组件：自动包含 L4 层特化元数据（状态变量、生命周期等）")
    print()


if __name__ == "__main__":
    main()


import tree_sitter
import tree_sitter_arkts as ts_arkts
from arkts_processor.symbol_service.service import SymbolService
from arkts_processor.chunk_service.service import ChunkService

# 1. 初始化服务（使用内存数据库，测试时不生成文件）
parser = tree_sitter.Parser(tree_sitter.Language(ts_arkts.language()))
symbol_service = SymbolService(":memory:")  # 使用内存数据库
symbol_service.set_parser(parser)
chunk_service = ChunkService(symbol_service, ":memory:")  # 使用内存数据库

# 2. 处理项目中的所有 .ets 文件
from pathlib import Path

project_files = list(Path("/Users/million_mo/projects/hmos_projects/hmosworld/").rglob("*.ets"))
all_chunks = []
for file_path in project_files:
    chunks = chunk_service.generate_chunks(str(file_path))
    all_chunks.extend(chunks)
    print(f"处理了 {file_path}: {len(chunks)} 个 Chunk")

print(f"\n总计 {len(all_chunks)} 个可嵌入文本")

# 诊断：检查 chunk_id 重复情况
from collections import Counter
chunk_id_counter = Counter(c.chunk_id for c in all_chunks)
duplicates = {cid: count for cid, count in chunk_id_counter.items() if count > 1}
if duplicates:
    print(f"\n⚠️  发现 {len(duplicates)} 个重复的 chunk_id（重复 {sum(duplicates.values()) - len(duplicates)} 次）:")
    for cid, count in list(duplicates.items())[:5]:
        print(f"  - {cid}: {count} 次")
    print(f"\n说明：数据库按 chunk_id 去重，内存列表包含重复项")
    print(f"内存总数 {len(all_chunks)} - 数据库总数 {len(set(c.chunk_id for c in all_chunks))} = {len(all_chunks) - len(set(c.chunk_id for c in all_chunks))} 个重复")
else:
    print("\n✓ 没有重复的 chunk_id")

# 新增：统计信息输出（数据库 + 内存）
# 数据库统计（已保存到内存DB）
stats_db = chunk_service.get_statistics()
print("\n全局统计（数据库）:")
print(f"  总 Chunk 数: {stats_db['total_chunks']}")
print("  按类型统计:")
if isinstance(stats_db.get("by_type"), dict):
    for chunk_type, count in stats_db["by_type"].items():
        if count > 0:
            print(f"    - {chunk_type}: {count}")

# 内存自定义统计
from collections import Counter
import statistics

def summarize_chunks(chunks):
    # 按类型计数
    type_counter = Counter(c.type.value for c in chunks)
    # 行数统计（优先使用元数据范围）
    line_counts = []
    for c in chunks:
        if c.metadata and c.metadata.range:
            line_counts.append(c.metadata.range.end_line - c.metadata.range.start_line + 1)
        else:
            line_counts.append((c.source.count("\n") + 1) if c.source else 0)
    lines_stats = {}
    if line_counts:
        lines_stats = {
            "min": min(line_counts),
            "max": max(line_counts),
            "avg": round(statistics.mean(line_counts), 2),
            "median": statistics.median(line_counts),
        }
    # 标签Top
    tags_counter = Counter()
    for c in chunks:
        if c.metadata and c.metadata.tags:
            tags_counter.update(c.metadata.tags)
    # 依赖Top（imports）
    imports_counter = Counter()
    for c in chunks:
        if c.imports:
            imports_counter.update(c.imports)
    # 组件统计
    components = [c for c in chunks if c.type.value == "component"]
    with_state = sum(1 for c in components if c.metadata and c.metadata.state_vars)
    return {
        "by_type": dict(type_counter),
        "lines": lines_stats,
        "top_tags": tags_counter.most_common(10),
        "top_imports": imports_counter.most_common(10),
        "components": {"count": len(components), "with_state": with_state},
    }

summary = summarize_chunks(all_chunks)
print("\n自定义统计（内存）:")
print(f"  按类型: {summary['by_type']}")
if summary.get("lines"):
    ls = summary["lines"]
    print(f"  行数: min={ls['min']} max={ls['max']} avg={ls['avg']} median={ls['median']}")
if summary.get("top_tags"):
    print("  Top 标签:")
    for tag, cnt in summary["top_tags"][:5]:
        print(f"    - {tag}: {cnt}")
if summary.get("top_imports"):
    print("  Top 依赖符号:")
    for name, cnt in summary["top_imports"][:5]:
        print(f"    - {name}: {cnt}")
comp = summary.get("components", {})
print(f"  组件数: {comp.get('count', 0)}，含@State: {comp.get('with_state', 0)}")

#!/bin/bash
# 运行所有 Chunk 服务相关的测试

echo "========================================="
echo "运行 Chunk 服务测试套件"
echo "========================================="
echo ""

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
TOTAL=0
PASSED=0
FAILED=0

# 运行单元测试
echo "${YELLOW}1. ChunkExtractor 单元测试${NC}"
if python -m pytest tests/test_chunk_extractor.py -v; then
    echo -e "${GREEN}✓ ChunkExtractor 测试通过${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ ChunkExtractor 测试失败${NC}"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))
echo ""

echo "${YELLOW}2. ContextEnricher 单元测试${NC}"
if python -m pytest tests/test_context_enricher.py -v; then
    echo -e "${GREEN}✓ ContextEnricher 测试通过${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ ContextEnricher 测试失败${NC}"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))
echo ""

echo "${YELLOW}3. ChunkMetadataBuilder 单元测试${NC}"
if python -m pytest tests/test_metadata_builder.py -v; then
    echo -e "${GREEN}✓ ChunkMetadataBuilder 测试通过${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ ChunkMetadataBuilder 测试失败${NC}"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))
echo ""

echo "${YELLOW}4. Chunk 集成测试${NC}"
if python -m pytest tests/test_chunk_integration.py -v; then
    echo -e "${GREEN}✓ Chunk 集成测试通过${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ Chunk 集成测试失败${NC}"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))
echo ""

echo "${YELLOW}5. Chunk 服务验证${NC}"
if python verify_chunk_service.py; then
    echo -e "${GREEN}✓ Chunk 服务验证通过${NC}"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ Chunk 服务验证失败${NC}"
    FAILED=$((FAILED + 1))
fi
TOTAL=$((TOTAL + 1))
echo ""

# 总结
echo "========================================="
echo "测试结果总结"
echo "========================================="
echo "总计: $TOTAL"
echo -e "${GREEN}通过: $PASSED${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}失败: $FAILED${NC}"
else
    echo -e "${GREEN}失败: $FAILED${NC}"
fi
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}⚠️  有测试失败，请检查。${NC}"
    exit 1
fi

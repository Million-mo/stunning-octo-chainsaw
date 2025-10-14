from setuptools import setup, find_packages

setup(
    name="arkts-code-processor",
    version="0.1.0",
    description="ArkTS代码处理平台 - 符号表服务MVP",
    author="ArkTS Team",
    python_requires=">=3.9",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "tree-sitter>=0.20.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.12.0",
        "pygls>=1.2.0",
        "networkx>=3.2.0",
        "fastapi>=0.104.0",
        "pydantic>=2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
        ]
    },
)

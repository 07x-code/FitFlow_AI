import os


# 测试绝不能发起可能计费或访问网络的大模型调用，即使开发者
# 已经在 backend/.env 中配置了本地 DashScope 环境。
os.environ["FITFLOW_LLM_PROVIDER"] = "fake"

# 测试必须独立运行，不依赖本机是否启动 Redis 服务。
os.environ["FITFLOW_WORKING_MEMORY_BACKEND"] = "memory"


TEST_DATABASE_URL = os.environ.get(
    "FITFLOW_TEST_DATABASE_URL",
    "postgresql+asyncpg://fitflow:fitflow@127.0.0.1:5432/fitflow_test",
)
os.environ["FITFLOW_DATABASE_URL"] = TEST_DATABASE_URL
"""
示例客户端 - 通过网关调用模型
演示如何使用 LiteLLM 网关的 OpenAI 兼容接口
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 配置：只需要改网关地址和 API Key，业务代码完全不用关心底层用什么模型
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:4000")
GATEWAY_API_KEY = os.getenv("GATEWAY_API_KEY", "sk-gateway-demo-key-12345")

# 初始化客户端（和 OpenAI 完全一样的用法）
client = OpenAI(
    base_url=f"{GATEWAY_URL}/v1",
    api_key=GATEWAY_API_KEY,
)


def basic_chat():
    """基础聊天调用"""
    print("=" * 50)
    print("示例 1: 基础聊天")
    print("=" * 50)

    response = client.chat.completions.create(
        model="chat-default",   # 使用网关定义的别名，不是具体模型名
        messages=[
            {"role": "system", "content": "你是一个 helpful 的助手"},
            {"role": "user", "content": "你好，介绍一下你自己"}
        ],
        temperature=0.7,
        max_tokens=200,
    )

    print(f"模型: {response.model}")
    print(f"回复: {response.choices[0].message.content}")
    print(f"Token 用量: {response.usage}")
    print()


def stream_chat():
    """流式输出"""
    print("=" * 50)
    print("示例 2: 流式输出")
    print("=" * 50)

    stream = client.chat.completions.create(
        model="chat-default",
        messages=[
            {"role": "user", "content": "写一首关于秋天的短诗"}
        ],
        stream=True,
        max_tokens=200,
    )

    print("流式回复:", end=" ", flush=True)
    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
    print("\n")


def multi_model_compare():
    """对比不同模型的效果"""
    print("=" * 50)
    print("示例 3: 多模型对比")
    print("=" * 50)

    question = "用一句话解释什么是大语言模型"
    models = ["chat-default", "chat-pro", "chat-lite"]

    for model in models:
        print(f"\n--- {model} ---")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": question}],
                max_tokens=100,
            )
            print(f"回复: {response.choices[0].message.content}")
            print(f"耗时: 见响应头，Token: {response.usage.total_tokens}")
        except Exception as e:
            print(f"失败: {e}")
    print()


def function_calling():
    """Function Calling 演示"""
    print("=" * 50)
    print("示例 4: Function Calling")
    print("=" * 50)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "获取指定城市的天气",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称，如北京、上海"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    ]

    response = client.chat.completions.create(
        model="chat-pro",
        messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message
    if message.tool_calls:
        print(f"模型调用了工具: {message.tool_calls[0].function.name}")
        print(f"参数: {message.tool_calls[0].function.arguments}")
    else:
        print(f"直接回复: {message.content}")
    print()


def list_models():
    """列出网关可用的模型"""
    print("=" * 50)
    print("示例 5: 可用模型列表")
    print("=" * 50)

    models = client.models.list()
    for model in models.data:
        print(f"  - {model.id}")
    print()


if __name__ == "__main__":
    print("\n🚀 模型网关示例客户端")
    print(f"网关地址: {GATEWAY_URL}")
    print()

    try:
        list_models()
        basic_chat()
        stream_chat()
        multi_model_compare()
        function_calling()

        print("✅ 所有示例运行完成！")
    except Exception as e:
        print(f"\n❌ 出错了: {e}")
        print("\n💡 请确保网关已启动:")
        print("   1. 启动 Mock LLM 服务: cd deployment/mock_server && ./start_mock.sh")
        print("   2. 启动 LiteLLM 网关: ./scripts/start_gateway.sh")
        print("   3. 或者用 Docker 一键启动: ./scripts/start_gateway_docker.sh")

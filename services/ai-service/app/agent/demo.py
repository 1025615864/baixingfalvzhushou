"""
AI Legal Assistant - Demo Script

演示如何使用编译后的法律助手状态机图
"""

from .state import get_initial_state
from .graph import compile_legal_assistant_graph


def run_legal_assistant(user_query: str):
    """
    运行法律助手

    Args:
        user_query: 用户输入的法律问题

    Returns:
        dict: 包含最终回复和状态信息
    """
    graph = compile_legal_assistant_graph()

    initial_state = get_initial_state(user_query)

    result = graph.invoke(initial_state)

    return {
        "user_query": result["user_query"],
        "intent": result["intent"],
        "search_query": result.get("search_query"),
        "retrieved_docs": result.get("retrieved_docs", []),
        "final_response": result.get("final_response"),
        "error_flag": result.get("error_flag", False),
        "retry_count": result.get("retry_count", 0)
    }


if __name__ == "__main__":
    print("=" * 60)
    print("AI 法律助手 - 演示程序")
    print("=" * 60)

    test_queries = [
        "老板不发工资怎么办",
        "你好",
    ]

    for query in test_queries:
        print(f"\n用户问题: {query}")
        print("-" * 40)
        result = run_legal_assistant(query)
        print(f"识别意图: {result['intent']}")
        if result.get("search_query"):
            print(f"检索词: {result['search_query']}")
        print(f"\n最终回复:\n{result['final_response']}")
        print("=" * 60)

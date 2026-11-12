# 导入标准错误输出，用来提示 MCP 启动失败而不污染协议通道
import sys
# 导入日志降噪函数，生成精简堆栈
from denoise import remove_noise_lines
# 导入诊断入口，复用定位、建议和源码抓拍
from diagnose import build_diagnosis


# 把原始日志整理成客户端可以直接阅读的诊断报告
def build_report(raw_log: str) -> str:
    # 先准备降噪后的堆栈标题和正文
    report = "【降噪堆栈】\n" + remove_noise_lines(raw_log)
    # 用原始日志诊断，保留降噪失败时的回退信息
    result = build_diagnosis(raw_log)
    # 无法识别日志时明确提示调用方
    if result is None:
        # 保留已有堆栈并说明需要完整的报错日志
        return report + "\n\n【诊断结果】\n未找到可识别的报错信息，请提供完整的 Python Traceback。"
    # 取出出错位置，方便展示文件、行号和函数名
    location = result.location
    # 把定位和错误类型追加到报告中
    report += f"\n\n【定位】\n文件：{location.file}\n行号：{location.line}\n函数：{location.function or '(未知)'}\n错误类型：{result.error_type}"
    # 把报错原文作为错误原因，并附上修复建议
    report += f"\n\n【错误原因】\n{result.message}\n\n【修复建议】\n{result.suggestion}"
    # 把源码抓拍追加到报告中，文件不可读时明确说明
    return report + "\n\n【本地源码抓拍】\n" + (result.code_context or "无法读取本地源码，文件可能不存在、不可读或行号无效。")


# 导入失败或环境受限时，只记录 MCP 不可用，不影响独立诊断函数
try:
    # 从官方 SDK 1.x 导入轻量 MCP 服务类
    from mcp.server.fastmcp import FastMCP
    # 创建供客户端识别的服务
    mcp = FastMCP("vibe-error-doctor")

    # 将下一行函数注册成 MCP 工具
    @mcp.tool()
    # 用完整类型标注向客户端描述工具的输入和输出
    def diagnose_python_error(raw_log: str) -> str:
        # 向 MCP 客户端说明这个工具能做什么
        """诊断 Python Traceback，返回降噪堆栈、定位、错误原因、建议及本地源码。"""
        # 调用同一报告函数，保持直接调用和 MCP 调用的行为一致
        return build_report(raw_log)
# 接住 SDK 缺失以及导入、初始化时的环境异常
except Exception as error:
    # 保存失败原因，供脚本启动时提示用户
    startup_error: str | None = f"MCP 初始化失败：{error}。请运行 python -m pip install -r requirements.txt。"

    # 没有 SDK 时仍允许直接调用文本诊断函数
    def diagnose_python_error(raw_log: str) -> str:
        # 继续使用不依赖 MCP 的报告生成流程
        return build_report(raw_log)
# 初始化正常时清除失败提示
else:
    # 标记服务可以正常启动
    startup_error = None


# 在单独的入口中启动协议循环，导入模块时不会启动服务
def main() -> None:
    # 初始化失败时只输出清晰提示并以失败状态退出
    if startup_error is not None:
        # print是黑盒：作用是把初始化失败原因变成标准错误通道中的提示文字
        print(startup_error, file=sys.stderr)
        # 结束 MCP 入口，不影响 main.py 的独立运行
        raise SystemExit(1)
    # 为协议运行加上环境异常兜底
    try:
        # 使用标准输入输出协议，由 MCP 客户端负责管理进程
        mcp.run(transport="stdio")
    # 接住权限、事件循环和其他运行环境错误
    except Exception as error:
        # print是黑盒：作用是把服务启动异常变成标准错误通道中的提示文字
        print(f"MCP 运行失败：{error}；命令行诊断仍可使用 python main.py。", file=sys.stderr)
        # 让客户端知道服务没有成功运行
        raise SystemExit(1) from error


# 只在直接运行脚本时启动 MCP 服务
if __name__ == "__main__":
    # 进入服务启动流程
    main()

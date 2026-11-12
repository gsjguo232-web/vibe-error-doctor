# 导入标准库测试框架，避免新增测试依赖
import unittest
# 导入路径工具，创建临时源码文件
from pathlib import Path
# 导入临时目录工具，测试结束后自动清理源码
from tempfile import TemporaryDirectory
# 导入模拟工具，验证 SDK 缺失和受限环境
from unittest.mock import patch
# 导入动态执行工具，在独立命名空间中模拟缺失的 SDK
import runpy
# 导入内存文字缓冲区，收集独立入口的真实输出
from io import StringIO
# 导入日志降噪函数
from denoise import remove_noise_lines
# 导入正则提取和源码抓拍函数
from extract import extract_location, extract_error_summary, extract_code_context
# 导入 MCP 报告函数，检查用户最终收到的文本
from mcp_server import diagnose_python_error


# 检查降噪、正则提取和源码读取的关键行为
class DoctorTests(unittest.TestCase):
    # 检查第三方堆栈、冻结模块、空行和箭头都被过滤
    def test_noise_filter(self) -> None:
        # 准备混合第三方库、系统模块和业务代码的日志
        log = 'Traceback (most recent call last):\n  File "/lib/site-packages/lib.py", line 9, in call\n    library()\n  File "<frozen runpy>", line 2, in run\n    internal()\n\n  File "/app/main.py", line 7, in main\n    value = 1 / 0\n    ^~~~\nZeroDivisionError: division by zero'
        # 准备应当保留的完整业务堆栈
        expected = '  File "/app/main.py", line 7, in main\n    value = 1 / 0\nZeroDivisionError: division by zero'
        # 确认第三方源码一起被删除，业务代码和异常摘要保持原样
        self.assertEqual(remove_noise_lines(log), expected)

    # 检查定位选择最底层堆栈，并支持 Windows 路径
    def test_location_extraction(self) -> None:
        # 准备包含两层业务调用的标准日志
        log = '  File "/app/outer.py", line 2, in outer\n  File "C:\\project\\main.py", line 107, in demo\nKeyError: missing'
        # 提取最终出错位置
        location = extract_location(log)
        # 确认成功识别定位，供下面读取字段
        assert location is not None
        # 确认文件、行号和函数都来自最底层调用
        self.assertEqual((location.file, location.line, location.function), ("C:\\project\\main.py", 107, "demo"))
        # 确认错误摘要能被正则完整提取
        self.assertEqual(extract_error_summary(log), ("KeyError", "missing"))
        # 确认普通文字不会被误认为定位
        self.assertIsNone(extract_location("ordinary text"))
        # 确认普通文字不会被误认为错误摘要
        self.assertIsNone(extract_error_summary("ordinary text"))

    # 检查默认抓取上下三行，且文件缺失时安全返回空值
    def test_local_source_context(self) -> None:
        # 创建隔离的源码目录
        with TemporaryDirectory() as directory:
            # 准备九行源码路径
            source = Path(directory) / "sample.py"
            # 写入九行可直接核对的源码
            source.write_text("a\nb\nc\nd\ne\nf\ng\nh\ni\n", encoding="utf-8")
            # str是黑盒：作用是把路径对象变成源码抓拍需要的路径文字
            context = extract_code_context(str(source), 5)
            # 确认第五行被标记，且仅包含第二到第八行
            self.assertEqual(context, "     2 | b\n     3 | c\n     4 | d\n>    5 | e\n     6 | f\n     7 | g\n     8 | h")
            # 删除测试文件，模拟日志指向不存在的源码
            source.unlink()
            # str是黑盒：作用是把已删除的路径变成文字，检查缺失文件返回空值
            self.assertIsNone(extract_code_context(str(source), 5))


# 检查 MCP 工具返回报告以及 SDK 不可用时的降级行为
class MCPReportTests(unittest.TestCase):
    # 检查工具返回完整报告，且源码缺失不妨碍其他诊断字段
    def test_tool_report(self) -> None:
        # 创建隔离的业务源码目录
        with TemporaryDirectory() as directory:
            # 准备临时业务源码路径
            source = Path(directory) / "sample.py"
            # 写入一个会除零的源码行
            source.write_text("value = 1 / 0\n", encoding="utf-8")
            # 准备同时含第三方和业务堆栈的日志
            log = f'Traceback (most recent call last):\n  File "/lib/site-packages/lib.py", line 2, in call\n    library()\n  File "{source}", line 1, in demo\nZeroDivisionError: division by zero'
            # 调用对外工具函数生成报告
            report = diagnose_python_error(log)
            # 确认所有要求的报告栏目和真实源码均存在
            for text in ("【降噪堆栈】", "【定位】", "函数：demo", "ZeroDivisionError", "【错误原因】\ndivision by zero", "【修复建议】", "【本地源码抓拍】\n>    1 | value = 1 / 0"):
                # 检查当前栏目或字段已经写入报告
                self.assertIn(text, report)
            # 确认报告里没有第三方堆栈
            self.assertNotIn("site-packages", report)
            # 删除源码以验证工具报告的降级显示
            source.unlink()
            # 确认文件缺失时有明确提示
            self.assertIn("无法读取本地源码", diagnose_python_error(log))

    # 检查无效日志会给出可操作的提示
    def test_unrecognized_log(self) -> None:
        # 确认工具不会为普通文字编造诊断
        self.assertIn("未找到可识别的报错信息", diagnose_python_error("hello"))

    # 检查 SDK 缺失时报告仍可调用，且命令行入口不依赖 MCP
    def test_missing_mcp(self) -> None:
        # 让独立执行的模块看不到 MCP SDK
        with patch.dict("sys.modules", {"mcp": None, "mcp.server.fastmcp": None}):
            # 加载 MCP 模块而不启动服务
            namespace = runpy.run_path("mcp_server.py")
            # 确认记录了初始化失败原因
            self.assertIsNotNone(namespace["startup_error"])
            # 确认没有 SDK 时仍能直接调用报告函数
            self.assertIn("未找到可识别的报错信息", namespace["diagnose_python_error"]("hello"))
            # 收集 SDK 缺失时命令行演示的完整输出
            with patch("sys.stdout", new_callable=StringIO) as output:
                # 真正执行独立入口，确认真实异常演示不依赖 MCP
                runpy.run_path("main.py", run_name="__main__")
                # 确认演示仍能打印第 107 行源码
                self.assertIn('>  107 |         print(fake_user["age"])', output.getvalue())

    # 检查协议运行受限时明确退出，不吞掉启动失败
    def test_restricted_runtime(self) -> None:
        # 导入服务模块以替换协议循环
        import mcp_server
        # 模拟 SDK 已正确初始化
        with patch.object(mcp_server, "startup_error", None):
            # 替换服务对象，即使 SDK 未安装也能独立验证失败分支
            with patch.object(mcp_server, "mcp", create=True) as server:
                # 让模拟服务的运行方法拒绝启动
                server.run.side_effect = RuntimeError("blocked")
                # 收集错误提示，避免干扰测试输出
                with patch("sys.stderr"):
                    # 确认受限环境会向客户端返回失败状态
                    with self.assertRaises(SystemExit) as caught:
                        # 进入服务启动流程
                        mcp_server.main()
                    # 确认退出码为失败
                    self.assertEqual(caught.exception.code, 1)


# 允许直接运行此测试脚本
if __name__ == "__main__":
    # 启动标准库测试运行器
    unittest.main()

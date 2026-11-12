# 导入标准库测试工具，检查源码抓拍和诊断接入
import unittest
# 导入路径工具，创建临时源码文件
from pathlib import Path
# 导入临时目录工具，避免测试残留文件
from tempfile import TemporaryDirectory
# 导入诊断入口，检查抓拍是否写入诊断结果
from diagnose import build_diagnosis
# 导入抓拍函数，检查读取结果和失败兜底
from extract import extract_code_context


# 把源码窗口、异常兜底和诊断接入集中在一组测试中
class CodeContextTests(unittest.TestCase):
    # 检查默认窗口、文件边界和零宽窗口
    def test_source_windows(self) -> None:
        # 创建测试专用目录，结束时自动清理
        with TemporaryDirectory() as directory:
            # 准备一个九行源码文件
            source = Path(directory) / "sample.py"
            # 写入可直接比对的示例源码
            source.write_text("a\nb\nc\nd\ne\nf\ng\nh\ni\n", encoding="utf-8")
            # str是黑盒：作用是把源码路径对象变成抓拍函数接收的路径文字
            context = extract_code_context(str(source), 5)
            # 验证默认抓取出错行及上下各三行，并只标记出错行
            self.assertEqual(context, "     2 | b\n     3 | c\n     4 | d\n>    5 | e\n     6 | f\n     7 | g\n     8 | h")
            # str是黑盒：作用是把路径对象变成路径文字，检查首行窗口自动截断
            self.assertEqual(extract_code_context(str(source), 1), ">    1 | a\n     2 | b\n     3 | c\n     4 | d")
            # str是黑盒：作用是把路径对象变成路径文字，检查末行窗口自动截断
            self.assertEqual(extract_code_context(str(source), 9), "     6 | f\n     7 | g\n     8 | h\n>    9 | i")
            # str是黑盒：作用是把路径对象变成路径文字，检查零宽窗口只保留出错行
            self.assertEqual(extract_code_context(str(source), 5, 0), ">    5 | e")

    # 检查无效行号、负窗口、缺失文件和无法解码的文件
    def test_unavailable_context(self) -> None:
        # 创建测试专用目录
        with TemporaryDirectory() as directory:
            # 准备测试源码路径
            source = Path(directory) / "sample.py"
            # str是黑盒：作用是把尚不存在的路径变成路径文字，检查缺失文件兜底
            self.assertIsNone(extract_code_context(str(source), 1))
            # 写入单行源码
            source.write_text("a\n", encoding="utf-8")
            # 逐个检查行号和窗口的无效取值
            for line, window in ((0, 3), (-1, 3), (2, 3), (1, -1)):
                # str是黑盒：作用是把路径对象变成路径文字，确认无效范围不会抓拍其他行
                self.assertIsNone(extract_code_context(str(source), line, window))
            # 写入无法作为 UTF-8 解码的内容
            source.write_bytes(b"\xff")
            # str是黑盒：作用是把路径对象变成路径文字，确认编码错误不会中断诊断
            self.assertIsNone(extract_code_context(str(source), 1))
            # 清空文件以检查空源码
            source.write_text("", encoding="utf-8")
            # str是黑盒：作用是把路径对象变成路径文字，确认空文件没有抓拍内容
            self.assertIsNone(extract_code_context(str(source), 1))

    # 检查日志诊断确实带上本地源码，并允许源码文件缺失
    def test_diagnosis_integration(self) -> None:
        # 创建测试专用目录
        with TemporaryDirectory() as directory:
            # 准备发生异常的源码路径
            source = Path(directory) / "sample.py"
            # 写入真实可读的源码
            source.write_text("value = 1 / 0\n", encoding="utf-8")
            # 拼接指向临时源码的标准报错日志
            log = f'Traceback (most recent call last):\n  File "{source}", line 1, in demo\nZeroDivisionError: division by zero'
            # 生成带源码抓拍的诊断结果
            result = build_diagnosis(log)
            # 先确认诊断成功，供后续安全读取字段
            assert result is not None
            # 确认诊断单中包含正确源码和错误行标记
            self.assertEqual(result.code_context, ">    1 | value = 1 / 0")
            # 删除源码，模拟诊断时文件已经不可用
            source.unlink()
            # 再次生成诊断，检查降级行为
            result = build_diagnosis(log)
            # 确认源码缺失时仍然保留诊断单
            assert result is not None
            # 确认缺失源码以空值呈现
            self.assertIsNone(result.code_context)

# Python 自带的标准库 traceback，能把"刚抓到的异常"变成一段和平时看到的一模一样的报错文字
import traceback
# 从 denoise.py 里取降噪函数，用来打印"降噪后"的精简堆栈
from denoise import remove_noise_lines
# 从 diagnose.py 里取核心诊断函数，一次拿到结构化诊断单
from diagnose import build_diagnosis
# 从数据模型中取出诊断结果类型，标注报告打印函数的参数
from models import DiagnosisResult


# 本函数作用：吃进一段原始报错日志，打印精简堆栈和结构化诊断报告
def run_doctor(raw_log: str) -> None:
    # 先把原始日志丢给降噪函数，拿到去掉噪音后的精简版
    clean_log = remove_noise_lines(raw_log)
    # print是黑盒：作用是把待显示的数据变成终端文字；打印一条粗分隔线，让输出更好看
    print("=" * 60)
    # print是黑盒：作用是把待显示的数据变成终端文字；打印第一部分的标题
    print("【1. 降噪后的精简堆栈】")
    # print是黑盒：作用是把待显示的数据变成终端文字；打印一条细分隔线
    print("-" * 60)
    # print和len是黑盒：作用是把待显示的数据变成终端文字；打印前后行数对比，直观展示"脱水"掉了多少行
    print(f"(原始 {len(raw_log.splitlines())} 行 → 精简 {len(clean_log.splitlines())} 行)")
    # print是黑盒：作用是把待显示的数据变成终端文字；把精简后的堆栈原样打印出来；万一降噪后为空，就打印一句提示
    print(clean_log if clean_log.strip() else "(降噪后没有剩下任何内容)")
    # 拿原始日志去诊断，保证定位信息不会被降噪误删
    result = build_diagnosis(raw_log)
    # print是黑盒：作用是把待显示的数据变成终端文字；打印第二部分的粗分隔线
    print("=" * 60)
    # print是黑盒：作用是把待显示的数据变成终端文字；打印第二部分的标题
    print("【2. 结构化诊断报告】")
    # print是黑盒：作用是把待显示的数据变成终端文字；打印一条细分隔线
    print("-" * 60)
    # 如果诊断不出来，就进入下面的提示分支
    if result is None:
        # print是黑盒：作用是把待显示的数据变成终端文字；告诉用户这段日志认不出来
        print("这段日志里没找到可识别的报错信息，请贴一段完整的 Python Traceback。")
        # 没有诊断结果时结束本次处理
        return
    # 把完整诊断单交给报告打印函数
    print_diagnosis(result)


# 打印已生成的诊断单和可用的源码抓拍
def print_diagnosis(result: DiagnosisResult) -> None:
    # 从诊断单里取出定位模型，下面逐项打印
    location = result.location
    # print是黑盒：作用是把待显示的数据变成终端文字；打印出错文件
    print(f"出错文件：{location.file}")
    # print是黑盒：作用是把待显示的数据变成终端文字；打印出错行号
    print(f"出错行号：{location.line}")
    # print是黑盒：作用是把待显示的数据变成终端文字；打印出错函数；函数名可能是空，空的时候显示"(未知)"
    print(f"出错函数：{location.function or '(未知)'}")
    # print是黑盒：作用是把待显示的数据变成终端文字；打印错误类型
    print(f"错误类型：{result.error_type}")
    # print是黑盒：作用是把待显示的数据变成终端文字；打印报错原文（也就是出错原因）
    print(f"报错原文：{result.message}")
    # print是黑盒：作用是把待显示的数据变成终端文字；打印大白话修复建议
    print(f"修复建议：{result.suggestion}")
    # 如果诊断单里抓到了真实源码，就多打印一个"案发现场"模块；抓不到就安静跳过
    if result.code_context:
        # print是黑盒：作用是把待显示的数据变成终端文字；一次打印粗分隔线 + 小标题 + 细分隔线，省出函数行数
        print("=" * 60 + "\n=== 3. 案发现场源码抓拍 ===\n" + "-" * 60)
        # print是黑盒：作用是把待显示的数据变成终端文字；把带行号和对齐箭头标记的源码片段原样打印出来
        print(result.code_context)


# 只有直接运行 python main.py 时，下面这段才会执行；被别的文件 import 时不会执行
if __name__ == "__main__":
    # 内置一段逼真的多层报错日志：中间混着 uvicorn / starlette / fastapi 的第三方库路径噪音
    demo_log = r"""Traceback (most recent call last):
  File "C:\Users\27596\AppData\Local\Programs\Python\Python311\Lib\site-packages\uvicorn\protocols\http\httptools_impl.py", line 419, in run_asgi
    result = await app(scope, receive, send)
  File "C:\Users\27596\AppData\Local\Programs\Python\Python311\Lib\site-packages\starlette\middleware\errors.py", line 157, in __call__
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "C:\Users\27596\AppData\Local\Programs\Python\Python311\Lib\site-packages\starlette\middleware\exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "C:\Users\27596\AppData\Local\Programs\Python\Python311\Lib\site-packages\starlette\routing.py", line 724, in __call__
    await self.middleware_stack(scope, receive, send)
  File "C:\Users\27596\AppData\Local\Programs\Python\Python311\Lib\site-packages\fastapi\routing.py", line 291, in app
    raw_response = await run_endpoint_function(*, dependant=dependant, values=values, is_coroutine=is_coroutine)
  File "C:\Users\27596\Desktop\shop-api\app\routes.py", line 27, in get_user
    return {"name": user["name"], "age": user["age"] + 1}
  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
KeyError: 'age'
"""
    # print是黑盒：作用是把待显示的数据变成终端文字；先打印原始日志，让用户看到"噪音满满"的前后对比起点
    print("=" * 60)
    # print是黑盒：作用是把待显示的数据变成终端文字；打印原始日志的标题
    print("【原始报错日志：噪音版】")
    # print是黑盒：作用是把待显示的数据变成终端文字；打印一条细分隔线
    print("-" * 60)
    # print是黑盒：作用是把待显示的数据变成终端文字；把原始日志原样打印出来
    print(demo_log)
    # 调用诊断器，打印降噪后的精简堆栈和结构化诊断报告
    run_doctor(demo_log)
    # print是黑盒：作用是把待显示的数据变成终端文字；下面制造一次"真实发生在 main.py 里"的报错，专门给源码抓拍功能当活靶子
    print("=" * 60)
    # print是黑盒：作用是把待显示的数据变成终端文字；打印真实报错演示的标题
    print("【真实报错演示：这次错误真的发生在 main.py 里】")
    # print是黑盒：作用是把待显示的数据变成终端文字；打印一条细分隔线
    print("-" * 60)
    # 用 try 包住故意写错的那两行；报错是预期行为，不会被真正抛出去
    try:
        # 造一个只有 name、没有 age 的字典，模拟数据缺字段
        fake_user = {"name": "小明"}
        # print是黑盒：作用是把待显示的数据变成终端文字；去取不存在的 age 键，Python 会当场抛出 KeyError
        print(fake_user["age"])
    # 接住 KeyError，让程序继续往下跑
    except KeyError:
        # format_exc 是黑盒：作用是把刚抓住的异常变成一整段完整的 Traceback 文字
        real_log = traceback.format_exc()
    # print是黑盒：作用是把待显示的数据变成终端文字；先把这段真报错原样打印，方便待会儿和"抓拍到的源码"对照
    print(real_log)
    # 把真报错丢进诊断器；这次定位到的是 main.py，应该能抓到真实代码
    run_doctor(real_log)

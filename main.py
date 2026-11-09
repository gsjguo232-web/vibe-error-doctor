# 从 denoise.py 里取降噪函数，用来打印"降噪后"的精简堆栈
from denoise import remove_noise_lines
# 从 diagnose.py 里取核心诊断函数，一次拿到结构化诊断单
from diagnose import build_diagnosis


# 本函数作用：吃进一段原始报错日志，打印精简堆栈和结构化诊断报告
def run_doctor(raw_log: str) -> None:
    # 先把原始日志丢给降噪函数，拿到去掉噪音后的精简版
    clean_log = remove_noise_lines(raw_log)
    # 打印一条粗分隔线，让输出更好看
    print("=" * 60)
    # 打印第一部分的标题
    print("【1. 降噪后的精简堆栈】")
    # 打印一条细分隔线
    print("-" * 60)
    # 打印前后行数对比，直观展示"脱水"掉了多少行
    print(f"(原始 {len(raw_log.splitlines())} 行 → 精简 {len(clean_log.splitlines())} 行)")
    # 把精简后的堆栈原样打印出来；万一降噪后为空，就打印一句提示
    print(clean_log if clean_log.strip() else "(降噪后没有剩下任何内容)")
    # 拿原始日志去诊断，保证定位信息不会被降噪误删
    result = build_diagnosis(raw_log)
    # 打印第二部分的粗分隔线
    print("=" * 60)
    # 打印第二部分的标题
    print("【2. 结构化诊断报告】")
    # 打印一条细分隔线
    print("-" * 60)
    # 如果诊断不出来，就进入下面的提示分支
    if result is None:
        # 告诉用户这段日志认不出来
        print("这段日志里没找到可识别的报错信息，请贴一段完整的 Python Traceback。")
        # return 是黑盒：作用是把函数当场结束，后面的代码不再执行
        return
    # 从诊断单里取出定位模型，下面逐项打印
    location = result.location
    # 打印出错文件
    print(f"出错文件：{location.file}")
    # 打印出错行号
    print(f"出错行号：{location.line}")
    # 打印出错函数；函数名可能是空，空的时候显示"(未知)"
    print(f"出错函数：{location.function or '(未知)'}")
    # 打印错误类型
    print(f"错误类型：{result.error_type}")
    # 打印报错原文（也就是出错原因）
    print(f"报错原文：{result.message}")
    # 打印大白话修复建议
    print(f"修复建议：{result.suggestion}")


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
    # 先打印原始日志，让用户看到"噪音满满"的前后对比起点
    print("=" * 60)
    # 打印原始日志的标题
    print("【原始报错日志：噪音版】")
    # 打印一条细分隔线
    print("-" * 60)
    # 把原始日志原样打印出来
    print(demo_log)
    # 调用诊断器，打印降噪后的精简堆栈和结构化诊断报告
    run_doctor(demo_log)

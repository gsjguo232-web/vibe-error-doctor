# 🩺 Vibe Error Doctor（Python 报错日志降噪与诊断器）

把一坨又长又乱的 Python Traceback，一键「脱水」成**你看得懂的三行**，并给出大白话级的修复建议。

> 只依赖 Python 标准库 + `pydantic`，没有多余第三方依赖，开箱即用。

---

## 😫 痛点对比

| 你平时遇到的 | 本工具给你的 |
| --- | --- |
| Traceback 里几十行 `site-packages`、`<frozen>` 噪音 | 自动过滤第三方库 / 系统内部堆栈，只留你自己的代码 |
| 手动一行行数「到底错在第几行」 | 直接输出 `出错文件 / 出错行号 / 出错函数` |
| 错误类型和原文混在一起，读起来费劲 | 拆成 `错误类型` + `报错原文` 两个独立字段 |
| 搜半天才知道怎么改 | 内置 12 种高频错误的**大白话**修复建议 |

**一句话：把「读报错」从 5 分钟压缩到 5 秒钟。**

---

## 🧩 核心模块

| 文件 | 职责 | 关键函数 |
| --- | --- | --- |
| `models.py` | 用 pydantic 定义数据结构 | `ErrorLocation`、`DiagnosisResult` |
| `denoise.py` | 日志降噪：去空行、`^ ~` 指示符、固定头部、`site-packages` / `<frozen` 堆栈 | `remove_noise_lines` |
| `extract.py` | 用正则从日志里捞出定位和错误摘要 | `extract_location`、`extract_error_summary` |
| `suggest.py` | 错误类型 → 大白话修复建议 | `suggest_fix` |
| `diagnose.py` | 串起「降噪 + 提取 + 建议」，产出诊断单 | `build_diagnosis` |
| `main.py` | 命令行 / 演示入口 | `run_doctor` |

数据流：

```
原始日志
   │  denoise.py   去噪音（空行 / 指示符 / 第三方堆栈）
   ▼
精简堆栈
   │  extract.py   捞出定位 + 错误摘要
   ▼
结构化字段（文件、行号、函数、错误类型、原文）
   │  suggest.py   查大白话修复建议
   ▼
DiagnosisResult
```

---

## 🚀 快速运行

```bash
pip install -r requirements.txt
python main.py
```

---

## ✨ 输出效果

运行 `python main.py`，会先看到噪音满满的原始日志，再看到降噪后的对比：

```text
============================================================
【原始报错日志：噪音版】
------------------------------------------------------------
Traceback (most recent call last):
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

============================================================
【1. 降噪后的精简堆栈】
------------------------------------------------------------
(原始 15 行 → 精简 3 行)
  File "C:\Users\27596\Desktop\shop-api\app\routes.py", line 27, in get_user
    return {"name": user["name"], "age": user["age"] + 1}
KeyError: 'age'
============================================================
【2. 结构化诊断报告】
------------------------------------------------------------
出错文件：C:\Users\27596\Desktop\shop-api\app\routes.py
出错行号：27
出错函数：get_user
错误类型：KeyError
报错原文：'age'
修复建议：字典里没有这个键，改用 dict.get() 或先用 in 判断
```

15 行噪音 → 3 行有效信息，出错位置和修复建议一目了然。

---

## 📚 内置的 12 种高频错误建议

| 错误类型 | 一句话排查方向 |
| --- | --- |
| `ZeroDivisionError` | 除数可能是 0，先判断再做除法 |
| `KeyError` | 字典里没有这个键，改用 `dict.get()` 或先用 `in` 判断 |
| `TypeError` | 两边类型对不上，用 `print(type(x))` 看实际类型 |
| `IndexError` | 下标越界，先用 `len()` 看列表多长 |
| `FileNotFoundError` | 文件路径不对，检查拼写和当前工作目录 |
| `AttributeError` | 属性名拼错或对象类型不对 |
| `ValueError` | 传入的值本身不合法，先 `print` 出原值 |
| `ImportError` | `from ... import ...` 里的名字拼错 |
| `ModuleNotFoundError` | 模块没装或包名拼错，先 `pip install` |
| `JSONDecodeError` | 响应不是合法 JSON，打印原文看看 |
| `ValidationError` | pydantic 字段名 / 类型 / 必填项不对 |
| `TimeoutError` | 加 `timeout` 并重试，检查网络或服务端 |

> 带模块前缀的错误名（如 `json.decoder.JSONDecodeError`、`pydantic_core._pydantic_core.ValidationError`）也能自动识别到短名并命中建议。

---

## 📁 项目结构

```text
vibe-error-doctor/
├── models.py          # 数据结构（pydantic 模型）
├── denoise.py         # 日志降噪
├── extract.py         # 正则提取定位与错误摘要
├── suggest.py         # 错误类型 → 修复建议
├── diagnose.py        # 组装诊断单
├── main.py            # 命令行 / 演示入口
├── requirements.txt   # 依赖（pydantic>=2.0.0）
├── .gitignore         # 忽略缓存、虚拟环境、密钥等
└── README.md
```

---

## ❓ 小提示

- 如果在 Windows 旧版 `cmd` 里看到中文乱码，先执行 `chcp 65001` 切到 UTF-8，再运行 `python main.py`。
- 想接入自己的日志：直接调用 `run_doctor(你的日志字符串)`，或只取降噪结果 `remove_noise_lines(...)`。

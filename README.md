# 🩺 Vibe Error Doctor v1.0（Python 报错日志降噪与 MCP 诊断工具）

把一坨又长又乱的 Python Traceback，一键「脱水」成**你看得懂的三行**，并给出大白话级的修复建议。

> 业务代码只使用 Python 标准库、`pydantic` 和 `mcp`。命令行诊断可独立运行，MCP 服务可接入 Cursor、Claude 和 Codex。

---

## 😫 痛点对比

| 你平时遇到的 | 本工具给你的 |
| --- | --- |
| Traceback 里几十行 `site-packages`、`<frozen>` 噪音 | 自动过滤第三方库 / 系统内部堆栈，只留你自己的代码 |
| 手动一行行数「到底错在第几行」 | 直接输出 `出错文件 / 出错行号 / 出错函数` |
| 错误类型和原文混在一起，读起来费劲 | 拆成 `错误类型` + `报错原文` 两个独立字段 |
| 搜半天才知道怎么改 | 内置 12 种高频错误的**大白话**修复建议 |
| 报错行附近的代码还得自己翻 | 自动抓取本地报错行及上下各 3 行源码，用 `>` 标记错误行 |

**一句话：把「读报错」从 5 分钟压缩到 5 秒钟。**

---

## 🧩 核心模块

| 文件 | 职责 | 关键函数 |
| --- | --- | --- |
| `models.py` | 用 pydantic 定义数据结构 | `ErrorLocation`、`DiagnosisResult` |
| `denoise.py` | 日志降噪：去空行、`^ ~` 指示符、固定头部、`site-packages` / `<frozen` 堆栈 | `remove_noise_lines` |
| `extract.py` | 提取定位、错误摘要和本地源码 | `extract_location`、`extract_error_summary`、`extract_code_context` |
| `suggest.py` | 错误类型 → 大白话修复建议 | `suggest_fix` |
| `diagnose.py` | 串起「降噪 + 提取 + 建议」，产出诊断单 | `build_diagnosis` |
| `main.py` | 命令行 / 演示入口 | `run_doctor` |
| `mcp_server.py` | 通过 stdio 提供 MCP 文本诊断工具 | `diagnose_python_error` |
| `test_doctor.py` | 降噪、定位、源码抓拍、MCP 报告与异常兜底测试 | 标准库 `unittest` |
| `test_code_context.py` | 源码窗口、边界和诊断接入回归测试 | 标准库 `unittest` |

数据流：

```
原始日志
   │  denoise.py   去噪音（空行 / 指示符 / 第三方堆栈）
   ▼
精简堆栈
   │  extract.py   捞出定位 + 错误摘要 + 本地源码
   ▼
结构化字段（文件、行号、函数、错误类型、原文、code_context）
   │  suggest.py   查大白话修复建议
   ▼
DiagnosisResult
```

---

## 🚀 快速运行

```bash
pip install -r requirements.txt
python main.py
python -m unittest -v
```

要求 Python 3.10+。依赖使用 `mcp>=1.0.0,<2`：官方 SDK 2.x 已移除本项目指定的 `mcp.server.fastmcp.FastMCP` 路径，详见 [SDK 迁移说明](https://github.com/modelcontextprotocol/python-sdk/blob/v2.3.0/docs/migration.md#fastmcp-renamed-to-mcpserver)。仅使用命令行时可只安装 `pydantic>=2.0.0`；`main.py` 不导入 MCP。MCP 导入或初始化失败时仍可直接调用文本报告函数，启动服务则会向标准错误输出提示并返回非零退出码。

## 真实输出效果演示

下面直接摘录本仓库运行 `python main.py` 的真实终端输出，包含第 107 行及上下各 3 行源码。路径和行号会随本地位置及后续代码变更而变化。

```text
============================================================
【真实报错演示：这次错误真的发生在 main.py 里】
------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Users\27596\Desktop\vibe-error-doctor\main.py", line 107, in <module>
    print(fake_user["age"])
          ~~~~~~~~~^^^^^^^
KeyError: 'age'

============================================================
【1. 降噪后的精简堆栈】
------------------------------------------------------------
(原始 5 行 → 精简 3 行)
  File "C:\Users\27596\Desktop\vibe-error-doctor\main.py", line 107, in <module>
    print(fake_user["age"])
KeyError: 'age'
============================================================
【2. 结构化诊断报告】
------------------------------------------------------------
出错文件：C:\Users\27596\Desktop\vibe-error-doctor\main.py
出错行号：107
出错函数：<module>
错误类型：KeyError
报错原文：'age'
修复建议：字典里没有这个键，改用 dict.get() 或先用 in 判断
============================================================
=== 3. 案发现场源码抓拍 ===
------------------------------------------------------------
   104 |         # 造一个只有 name、没有 age 的字典，模拟数据缺字段
   105 |         fake_user = {"name": "小明"}
   106 |         # print是黑盒：作用是把待显示的数据变成终端文字；去取不存在的 age 键，Python 会当场抛出 KeyError
>  107 |         print(fake_user["age"])
   108 |     # 接住 KeyError，让程序继续往下跑
   109 |     except KeyError:
   110 |         # format_exc 是黑盒：作用是把刚抓住的异常变成一整段完整的 Traceback 文字
```

## 接入 Cursor / Claude / Codex (MCP)

先在将用于启动服务的 Python 环境中安装 `requirements.txt`。服务名为 `vibe-error-doctor`，工具名为 `diagnose_python_error`，输入参数为 `raw_log`（完整 Python Traceback 字符串）。报告返回降噪堆栈、定位、错误原因、修复建议和本地源码；读不到源码时仍保留其他诊断信息。

Cursor 项目配置写入 `.cursor/mcp.json`；Claude Code 项目配置写入根目录 `.mcp.json`；Claude Desktop 可将同一 JSON 合并到 `claude_desktop_config.json` 的 `mcpServers` 中。下面是本机路径示例，请把 `command` 换成已安装依赖的 Python 解释器绝对路径，把 `args` 换成你的仓库绝对路径，Windows 路径可使用 `/`。

```json
{
  "mcpServers": {
    "vibe-error-doctor": {
      "command": "C:/Users/27596/miniconda3/python.exe",
      "args": ["C:/Users/27596/Desktop/vibe-error-doctor/mcp_server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8"
      }
    }
  }
}
```

配置格式见 [Cursor 官方文档](https://cursor.com/docs/mcp)、[Claude Code 官方文档](https://code.claude.com/docs/en/mcp) 和 [MCP 官方服务端教程（Claude Desktop）](https://modelcontextprotocol.io/docs/develop/build-server)。配置后在客户端启用服务并确认能看到 `diagnose_python_error`。

**Codex 使用 TOML 配置**，不能直接粘贴上面的 JSON。将下面内容合并到 `~/.codex/config.toml`（项目级配置可写入受信任项目的 `.codex/config.toml`）：

```toml
[mcp_servers.vibe-error-doctor]
command = "C:/Users/27596/miniconda3/python.exe"
args = ["C:/Users/27596/Desktop/vibe-error-doctor/mcp_server.py"]

[mcp_servers.vibe-error-doctor.env]
PYTHONIOENCODING = "utf-8"
```

也可以让 Codex CLI 写入配置：

```bash
codex mcp add vibe-error-doctor --env PYTHONIOENCODING=utf-8 -- C:/Users/27596/miniconda3/python.exe C:/Users/27596/Desktop/vibe-error-doctor/mcp_server.py
```

格式见 [OpenAI 官方 MCP 文档](https://developers.openai.com/codex/mcp/)。

服务只读取日志指向的本机文件，不会执行日志中的代码。源码路径应使用绝对路径；相对路径按服务进程的工作目录解析。MCP 客户端须能访问这些文件；服务返回的源码会进入客户端上下文。`python mcp_server.py` 使用 stdio 等待客户端协议消息，不会像 `main.py` 一样打印演示；普通报告作为工具返回值发送，标准输出专用于 MCP 协议。

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
├── mcp_server.py      # MCP 服务与文本诊断工具
├── test_doctor.py     # 降噪、定位、源码抓拍及 MCP 测试
├── test_code_context.py # 源码窗口与边界回归测试
├── AGENTS.md          # 四条永久开发规范
├── requirements.txt   # 依赖（pydantic、mcp 1.x）
├── .gitignore         # 忽略缓存、虚拟环境、密钥等
├── LICENSE            # MIT 开源许可证
└── README.md
```

---

## ❓ 小提示

- 如果在 Windows 旧版 `cmd` 里看到中文乱码，先执行 `chcp 65001` 切到 UTF-8，再运行 `python main.py`。
- 想接入自己的日志：直接调用 `run_doctor(你的日志字符串)`，或只取降噪结果 `remove_noise_lines(...)`。

---

## 📄 License

本项目采用 [MIT License](LICENSE) 开源。

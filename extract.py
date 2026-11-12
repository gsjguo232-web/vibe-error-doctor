# 导入 Python 自带的正则库 re，用来按"固定格式"从一坨文字里捞东西
import re

# 从我们自己写的 models.py 里，把定位模型拿过来用
from models import ErrorLocation

# 正则是黑盒：作用是把堆栈定位文字变成文件路径、行号和函数名的匹配规则
_TRACEBACK_PATTERN = re.compile(r'File "(.+)", line (\d+), in (.+)')


# 本函数作用：吃进一整段报错日志（文字），吐出最后一条出错定位（模型），认不出来就吐 None
def extract_location(log_text: str) -> ErrorLocation | None:
    # 正则是黑盒：作用是把报错日志变成文件路径、行号和函数名的匹配列表
    matches = _TRACEBACK_PATTERN.findall(log_text)
    # 列表是空的，说明这段日志格式我们不认识，返回 None 表示"找不到"
    if not matches:
        # 没有定位信息时交回空结果
        return None
    # 取列表的最后一个元素（Python 里 -1 表示倒数第一）；traceback 最下面那条才是真正出错的地方
    file_path, line_str, func_name = matches[-1]
    # int是黑盒：作用是把文字行号变成整数行号
    line_number = int(line_str)
    # 组装并返回定位模型；column 这里没有，会自动保持 None
    return ErrorLocation(file=file_path, line=line_number, function=func_name)


# 正则是黑盒：作用是把异常摘要文字变成错误类型和报错原文的匹配规则
_ERROR_PATTERN = re.compile(r'^([\w.]+(?:Error|Exception)):\s*(.*)$', re.MULTILINE)


# 本函数作用：吃进整段日志，吐出（错误类型, 报错原文）这个二元组；认不出来吐 None
def extract_error_summary(log_text: str) -> tuple[str, str] | None:
    # 正则是黑盒：作用是把报错日志变成错误类型和原文的匹配列表
    matches = _ERROR_PATTERN.findall(log_text)
    # 一项都没捞到，说明不是标准异常格式，返回 None
    if not matches:
        # 没有摘要信息时交回空结果
        return None
    # 取最后一个；多层异常时最后匹配的那条才是最终抛出来的
    error_type, message = matches[-1]
    # 原文可能是空字符串，补一句占位文字，避免后面做空值判断时踩坑
    if not message.strip():
        # 给没有说明的错误补上占位文字
        message = "(无附加说明)"
    # 返回二元组；调用方可以这样接：err_type, msg = extract_error_summary(log)
    return error_type, message


# 本函数作用：吃进（文件路径, 出错行号, 上下各看几行），吐出带行号和箭头标记的源码片段；抓不到就吐 None
def extract_code_context(file_path: str, line_number: int, window: int = 3) -> str | None:
    # 整个读取过程套上"保险网"：文件不存在、路径是虚拟的、编码不对，都只返回 None，绝不让程序崩溃
    try:
        # open是黑盒：作用是把本地文件路径变成按 UTF-8 解码的可读文件
        with open(file_path, "r", encoding="utf-8") as file:
            # 读取全部源码，每个列表元素对应一行
            all_lines = file.readlines()
        # len是黑盒：作用是把源码列表变成总行数，用于检查行号和窗口是否合法
        if line_number < 1 or line_number > len(all_lines) or window < 0:
            # 行号无效或窗口为负时交回空结果
            return None
        # max是黑盒：作用是把窗口起点和 1 变成不早于首行的起始行号
        start_line = max(1, line_number - window)
        # min和len是黑盒：作用是把源码总行数和窗口终点变成不超过末行的结束行号
        end_line = min(len(all_lines), line_number + window)
        # 准备一个空列表，用来装拼好行号的每一行文字
        parts: list[str] = []
        # range是黑盒：作用是把片段起止行号变成逐行抓拍的行号序列
        for current_line in range(start_line, end_line + 1):
            # 去掉源码末尾的换行符，避免输出多余空行
            text = all_lines[current_line - 1].rstrip("\n")
            # 是真正出错的那一行就加 "> " 箭头，其余行加两个空格，让行号列对得整整齐齐
            mark = "> " if current_line == line_number else "  "
            # 把箭头、对齐的行号和源码拼成抓拍结果的一行
            parts.append(f"{mark}{current_line:>4} | {text}")
        # 把抓拍列表合成一段保留换行的源码文字
        return "\n".join(parts)
    # 任何异常都走这里：安静地返回 None，把"抓不到"交给调用方决定怎么显示
    except Exception:
        # 文件不可读时交回空结果，保留其他诊断信息
        return None

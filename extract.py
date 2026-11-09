# 导入 Python 自带的正则库 re，用来按"固定格式"从一坨文字里捞东西
import re

# 从我们自己写的 models.py 里，把定位模型拿过来用
from models import ErrorLocation

# 正则黑盒①：作用是从 'File "app.py", line 42, in foo' 这行里提取 [文件路径, 行号, 函数名] 三样东西
# (.+) 意思是"捞任意一串字"，(\d+) 意思是"捞一串数字"，in 后面 (.+) 是"捞函数名"
_TRACEBACK_PATTERN = re.compile(r'File "(.+)", line (\d+), in (.+)')


# 本函数作用：吃进一整段报错日志（文字），吐出最后一条出错定位（模型），认不出来就吐 None
def extract_location(log_text: str) -> ErrorLocation | None:
    # findall 是黑盒：从 log_text 里把符合上面格式的片段全部捞出来，结果是一个列表，每项是三元组
    matches = _TRACEBACK_PATTERN.findall(log_text)
    # 列表是空的，说明这段日志格式我们不认识，返回 None 表示"找不到"
    if not matches:
        return None
    # 取列表的最后一个元素（Python 里 -1 表示倒数第一）；traceback 最下面那条才是真正出错的地方
    file_path, line_str, func_name = matches[-1]
    # 捞出来的行号是文字（比如 "42"），用 int() 掉包成整数，才能塞进模型的 int 字段
    line_number = int(line_str)
    # 组装并返回定位模型；column 这里没有，会自动保持 None
    return ErrorLocation(file=file_path, line=line_number, function=func_name)


# 正则黑盒②：作用是从一行 'ZeroDivisionError: division by zero' 里提取 [错误类型, 报错原文]
# ^ 是行首，[\w.]+ 是"一串字母数字下划线或点"，冒号后面整段归第二组
_ERROR_PATTERN = re.compile(r'^([\w.]+(?:Error|Exception)):\s*(.*)$', re.MULTILINE)


# 本函数作用：吃进整段日志，吐出（错误类型, 报错原文）这个二元组；认不出来吐 None
def extract_error_summary(log_text: str) -> tuple[str, str] | None:
    # findall 是黑盒：按上面格式逐行捞，列表里每一项都是（错误类型, 原文）这样的二元组
    matches = _ERROR_PATTERN.findall(log_text)
    # 一项都没捞到，说明不是标准异常格式，返回 None
    if not matches:
        return None
    # 取最后一个；多层异常时最后匹配的那条才是最终抛出来的
    error_type, message = matches[-1]
    # 原文可能是空字符串，补一句占位文字，避免后面做空值判断时踩坑
    if not message.strip():
        message = "(无附加说明)"
    # 返回二元组；调用方可以这样接：err_type, msg = extract_error_summary(log)
    return error_type, message


# 本函数作用：吃进（文件路径, 出错行号, 上下各看几行），吐出带行号和箭头标记的源码片段；抓不到就吐 None
def extract_code_context(file_path: str, line_number: int, window: int = 3) -> str | None:
    # 整个读取过程套上"保险网"：文件不存在、路径是虚拟的、编码不对，都只返回 None，绝不让程序崩溃
    try:
        # open 是黑盒：作用是把磁盘上的文件变成可读对象；encoding 指定用 UTF-8 解码，防止中文注释乱码
        with open(file_path, "r", encoding="utf-8") as file:
            # readlines 是黑盒：把整个文件读成一个列表，每个元素是一行（行尾带着换行符）
            all_lines = file.readlines()
        # 算出片段的第一行；max 是黑盒：取两个数里较大的那个，保证不早于第 1 行
        start_line = max(1, line_number - window)
        # 算出片段的最后一行；min 是黑盒：取两个数里较小的那个，保证不超过文件总行数
        end_line = min(len(all_lines), line_number + window)
        # 要看的行号完全落在文件外面（比如行号是 0 或特别大），没东西可抓，返回 None
        if start_line > end_line:
            return None
        # 准备一个空列表，用来装拼好行号的每一行文字
        parts: list[str] = []
        # 从片段第一行逐行走到最后一行
        for current_line in range(start_line, end_line + 1):
            # rstrip 是黑盒：作用是把行尾的换行符去掉，避免打印时多出一行空行
            text = all_lines[current_line - 1].rstrip("\n")
            # 是真正出错的那一行就加 "> " 箭头，其余行加两个空格，让行号列对得整整齐齐
            mark = "> " if current_line == line_number else "  "
            # f-string 里的 :>4 是黑盒：作用是把行号右对齐补空格到 4 位宽，数字才会竖着对齐
            parts.append(f"{mark}{current_line:>4} | {text}")
        # join 是黑盒：把列表里的每一行用换行符重新粘成一段文字，交出去
        return "\n".join(parts)
    # 任何异常都走这里：安静地返回 None，把"抓不到"交给调用方决定怎么显示
    except Exception:
        return None

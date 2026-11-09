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

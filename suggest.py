# 建一个"查号台"字典：左边是错误类型名字，右边是对应的修复建议
# dict[str, str] 这个标注的意思是"键是文字，值也是文字"
_FIX_HINTS: dict[str, str] = {
    # 除数为 0 时 Python 会抛这个错
    "ZeroDivisionError": "除数可能是 0，先判断再做除法",
    # 字典里找不到这个键
    "KeyError": "字典里没有这个键，改用 dict.get() 或先用 in 判断",
    # 两边的类型对不上，比如数字加字符串
    "TypeError": "两边类型对不上，用 print(type(x)) 看看实际是什么类型",
    # 下标超出了列表长度
    "IndexError": "下标越界了，先用 len() 看看列表到底多长",
    # 文件路径不存在
    "FileNotFoundError": "文件路径不对，检查拼写和当前工作目录",
    # 对象身上根本没有这个属性，多半是名字拼错或对象类型不对
    "AttributeError": "检查属性名有没有拼错，再用 print(type(obj)) 看看对象到底是什么类型",
    # 传进去的值本身不合法，比如把 'abc' 硬转成 int
    "ValueError": "检查传给函数的值是否合法，比如能不能转成 int、格式对不对，先 print 出原值看看",
    # 导入的名字在模块里找不到，通常是名字拼错
    "ImportError": "检查 from ... import ... 里的名字拼写，确认模块里确实有这个名字",
    # Python 连这个模块都没找到，通常是没装或包名拼错
    "ModuleNotFoundError": "模块没装或名字拼错，先跑 pip install 装好，再检查 import 的拼写",
    # 一段文字不是合法 JSON，解析时炸掉
    "JSONDecodeError": "把响应原文打印出来看看，确认它是合法 JSON，而不是空字符串、HTML 页面或纯文本",
    # pydantic 校验数据时发现某个字段不符合要求
    "ValidationError": "检查传给模型的字段名、类型和必填项，对照报错里点名的那个字段改",
    # 网络请求或其他操作等太久，超时了
    "TimeoutError": "给请求加上 timeout 并做重试，同时检查网络或服务端是不是响应太慢",
}


# 本函数作用：给一个错误类型名，返回一句修复建议；没见过的类型就给通用建议
def suggest_fix(error_type: str) -> str:
    # rsplit 是黑盒：从右边按点切一次并取最后一段，把 json.decoder.JSONDecodeError 变成 JSONDecodeError
    short_name = error_type.rsplit(".", 1)[-1]
    # 先按短名字查，查不到再用完整名字查，都没有就返回兜底建议（or 会跳过空值，不会报错）
    return _FIX_HINTS.get(short_name) or _FIX_HINTS.get(error_type) or "暂无匹配建议，请查看报错原文和出错行附近的代码"

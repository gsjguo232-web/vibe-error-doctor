# 从 pydantic 库里拿出两样东西：BaseModel 是"数据模型的地基"，Field 用来给字段加小规矩
from pydantic import BaseModel, Field


# 定义"报错定位"模型：专门存放"错误出在哪个文件、哪一行、哪个函数"这类信息
class ErrorLocation(BaseModel):
    # 出错的文件路径；类型标注 str 表示这里必须是一串文字
    file: str
    # 出错的行号；类型标注 int 表示这里必须是整数，传 "abc" 会自动被骂
    line: int
    # 出错的列号；int | None 表示"整数或者空"，= None 表示不写这个字段也行
    column: int | None = None
    # 出错的函数名；同理，要么一串文字，要么空着
    function: str | None = None


# 定义"诊断结果"模型：把定位信息 + 错误类型 + 原始报错 + 修复建议打包成一体
class DiagnosisResult(BaseModel):
    # 定位字段；这里不写 str，而是写 ErrorLocation，意思是"必须塞一个上面的定位模型进来"
    location: ErrorLocation
    # 错误类型名字，比如 "ZeroDivisionError"；字符串
    error_type: str
    # 原始报错原文；字符串
    message: str
    # 大白话修复建议；Field(min_length=1) 是给这个字段加的规矩：至少 1 个字，不允许空字符串
    suggestion: str = Field(min_length=1)

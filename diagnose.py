# 从 denoise.py 里取降噪函数，先把日志"脱水"再去分析
from denoise import remove_noise_lines
# 从 extract.py 里取两块"从日志捞东西"的积木，再加上新的"源码抓拍"积木
from extract import extract_location, extract_error_summary, extract_code_context
# 从 models.py 里取诊断单模型，这是最终要装出来的东西
from models import DiagnosisResult
# 从 suggest.py 里取"错误类型 → 建议"的查号台
from suggest import suggest_fix


# 本函数作用：吃进一整段日志，吐出拼好的完整诊断单；缺任何一块料就吐 None
def build_diagnosis(log_text: str) -> DiagnosisResult | None:
    # 第一步：先降噪，把空行、指示符和第三方库堆栈都去掉
    clean_text = remove_noise_lines(log_text)
    # 第二步：在降噪后的日志里捞定位（文件、行号、函数名）
    location = extract_location(clean_text)
    # 降噪后捞不到定位时，退回原日志再捞一次，防止降噪把有用的定位误删
    if location is None:
        # 用原始日志重新寻找出错位置
        location = extract_location(log_text)
    # 第三步：在降噪后的日志里捞（错误类型, 原文）
    summary = extract_error_summary(clean_text)
    # 降噪后捞不到报错摘要时，同样退回原日志再捞一次
    if summary is None:
        # 用原始日志重新寻找错误类型和原文
        summary = extract_error_summary(log_text)
    # 只要有一块没捞到，就拼不出完整诊断单，直接返回 None 收工
    if location is None or summary is None:
        # 定位或摘要缺失时交回空结果
        return None
    # 把二元组拆开，分别装进两个变量：错误类型、原文
    error_type, message = summary
    # 第四步：拿错误类型去查一句建议；字典里没有会给通用建议，不会报错
    suggestion = suggest_fix(error_type)
    # 第五步：拿定位里的文件路径和行号，去本地磁盘抓取出错行前后的真实源码；抓不到也没关系，会是 None
    code_context = extract_code_context(location.file, location.line)
    # 五样料齐了，一起塞进诊断单模型，这就是本函数的最终产物
    return DiagnosisResult(
        # 填入出错文件、行号和函数名
        location=location,
        # 填入错误类型
        error_type=error_type,
        # 填入报错原文
        message=message,
        # 填入修复建议
        suggestion=suggestion,
        # 填入源码抓拍，读取失败时保留空值
        code_context=code_context,
    # 完成诊断单的组装并交回调用方
    )

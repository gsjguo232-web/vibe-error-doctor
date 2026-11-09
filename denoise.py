# 一份"以这些开头就算噪声"的清单；元组和列表一样，只是装东西的盒子
_NOISE_PREFIXES: tuple[str, ...] = (
    # Python 打印调用栈时固定会带的第一行，本身不含信息
    "Traceback (most recent call last):",
    # 异常链里夹在中间的提示句，也不是真正的报错
    "During handling of the above exception",
)

# 一份"只要包含这些字眼就算第三方库/系统内部噪音"的清单
_NOISE_KEYWORDS: tuple[str, ...] = (
    # 第三方库安装目录的典型路径片段，基本都是和我们无关的库代码
    "site-packages",
    # Python 冻结模块（内置模块）的典型路径片段，同样属于系统内部噪音
    "<frozen",
)


# 本函数作用：吃进一整段日志，吐出去掉噪声行的版本；行数会变少，内容不变
def remove_noise_lines(log_text: str) -> str:
    # 准备一个空列表，用来装"我决定留下"的行
    kept_lines: list[str] = []
    # splitlines 是黑盒：把一整段文字按换行切成一个列表，每个元素是一行
    lines: list[str] = log_text.splitlines()
    # 跳行标记：上一行如果是第三方库堆栈，它下面的源码片段也要一起扔掉
    skip_next: bool = False
    # 逐个检查每一行
    for one_line in lines:
        # 去掉这行左右两边的空格，得到一个"干净版"，判断都用它，但存的时候还是存原版
        stripped = one_line.strip()
        # 先处理"上一行是第三方堆栈"的情况
        if skip_next:
            # 跳行标记用一次就复位，避免误伤后面的行
            skip_next = False
            # 缩进且不是新的 File 行，说明它是被扔掉那层的源码片段，一起扔掉
            if one_line[:1].isspace() and not stripped.startswith('File "'):
                continue
        # 规则一：整行只有空白（比如空行），直接扔掉
        if not stripped:
            continue
        # 规则二：每行去掉空格后，如果剩下的字符全是 ^ 或 ~，说明是"箭头指示行"，扔掉
        if all(char in "^~" for char in stripped):
            continue
        # 规则三：落在噪声清单里的开头，扔掉
        if stripped.startswith(_NOISE_PREFIXES):
            continue
        # 规则四：定位行里带第三方库或系统内部路径，连同它下面的源码片段一起扔掉
        if stripped.startswith('File "') and any(keyword in stripped for keyword in _NOISE_KEYWORDS):
            # 做个记号，让下一行的源码片段也被跳过
            skip_next = True
            continue
        # 规则五：其他任何一行只要带第三方库或系统内部路径字眼，也扔掉
        if any(keyword in stripped for keyword in _NOISE_KEYWORDS):
            continue
        # 逃过上面五道检查的都是有用的行，收到篮子里
        kept_lines.append(one_line)
    # 兜底：如果全被过滤光了，就保留原始日志，免得用户看到一片空白
    if not kept_lines:
        return log_text
    # join 是黑盒：把列表里的文字用换行重新粘成整段文字，吐出去
    return "\n".join(kept_lines)

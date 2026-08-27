# 500个字符为一个chunk 每个chunk中间重复100个字符，防止分割语义不完整
# eg：0~499 400~899
def split_text(text: str,chunk_size: int = 500,overlap: int = 100) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")
    if overlap < 0:
        raise ValueError("overlap 不能小于 0")
    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")

    text = text.strip() # 去掉字符串开头、结尾的空白字符
    if not text:
        return []

    chunks: list[str] = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size,text_length,)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks
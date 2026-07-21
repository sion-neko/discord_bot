"""
5-7-5判定モジュール

メッセージ本文を形態素解析し、モーラ（拍）数が5-7-5になっているかを判定します。
"""
import re

from janome.tokenizer import Tokenizer

from utils.logger import setup_logger

logger = setup_logger(__name__)

_tokenizer = Tokenizer()

# 拗音を作る小書きカナ。直前の文字と合わせて1モーラなので単独ではカウントしない。
_SMALL_YOON = set('ァィゥェォヵヶャュョ')

_CUSTOM_EMOJI_RE = re.compile(r'<a?:\w+:\d+>')
_MENTION_RE = re.compile(r'<@!?\d+>|<@&\d+>|<#\d+>')
_URL_RE = re.compile(r'https?://\S+')

_TARGET_MORA = (5, 7, 5)
_TOTAL_MORA = sum(_TARGET_MORA)
_BOUNDARY_1 = _TARGET_MORA[0]
_BOUNDARY_2 = _TARGET_MORA[0] + _TARGET_MORA[1]


def count_mora(reading: str) -> int:
    """カタカナ読みからモーラ数を数える"""
    return sum(1 for ch in reading if ch not in _SMALL_YOON)


def _clean(text: str) -> str:
    text = _CUSTOM_EMOJI_RE.sub('', text)
    text = _MENTION_RE.sub('', text)
    text = _URL_RE.sub('', text)
    return text.strip()


def _is_kana(text: str) -> bool:
    return bool(text) and all(
        '぀' <= ch <= 'ゟ' or '゠' <= ch <= 'ヿ' or ch in _SMALL_YOON
        for ch in text
    )


def _tokenize(text: str):
    """トークンごとの(表層形, モーラ数)のリストを返す。読みが解決できないトークンがあればNoneを返す"""
    result = []
    for token in _tokenizer.tokenize(text):
        reading = token.reading
        if reading == '*':
            if _is_kana(token.surface):
                reading = token.surface
            else:
                return None
        result.append((token.surface, count_mora(reading)))
    return result


def _split_three_lines(text: str):
    """3行に分かれたテキストがそれぞれ5・7・5モーラならその3行をそのまま返す"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if len(lines) != 3:
        return None

    for line, expected in zip(lines, _TARGET_MORA):
        tokens = _tokenize(line)
        if tokens is None or sum(m for _, m in tokens) != expected:
            return None
    return lines


def _split_single_line(text: str):
    """1行のテキストを単語境界に沿って5・7・5モーラの3行に分割して返す"""
    tokens = _tokenize(text)
    if tokens is None:
        return None

    if sum(m for _, m in tokens) != _TOTAL_MORA:
        return None

    cumulative_mora = 0
    cumulative_chars = 0
    boundary_1_pos = None
    boundary_2_pos = None
    for surface, mora in tokens:
        cumulative_mora += mora
        cumulative_chars += len(surface)
        if cumulative_mora == _BOUNDARY_1:
            boundary_1_pos = cumulative_chars
        elif cumulative_mora == _BOUNDARY_2:
            boundary_2_pos = cumulative_chars

    if boundary_1_pos is None or boundary_2_pos is None:
        return None

    return [
        text[:boundary_1_pos],
        text[boundary_1_pos:boundary_2_pos],
        text[boundary_2_pos:],
    ]


def split_575(text: str):
    """5-7-5と判定できれば[5音, 7音, 5音]の3行に分割して返す。判定できなければNoneを返す"""
    cleaned = _clean(text)
    if not cleaned:
        return None

    try:
        if '\n' in cleaned:
            lines = _split_three_lines(cleaned)
            if lines is not None:
                return lines
            # 改行があっても3行に整形されていない場合は改行を除いて1行判定にフォールバック
            cleaned = cleaned.replace('\n', '')
            if not cleaned:
                return None
        return _split_single_line(cleaned)
    except Exception as e:
        logger.warning(f"[senryu] 解析エラー: {e}")
        return None


def is_senryu(text: str) -> bool:
    """テキストが5-7-5（モーラ数・単語境界基準）かどうかを判定する"""
    return split_575(text) is not None

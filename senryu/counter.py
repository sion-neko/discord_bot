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


def _token_mora_counts(text: str):
    """トークンごとのモーラ数のリストを返す。読みが解決できないトークンがあればNoneを返す"""
    counts = []
    for token in _tokenizer.tokenize(text):
        reading = token.reading
        if reading == '*':
            if _is_kana(token.surface):
                reading = token.surface
            else:
                return None
        counts.append(count_mora(reading))
    return counts


def _check_three_lines(text: str) -> bool:
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if len(lines) != 3:
        return False

    for line, expected in zip(lines, _TARGET_MORA):
        counts = _token_mora_counts(line)
        if counts is None or sum(counts) != expected:
            return False
    return True


def _check_single_line(text: str) -> bool:
    counts = _token_mora_counts(text)
    if counts is None:
        return False

    total = sum(counts)
    if total != _TOTAL_MORA:
        return False

    cumulative = 0
    boundaries = set()
    for c in counts:
        cumulative += c
        boundaries.add(cumulative)

    return _BOUNDARY_1 in boundaries and _BOUNDARY_2 in boundaries


def is_senryu(text: str) -> bool:
    """テキストが5-7-5（モーラ数・単語境界基準）かどうかを判定する"""
    cleaned = _clean(text)
    if not cleaned:
        return False

    try:
        if '\n' in cleaned:
            if _check_three_lines(cleaned):
                return True
            # 改行があっても3行に整形されていない場合は改行を除いて1行判定にフォールバック
            cleaned = cleaned.replace('\n', '')
            if not cleaned:
                return False
        return _check_single_line(cleaned)
    except Exception as e:
        logger.warning(f"[senryu] 解析エラー: {e}")
        return False

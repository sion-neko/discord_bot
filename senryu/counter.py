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
_SENTENCE_SPLIT_RE = re.compile(r'[。\n！？!?]+')

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


def _sentences(text: str):
    """。\n！？で文単位に分割する"""
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]


def _match_three_sentences(sentences):
    """連続する3文がそれぞれ5・7・5モーラならその3文をそのまま返す"""
    for sentence, expected in zip(sentences, _TARGET_MORA):
        tokens = _tokenize(sentence)
        if tokens is None or sum(m for _, m in tokens) != expected:
            return None
    return list(sentences[:3])


def _split_sentence(text: str):
    """1文を単語境界に沿って5・7・5モーラの3行に分割して返す"""
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
    """
    テキスト中に5-7-5があれば[5音, 7音, 5音]の3行に分割して返す。
    「。」「\\n」「！」「？」で文に分割し、
    (1) 連続する3文がそれぞれ5・7・5になっている箇所
    (2) 単体で5-7-5（17モーラ・単語境界一致）になっている文
    のいずれかが見つかればそれを返す。見つからなければNoneを返す。
    """
    cleaned = _clean(text)
    if not cleaned:
        return None

    try:
        sentences = _sentences(cleaned)
        if not sentences:
            return None

        for i in range(len(sentences) - 2):
            matched = _match_three_sentences(sentences[i:i + 3])
            if matched is not None:
                return matched

        for sentence in sentences:
            result = _split_sentence(sentence)
            if result is not None:
                return result

        return None
    except Exception as e:
        logger.warning(f"[senryu] 解析エラー: {e}")
        return None


def is_senryu(text: str) -> bool:
    """テキストが5-7-5（モーラ数・単語境界基準）かどうかを判定する"""
    return split_575(text) is not None

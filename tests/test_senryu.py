from senryu import is_senryu, split_575
from senryu.counter import count_mora


def test_count_mora_basic():
    assert count_mora('フルイケヤ') == 5


def test_count_mora_youon_not_counted_separately():
    # キャ・シュ・ニョ等の拗音は直前の文字と合わせて1モーラ
    assert count_mora('キャベツ') == 3


def test_count_mora_sokuon_choonpu_n_counted():
    # 促音「ッ」・長音「ー」・撥音「ン」はそれぞれ独立した1モーラ
    assert count_mora('コーヒー') == 4
    assert count_mora('ヤッタ') == 3
    assert count_mora('ホンダ') == 3


def test_split_575_single_line_kanji_haiku():
    assert split_575('古池や蛙飛び込む水の音') == ['古池や', '蛙飛び込む', '水の音']


def test_split_575_explicit_three_lines():
    assert split_575('古池や\n蛙飛び込む\n水の音') == ['古池や', '蛙飛び込む', '水の音']


def test_split_575_matches_single_sentence_within_longer_message():
    # 5-7-5になっているのは2文目だけの2行メッセージ
    text = 'まじ辛い\nこの時期に病院どこもやってない'
    assert split_575(text) == ['この時期に', '病院どこも', 'やってない']


def test_split_575_matches_three_consecutive_sentences_split_by_punctuation():
    text = 'マジ辛い！この時期に病院どこもやってない！つらすぎる'
    assert split_575(text) == ['この時期に', '病院どこも', 'やってない']


def test_split_575_strips_mentions_before_matching():
    text = '<@123456789012345678> 古池や蛙飛び込む水の音'
    assert split_575(text) == ['古池や', '蛙飛び込む', '水の音']


def test_split_575_none_for_non_575_text():
    assert split_575('こんにちは') is None
    assert split_575('プログラムがうごかないなぜだろう') is None


def test_split_575_none_for_empty_or_whitespace():
    assert split_575('') is None
    assert split_575('   ') is None


def test_split_575_none_when_no_sentence_matches():
    assert split_575('猫が好き。犬も好き。鳥も好き') is None


def test_is_senryu_matches_split_575():
    assert is_senryu('古池や蛙飛び込む水の音') is True
    assert is_senryu('こんにちは') is False

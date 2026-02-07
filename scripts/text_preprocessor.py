#!/usr/bin/env python3
"""
日本語TTS用テキスト前処理モジュール

数字の読み方を文脈に応じて正しく変換する。
例: 「1000万」→「いっせんまん」、「1000円」→「せんえん」
"""

import re
import argparse
from typing import Optional


class JapaneseTextPreprocessor:
    """日本語テキストの前処理クラス"""

    # 数字の基本読み
    DIGIT_READINGS = {
        '0': 'ゼロ', '1': 'いち', '2': 'に', '3': 'さん', '4': 'よん',
        '5': 'ご', '6': 'ろく', '7': 'なな', '8': 'はち', '9': 'きゅう'
    }

    # 特殊な数字読み（促音化など）
    SPECIAL_READINGS = {
        '1兆': 'いっちょう',
        '1000兆': 'いっせんちょう',
        '8兆': 'はっちょう',
        '10兆': 'じゅっちょう',
        '100兆': 'ひゃくちょう',
        '6百': 'ろっぴゃく',
        '8百': 'はっぴゃく',
        '3千': 'さんぜん',
        '8千': 'はっせん',
    }

    def __init__(self):
        self.debug_mode = False

    def preprocess(self, text: str, show_debug: bool = False) -> str:
        """
        テキストを前処理する

        Args:
            text: 入力テキスト
            show_debug: デバッグ情報を表示するか

        Returns:
            前処理済みテキスト
        """
        self.debug_mode = show_debug

        # Step 1: 全角数字を半角に
        text = self._normalize_numbers(text)

        # Step 2: 数字+単位の読み変換
        text = self._convert_number_readings(text)

        # Step 3: 全角/半角の正規化
        text = self._normalize_width(text)

        return text

    def _normalize_numbers(self, text: str) -> str:
        """全角数字を半角に変換"""
        zen_to_han = str.maketrans('０１２３４５６７８９', '0123456789')
        return text.translate(zen_to_han)

    def _normalize_width(self, text: str) -> str:
        """全角/半角の正規化（数字以外）"""
        # 全角スペースを半角に
        text = text.replace('　', ' ')
        return text

    def _convert_number_readings(self, text: str) -> str:
        """
        数字の読み方を文脈に応じて変換

        ルール:
        - X千万/X千億/X千兆 → いっせんまん/いっせんおく/いっせんちょう
        - 1億/1兆 → いちおく/いっちょう
        - 100万 → ひゃくまん（「いち」は入らない）
        - 1000 (単独) → せん
        """

        # パターン1: 千+大単位（万/億/兆）の組み合わせ
        # 1000万、2000万、5000億 など
        def replace_sen_with_unit(match):
            prefix = match.group(1) or ''  # 千の前の数字（あれば）
            unit = match.group(2)  # 万/億/兆

            if self.debug_mode:
                print(f"  [DEBUG] Match: {match.group(0)} -> prefix={prefix}, unit={unit}")

            # 千の前に数字がない場合（1000万 = 千万）
            if not prefix or prefix == '1':
                if unit == '万':
                    return 'いっせんまん'
                elif unit == '億':
                    return 'いっせんおく'
                elif unit == '兆':
                    return 'いっせんちょう'
            else:
                # 2000万、3000億など
                digit_reading = self._get_digit_reading(prefix)
                if unit == '万':
                    return f'{digit_reading}せんまん'
                elif unit == '億':
                    return f'{digit_reading}せんおく'
                elif unit == '兆':
                    return f'{digit_reading}せんちょう'

            return match.group(0)

        # 「X千万」「X千億」「X千兆」パターン
        text = re.sub(r'(\d)?千(万|億|兆)', replace_sen_with_unit, text)

        # パターン2: 数字+万/億/兆（千を含まない）
        # 1万、100万、1億 など
        def replace_number_with_unit(match):
            number = match.group(1)
            unit = match.group(2)

            if self.debug_mode:
                print(f"  [DEBUG] Number+Unit: {number}{unit}")

            # 1万、1億、1兆 の場合
            if number == '1':
                if unit == '万':
                    return 'いちまん'
                elif unit == '億':
                    return 'いちおく'
                elif unit == '兆':
                    return 'いっちょう'
            # 100万、10万 などはそのまま（ひゃくまん、じゅうまん）

            return match.group(0)

        # 「数字+万/億/兆」パターン（千万等は除外済み）
        text = re.sub(r'(\d+)(万|億|兆)', replace_number_with_unit, text)

        if self.debug_mode:
            print(f"  [Result] {text}")

        return text

    def _get_digit_reading(self, digit: str) -> str:
        """1桁の数字の読みを取得"""
        if digit in self.DIGIT_READINGS:
            return self.DIGIT_READINGS[digit]
        return digit

    def get_reading_annotation(self, text: str) -> str:
        """
        テキストに読み仮名アノテーションを付与

        Returns:
            読み仮名付きテキスト
        """
        processed = self.preprocess(text, show_debug=True)
        return f"原文: {text}\n読み: {processed}"


def main():
    parser = argparse.ArgumentParser(description='日本語TTS用テキスト前処理')
    parser.add_argument('--text', '-t', type=str, required=True,
                        help='処理するテキスト')
    parser.add_argument('--show-reading', '-r', action='store_true',
                        help='読み変換の詳細を表示')
    parser.add_argument('--output', '-o', type=str,
                        help='出力ファイル（省略時は標準出力）')

    args = parser.parse_args()

    preprocessor = JapaneseTextPreprocessor()

    if args.show_reading:
        result = preprocessor.get_reading_annotation(args.text)
    else:
        result = preprocessor.preprocess(args.text)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
        print(f"Output saved to: {args.output}")
    else:
        print(result)


if __name__ == '__main__':
    main()

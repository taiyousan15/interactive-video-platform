#!/usr/bin/env python3
"""
Fish Audio TTS - 日本語音声合成

Fish Audio APIを使用した高品質日本語TTS。
LLMベースの文脈理解により、数字の読み方も自動的に正しく処理される。
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from typing import Optional

# 前処理モジュールをインポート
sys.path.insert(0, str(Path(__file__).parent))
from text_preprocessor import JapaneseTextPreprocessor


class FishAudioTTS:
    """Fish Audio APIを使用したTTSクラス"""

    BASE_URL = "https://api.fish.audio/v1/tts"

    # デフォルトの日本語ボイスID
    DEFAULT_VOICE_ID = "d4c86c697b3e4fc090cf056f17530b2a"

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Fish Audio APIキー（環境変数から取得可能）
        """
        self.api_key = api_key or os.environ.get("FISH_AUDIO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FISH_AUDIO_API_KEY environment variable is not set. "
                "Get your API key from https://fish.audio/"
            )
        self.preprocessor = JapaneseTextPreprocessor()

    def synthesize(
        self,
        text: str,
        output_path: str,
        voice_id: Optional[str] = None,
        format: str = "mp3",
        chunk_length: int = 200,
        normalize: bool = True,
        preprocess: bool = True,
    ) -> str:
        """
        テキストを音声に変換

        Args:
            text: 読み上げるテキスト
            output_path: 出力ファイルパス
            voice_id: ボイスID（省略時はデフォルト日本語ボイス）
            format: 出力形式（mp3/wav）
            chunk_length: チャンク長
            normalize: 参照音声の正規化
            preprocess: 日本語前処理を適用するか

        Returns:
            出力ファイルパス
        """
        # 日本語前処理（オプション）
        if preprocess:
            processed_text = self.preprocessor.preprocess(text)
            print(f"[Preprocessed] {text[:50]}... -> {processed_text[:50]}...")
        else:
            processed_text = text

        # APIリクエスト
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "text": processed_text,
            "reference_id": voice_id or self.DEFAULT_VOICE_ID,
            "format": format,
            "chunk_length": chunk_length,
            "normalize": normalize,
            "latency": "normal",
        }

        print(f"[Fish Audio] Generating speech...")
        print(f"  Voice ID: {payload['reference_id']}")
        print(f"  Format: {format}")
        print(f"  Text length: {len(processed_text)} chars")

        response = requests.post(
            self.BASE_URL,
            headers=headers,
            json=payload,
            stream=True,
        )

        if response.status_code != 200:
            error_msg = response.text
            raise Exception(f"Fish Audio API error: {response.status_code} - {error_msg}")

        # 出力ディレクトリを作成
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 音声データを保存
        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        file_size = output_file.stat().st_size / 1024
        print(f"[Success] Saved to: {output_path} ({file_size:.1f} KB)")

        return str(output_file)

    def list_voices(self) -> list:
        """
        利用可能なボイス一覧を取得

        Returns:
            ボイス情報のリスト
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        response = requests.get(
            "https://api.fish.audio/v1/voices",
            headers=headers,
        )

        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}")

        return response.json()


def main():
    parser = argparse.ArgumentParser(description='Fish Audio日本語TTS')
    parser.add_argument('--text', '-t', type=str, required=True,
                        help='読み上げるテキスト')
    parser.add_argument('--output', '-o', type=str,
                        default='output/fish_tts.mp3',
                        help='出力ファイルパス')
    parser.add_argument('--voice-id', '-v', type=str,
                        help='ボイスID（省略時はデフォルト日本語ボイス）')
    parser.add_argument('--format', '-f', type=str,
                        choices=['mp3', 'wav'], default='mp3',
                        help='出力形式')
    parser.add_argument('--chunk-length', type=int, default=200,
                        help='チャンク長')
    parser.add_argument('--no-normalize', action='store_true',
                        help='参照音声の正規化を無効化')
    parser.add_argument('--no-preprocess', action='store_true',
                        help='日本語前処理を無効化')
    parser.add_argument('--list-voices', action='store_true',
                        help='利用可能なボイス一覧を表示')

    args = parser.parse_args()

    try:
        tts = FishAudioTTS()

        if args.list_voices:
            voices = tts.list_voices()
            print("Available voices:")
            for voice in voices[:10]:  # 最初の10件
                print(f"  - {voice.get('id')}: {voice.get('name')}")
            return

        output_path = tts.synthesize(
            text=args.text,
            output_path=args.output,
            voice_id=args.voice_id,
            format=args.format,
            chunk_length=args.chunk_length,
            normalize=not args.no_normalize,
            preprocess=not args.no_preprocess,
        )

        print(f"\n✅ Generated: {output_path}")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

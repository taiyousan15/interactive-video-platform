#!/usr/bin/env python3
"""
Style-Bert-VITS2 TTS - ローカル高品質日本語音声合成

Style-Bert-VITS2 JP-Extraを使用したローカルTTS。
BERTによる文脈理解とアクセント制御が可能。
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


class StyleBertVITS2TTS:
    """Style-Bert-VITS2を使用したTTSクラス"""

    DEFAULT_URL = "http://localhost:5000"

    # 利用可能なスタイル
    STYLES = [
        "Neutral",   # 中立
        "Happy",     # 嬉しい
        "Sad",       # 悲しい
        "Angry",     # 怒り
        "Fearful",   # 恐怖
        "Surprised", # 驚き
        "Disgust",   # 嫌悪
    ]

    def __init__(self, base_url: Optional[str] = None):
        """
        Args:
            base_url: Style-Bert-VITS2サーバーURL
        """
        self.base_url = base_url or os.environ.get(
            "STYLE_BERT_VITS2_URL", self.DEFAULT_URL
        )
        self.preprocessor = JapaneseTextPreprocessor()

    def check_server(self) -> bool:
        """サーバーの稼働状況を確認"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False

    def list_models(self) -> list:
        """
        利用可能なモデル一覧を取得

        Returns:
            モデル情報のリスト
        """
        try:
            response = requests.get(f"{self.base_url}/models/info")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []

    def synthesize(
        self,
        text: str,
        output_path: str,
        model_name: str = "jvnv-F1-jp",
        style: str = "Neutral",
        style_weight: float = 1.0,
        speed: float = 1.0,
        sdp_ratio: float = 0.2,
        noise: float = 0.6,
        noise_w: float = 0.8,
        preprocess: bool = True,
    ) -> str:
        """
        テキストを音声に変換

        Args:
            text: 読み上げるテキスト
            output_path: 出力ファイルパス
            model_name: モデル名
            style: スタイル（Neutral/Happy/Sad/Angry等）
            style_weight: スタイル強度（0.0-2.0）
            speed: 話速（0.5-2.0）
            sdp_ratio: SDPモード比率（0.0-1.0）
            noise: ノイズスケール
            noise_w: ノイズスケールW
            preprocess: 日本語前処理を適用するか

        Returns:
            出力ファイルパス
        """
        # サーバー確認
        if not self.check_server():
            raise ConnectionError(
                f"Style-Bert-VITS2 server is not running at {self.base_url}. "
                "Please start the server first:\n"
                "  cd Style-Bert-VITS2 && python server_editor.py --host 0.0.0.0 --port 5000"
            )

        # 日本語前処理（オプション）
        if preprocess:
            processed_text = self.preprocessor.preprocess(text)
            print(f"[Preprocessed] {text[:50]}... -> {processed_text[:50]}...")
        else:
            processed_text = text

        # APIリクエスト
        params = {
            "text": processed_text,
            "model_name": model_name,
            "style": style,
            "style_weight": style_weight,
            "speed": speed,
            "sdp_ratio": sdp_ratio,
            "noise": noise,
            "noise_w": noise_w,
            "auto_split": True,
            "split_interval": 0.5,
            "language": "JP",
        }

        print(f"[Style-Bert-VITS2] Generating speech...")
        print(f"  Model: {model_name}")
        print(f"  Style: {style} (weight={style_weight})")
        print(f"  Speed: {speed}")
        print(f"  Text length: {len(processed_text)} chars")

        try:
            response = requests.get(
                f"{self.base_url}/voice",
                params=params,
                timeout=120,
            )
        except requests.exceptions.Timeout:
            raise TimeoutError("Request timed out. Text may be too long.")

        if response.status_code != 200:
            error_msg = response.text
            raise Exception(f"Style-Bert-VITS2 error: {response.status_code} - {error_msg}")

        # 出力ディレクトリを作成
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 音声データを保存
        with open(output_file, "wb") as f:
            f.write(response.content)

        file_size = output_file.stat().st_size / 1024
        print(f"[Success] Saved to: {output_path} ({file_size:.1f} KB)")

        return str(output_file)

    def synthesize_with_accent(
        self,
        text: str,
        reading: str,
        accent: str,
        output_path: str,
        **kwargs,
    ) -> str:
        """
        アクセント指定で音声を生成

        Args:
            text: 元テキスト
            reading: 読み（カタカナ）
            accent: アクセントパターン（例: "0111100000"）
            output_path: 出力ファイルパス
            **kwargs: synthesize()の追加パラメータ

        Returns:
            出力ファイルパス
        """
        # アクセント指定形式でテキストを構成
        # 形式: 読み|アクセントパターン
        accent_text = f"{reading}|{accent}"

        print(f"[Accent Mode] {text}")
        print(f"  Reading: {reading}")
        print(f"  Accent: {accent}")

        # 前処理をスキップ（アクセント指定時は手動制御）
        return self.synthesize(
            text=accent_text,
            output_path=output_path,
            preprocess=False,
            **kwargs,
        )


def main():
    parser = argparse.ArgumentParser(description='Style-Bert-VITS2日本語TTS')
    parser.add_argument('--text', '-t', type=str, required=True,
                        help='読み上げるテキスト')
    parser.add_argument('--output', '-o', type=str,
                        default='output/sbv2_tts.wav',
                        help='出力ファイルパス')
    parser.add_argument('--model', '-m', type=str, default='jvnv-F1-jp',
                        help='モデル名')
    parser.add_argument('--style', '-s', type=str, default='Neutral',
                        choices=StyleBertVITS2TTS.STYLES,
                        help='スタイル')
    parser.add_argument('--style-weight', type=float, default=1.0,
                        help='スタイル強度（0.0-2.0）')
    parser.add_argument('--speed', type=float, default=1.0,
                        help='話速（0.5-2.0）')
    parser.add_argument('--sdp-ratio', type=float, default=0.2,
                        help='SDPモード比率（0.0-1.0）')
    parser.add_argument('--server-url', type=str,
                        help='サーバーURL（省略時は環境変数またはlocalhost:5000）')
    parser.add_argument('--no-preprocess', action='store_true',
                        help='日本語前処理を無効化')
    parser.add_argument('--list-models', action='store_true',
                        help='利用可能なモデル一覧を表示')
    parser.add_argument('--check-server', action='store_true',
                        help='サーバー稼働状況を確認')

    args = parser.parse_args()

    try:
        tts = StyleBertVITS2TTS(base_url=args.server_url)

        if args.check_server:
            if tts.check_server():
                print(f"✅ Server is running at {tts.base_url}")
            else:
                print(f"❌ Server is not running at {tts.base_url}")
            return

        if args.list_models:
            models = tts.list_models()
            if models:
                print("Available models:")
                for model in models:
                    print(f"  - {model}")
            else:
                print("No models found or server not running")
            return

        output_path = tts.synthesize(
            text=args.text,
            output_path=args.output,
            model_name=args.model,
            style=args.style,
            style_weight=args.style_weight,
            speed=args.speed,
            sdp_ratio=args.sdp_ratio,
            preprocess=not args.no_preprocess,
        )

        print(f"\n✅ Generated: {output_path}")

    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

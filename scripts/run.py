#!/usr/bin/env python3
"""
Japan TTS - 実行ラッパー

使用方法:
  python run.py fish_tts.py --text "テキスト" --output output.mp3
  python run.py style_bert_tts.py --text "テキスト" --output output.wav
  python run.py preprocessor.py --text "1000万円" --show-reading
"""

import os
import sys
import subprocess
from pathlib import Path


def get_venv_python():
    """仮想環境のPythonパスを取得"""
    script_dir = Path(__file__).parent.parent
    venv_dir = script_dir / "venv"

    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        python_path = venv_dir / "bin" / "python"

    if python_path.exists():
        return str(python_path)
    return sys.executable


def setup_venv():
    """仮想環境をセットアップ"""
    script_dir = Path(__file__).parent.parent
    venv_dir = script_dir / "venv"

    if not venv_dir.exists():
        print("[Setup] Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)

        # 依存関係インストール
        pip_path = get_venv_python().replace("python", "pip")
        if sys.platform != "win32":
            pip_path = str(venv_dir / "bin" / "pip")
        else:
            pip_path = str(venv_dir / "Scripts" / "pip.exe")

        print("[Setup] Installing dependencies...")
        subprocess.run([
            pip_path, "install", "requests",
        ], check=True)
        print("[Setup] Done!")


def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py <script.py> [args...]")
        print("")
        print("Available scripts:")
        print("  fish_tts.py        - Fish Audio API TTS（デフォルト推奨）")
        print("  style_bert_tts.py  - Style-Bert-VITS2 ローカルTTS")
        print("  preprocessor.py    - テキスト前処理（デバッグ用）")
        print("")
        print("Examples:")
        print("  python run.py fish_tts.py --text '1000万円の投資' --output output.mp3")
        print("  python run.py style_bert_tts.py --text 'こんにちは' --style Happy")
        print("  python run.py preprocessor.py --text '1000万円' --show-reading")
        sys.exit(1)

    script_name = sys.argv[1]
    script_args = sys.argv[2:]

    # スクリプトパスを構築
    script_dir = Path(__file__).parent
    script_path = script_dir / script_name

    # ショートカット名の処理
    shortcuts = {
        "fish": "fish_tts.py",
        "sbv2": "style_bert_tts.py",
        "bert": "style_bert_tts.py",
        "preprocess": "preprocessor.py",
        "pre": "preprocessor.py",
    }

    if script_name in shortcuts:
        script_path = script_dir / shortcuts[script_name]

    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    # 実行
    python_path = get_venv_python()

    # 環境変数を継承
    env = os.environ.copy()

    # 実行
    result = subprocess.run(
        [python_path, str(script_path)] + script_args,
        env=env,
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()

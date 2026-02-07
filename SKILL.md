---
name: japan-tts
description: 日本語TTS（Text-to-Speech）スキル。Fish Audio APIをデフォルトとし、Style-Bert-VITS2のローカル高品質モードも対応。日本語の文脈理解により「1000万」→「いっせんまん」のような正しい読み分けを実現。
---

# Japan TTS - 日本語音声合成スキル

日本語の文脈を正しく理解し、流暢な音声を生成するTTSスキル。

## When to Use This Skill

以下のキーワードで発動:
- 「音声生成」「TTS」「読み上げ」「ナレーション」
- 「日本語音声」「音声ファイル作成」
- 「テキストを音声に」「スピーチ生成」
- `/japan-tts` `/tts-japan`

## Quick Start

```bash
cd ~/.claude/skills/japan-tts

# 1. Fish Audio API（デフォルト・推奨）
python scripts/run.py fish_tts.py \
  --text "2026年、1000万円の投資で始める新時代" \
  --output output/narration.mp3

# 2. Style-Bert-VITS2（ローカル高品質）
python scripts/run.py style_bert_tts.py \
  --text "AIエージェントが1000体稼働する未来" \
  --output output/narration.wav

# 3. テキスト前処理のみ（デバッグ用）
python scripts/run.py preprocessor.py \
  --text "1000万円を投資" \
  --show-reading
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Japan TTS Pipeline                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  入力テキスト                                                    │
│       ↓                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Layer 1: 日本語前処理 (text_preprocessor.py)            │   │
│  │  ├─ 数字読み変換（1000万→いっせんまん）                   │   │
│  │  ├─ 全角/半角正規化                                      │   │
│  │  └─ 特殊記号処理                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Layer 2: TTS Engine Selection                           │   │
│  │                                                          │   │
│  │  ┌──────────────┐    ┌──────────────────────┐           │   │
│  │  │ Fish Audio   │    │ Style-Bert-VITS2     │           │   │
│  │  │ (Default)    │    │ (Local High-Quality) │           │   │
│  │  │              │    │                      │           │   │
│  │  │ - LLM文脈理解 │    │ - BERT文脈理解       │           │   │
│  │  │ - API課金    │    │ - ローカル無料       │           │   │
│  │  │ - 超高品質   │    │ - 高品質             │           │   │
│  │  └──────────────┘    └──────────────────────┘           │   │
│  └─────────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│  出力: MP3/WAV                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 数字読みルール（自動適用）

| 入力 | 出力読み | ルール |
|------|---------|--------|
| 1000 | せん | 単独では「いち」不要 |
| 1000万 | いっせんまん | 万の直前では「いっせん」必須 |
| 1000億 | いっせんおく | 億の直前では「いっせん」必須 |
| 1000兆 | いっせんちょう | 兆の直前では「いっせん」必須 |
| 1500万 | せんごひゃくまん | 万の直前でなければ任意 |
| 100万 | ひゃくまん | 百万には「いち」不要 |
| 1億 | いちおく | 万以上は「いち」必須 |

## Engine Comparison

| 項目 | Fish Audio | Style-Bert-VITS2 |
|------|-----------|------------------|
| **文脈理解** | ✅ LLM内蔵（最高） | ○ BERT（良好） |
| **数字読み** | ✅ 自動 | ○ 前処理必要 |
| **セットアップ** | 簡単（API） | 中（ローカル） |
| **コスト** | 課金制 | 無料 |
| **品質** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **速度** | 高速 | 中速 |
| **オフライン** | ✗ | ✅ |

## Parameters

### Fish Audio TTS

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--text` | Yes | - | 読み上げテキスト |
| `--output` | No | `output/fish_tts.mp3` | 出力ファイルパス |
| `--voice-id` | No | `d4c86c697b3e4fc090cf056f17530b2a` | 声のID |
| `--format` | No | `mp3` | 出力形式（mp3/wav） |
| `--chunk-length` | No | 200 | チャンク長 |
| `--normalize` | No | True | 参照音声正規化 |

### Style-Bert-VITS2 TTS

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--text` | Yes | - | 読み上げテキスト |
| `--output` | No | `output/sbv2_tts.wav` | 出力ファイルパス |
| `--model` | No | `jvnv-F1-jp` | モデル名 |
| `--style` | No | `Neutral` | スタイル |
| `--style-weight` | No | 1.0 | スタイル強度 |
| `--speed` | No | 1.0 | 話速 |
| `--sdp-ratio` | No | 0.2 | SDPモード比率 |

## Usage Examples

### 1. VSL/セールスレターのナレーション

```bash
# Fish Audio（高品質）
python scripts/run.py fish_tts.py \
  --text "2026年、AIエージェント1000体を活用する時代が到来します。
あなたの1000万円の投資が、100億円の価値を生み出す可能性があります。" \
  --output output/vsl_narration.mp3

# Style-Bert-VITS2（ローカル）
python scripts/run.py style_bert_tts.py \
  --text "今から5分後、あなたの人生は変わります。" \
  --style "Happy" \
  --style-weight 1.5 \
  --output output/intro.wav
```

### 2. 教育コンテンツ

```bash
python scripts/run.py fish_tts.py \
  --text "第1章。100万円から始める投資入門。
1000万円を目標に、毎月5万円ずつ積み立てていきましょう。" \
  --output output/chapter1.mp3
```

### 3. バッチ処理（複数ファイル）

```bash
# scripts/batch_tts.py
python scripts/run.py batch_tts.py \
  --input-dir texts/ \
  --output-dir output/ \
  --engine fish
```

## Environment Variables

```bash
# Fish Audio API（必須）
export FISH_AUDIO_API_KEY="your-api-key"

# Style-Bert-VITS2（オプション）
export STYLE_BERT_VITS2_URL="http://localhost:5000"
```

## Setup

### Fish Audio（推奨）

1. [Fish Audio](https://fish.audio/)でアカウント作成
2. APIキーを取得
3. 環境変数に設定

```bash
export FISH_AUDIO_API_KEY="your-api-key"
```

### Style-Bert-VITS2（ローカル）

1. リポジトリをクローン
```bash
git clone https://github.com/litagin02/Style-Bert-VITS2.git
cd Style-Bert-VITS2
```

2. 依存関係インストール
```bash
pip install -r requirements.txt
```

3. モデルダウンロード（JP-Extra推奨）
```bash
python scripts/download_models.py
```

4. APIサーバー起動
```bash
python server_editor.py --host 0.0.0.0 --port 5000
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| API key error | `FISH_AUDIO_API_KEY`環境変数を確認 |
| 数字読み間違い | `preprocessor.py --show-reading`でデバッグ |
| ローカルTTS接続エラー | Style-Bert-VITS2サーバー起動を確認 |
| 音声品質低下 | `--chunk-length`を調整 |

## Data Storage

```
japan-tts/
├── scripts/
│   ├── run.py              # 実行ラッパー
│   ├── fish_tts.py         # Fish Audio API
│   ├── style_bert_tts.py   # Style-Bert-VITS2
│   ├── text_preprocessor.py # 日本語前処理
│   └── batch_tts.py        # バッチ処理
├── data/
│   └── user_dict.csv       # ユーザー辞書（カスタム読み）
├── output/                 # 生成音声
└── models/                 # ローカルモデル（Style-Bert-VITS2）
```

## Related Skills

| Skill | Description |
|-------|-------------|
| `video-agent` | 動画生成パイプライン |
| `omnihuman1-video` | AIアバター動画 |
| `anime-slide-generator` | スライド動画 |

## References

- [Fish-Speech Paper](https://arxiv.org/html/2411.01156v1)
- [Style-Bert-VITS2 GitHub](https://github.com/litagin02/Style-Bert-VITS2)
- [Style-Bert-VITS2 JP-Extra解説](https://zenn.dev/litagin/articles/034819a5256ff4)
- [pyopenjtalk-plus](https://github.com/tsukumijima/pyopenjtalk-plus)

# Human Like Typing

[English README](README.md)

tmuxペインに対して、人間らしい遅延とキーボード打鍵音でテキストをタイピングするPythonアプリケーションです。

## インストール

```bash
pip install -e .
```

## 使い方

### 基本的な使い方

```bash
# テキストを直接入力
human-like "Hello, World!"

# ファイルから読み込み
human-like -f script.txt

# パイプ入力
echo "Hello" | human-like
```

### オプション

```bash
# スピード倍率（2.0 = 2倍速）
human-like --speed 2.0 "text"

# タイプミス率（0.1 = 10%の確率でミス、自動的にBackspaceで修正）
human-like --typo 0.1 "text"

# サウンドエフェクトを無効化
human-like --no-sound "text"

# 特定のサウンドテーマを使用
human-like --theme default "text"

# 特定のtmuxペインに送信
human-like -t right "text"
human-like -t %1 "text"

# オプションの組み合わせ
human-like --speed 2.0 --typo 0.05 -t %8 "Hello, World!"
```

### サウンドデーモン管理

```bash
# デーモンのステータス確認
human-like --daemon status

# デーモンを手動で起動
human-like --daemon start

# 特定のテーマでデーモンを起動
human-like --theme mytheme --daemon start

# デーモンを停止
human-like --daemon stop
```

注意: デーモンは起動時に指定されたテーマを使用します。テーマを切り替えるには、デーモンを停止して再起動してください。

## 機能

### 人間らしいタイピング遅延

文字タイプに基づくランダムな遅延：

| コンテキスト | 遅延範囲 |
|---------|-------------|
| 連続する文字 | 20-50ms（流暢なタイピング） |
| 句読点の後 | 200-600ms（思考の間） |
| スペースの後 | 100-300ms |
| 改行の後 | 300-800ms |

### 流暢性モディファイア

キーボードの人間工学に基づいてタイピング速度を調整：

- **同じキーの連打**: 25%高速化（例: "ll", "ss"）
- **ホームローキー**（asdfghjkl）: 10%高速化
- **左右の手を交互に使用**: 5%高速化（例: "aj", "sl"）

### タイプミスシミュレーション

`--typo`を有効にすると：

1. 指定された確率でミスタイプが発生
2. 間違った文字が入力される（QWERTYレイアウトの隣接キー）
3. 短い間（ミスに気づく）
4. Backspaceで削除
5. 正しい文字を入力

### キーボードサウンドエフェクト

- Unixソケットデーモンを介したリアルなキーボード音
- 通常キー、Enter、Spaceで異なる音
- 高速タイピング時に音が自然にミックス
- 必要に応じて自動起動、バックグラウンドで実行

## サウンドテーマ

### 利用可能なテーマを表示

```bash
human-like --theme list
```

これにより、利用可能なすべてのサウンドテーマが表示されます。デフォルトテーマはアスタリスク（*）でマークされます。

### カスタムテーマの作成

`sounds/`ディレクトリに新しいディレクトリを追加することで、独自のサウンドテーマを作成できます：

1. テーマディレクトリを作成（例: `sounds/mytheme/`）
2. 以下の構造で`theme.json`ファイルを追加：

```json
{
    "name": "My Custom Theme",
    "description": "テーマの説明",
    "sounds": {
        "single_mid": "key-press-mid.mp3",
        "single_hard": "key-press-hard.mp3",
        "single_gentle": "key-press-gentle.mp3",
        "enter_mid": "enter-mid.mp3",
        "enter_hard": "enter-hard.mp3",
        "space_mid": "space-mid.mp3",
        "space_hard": "space-hard.mp3",
        "shift": "shift.mp3"
    }
}
```

3. MP3サウンドファイルを同じディレクトリに配置
4. テーマを使用: `human-like --theme mytheme "text"`

8つのサウンドキー（`single_mid`, `single_hard`, `single_gentle`, `enter_mid`, `enter_hard`, `space_mid`, `space_hard`, `shift`）はすべて必須です。

## サウンドファイル

### デフォルトテーマ

デフォルトテーマは`sounds/default/`ディレクトリにあります：

| ファイル | 説明 |
|------|-------------|
| `PC-Keyboard06-04(Single-Mid).mp3` | 通常キー（中） |
| `PC-Keyboard06-05(Single-Hard).mp3` | 通常キー（強） |
| `PC-Keyboard06-06(Single-Gentle).mp3` | 通常キー（弱） |
| `PC-Keyboard06-08(Enter-Mid).mp3` | Enterキー（中） |
| `PC-Keyboard06-09(Enter-Hard).mp3` | Enterキー（強） |
| `PC-Keyboard06-10(Space-Mid).mp3` | Spaceキー（中） |
| `PC-Keyboard06-11(Space-Hard).mp3` | Spaceキー（強） |
| `PC-Keyboard06-12(Shift).mp3` | Shiftキー |

**出典:** [OtoLogic](https://otologic.jp/free/se/pc-keyboard01.html)
**ライセンス:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

## 依存関係

- Python 3.10+
- click: CLIフレームワーク
- numpy: オーディオミキシング
- sounddevice: リアルタイムオーディオ再生
- soundfile: オーディオファイル読み込み

## ライセンス

MIT

---

Built with [Claude Code](https://claude.ai/code)

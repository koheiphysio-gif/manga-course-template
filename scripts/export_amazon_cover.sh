#!/usr/bin/env bash
# image_genで生成した表紙を、Amazon向けの1600×2560 JPEGとして書き出す。
# 使い方: bash scripts/export_amazon_cover.sh 入力画像.png 出力画像.jpg

set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "使い方: bash scripts/export_amazon_cover.sh 入力画像 出力画像.jpg" >&2
  exit 1
fi

src="$1"
dst="$2"

if [ ! -f "$src" ]; then
  echo "入力画像が見つかりません: $src" >&2
  exit 1
fi

case "$dst" in
  *.jpg|*.jpeg) ;;
  *)
    echo "出力ファイルは .jpg または .jpeg にしてください: $dst" >&2
    exit 1
    ;;
esac

# 先に高さ2560pxへ拡大し、余る左右を中央トリミングする。
# 縦横を強制変形しないため、人物や文字の比率を保てる。
tmp="${dst%.*}_resampled.png"
cropped="${dst%.*}_cropped.png"
sips --resampleHeight 2560 "$src" --out "$tmp" >/dev/null
sips --cropToHeightWidth 2560 1600 "$tmp" --out "$cropped" >/dev/null
sips --setProperty format jpeg "$cropped" --out "$dst" >/dev/null
rm "$tmp" "$cropped"

width="$(sips -g pixelWidth "$dst" | awk '/pixelWidth/ {print $2}')"
height="$(sips -g pixelHeight "$dst" | awk '/pixelHeight/ {print $2}')"
format="$(sips -g format "$dst" | awk '/format/ {print $2}')"

if [ "$width" != "1600" ] || [ "$height" != "2560" ] || [ "$format" != "jpeg" ]; then
  echo "書き出し検証に失敗しました: ${width}x${height}, format=${format}" >&2
  exit 1
fi

echo "Amazon向けJPEGを書き出しました: $dst (${width}x${height}, ${format})"

<div align="center">
	<a href="https://github.com/CrossDarkrix/DSRE-Equalizer">
	<img width="150px" height="150px" alt="DSRE-Equalizer" src="https://raw.githubusercontent.com/CrossDarkrix/DSRE-Equalizer/refs/heads/main/icon.png"></a>
</div>

---

# DSRE-Equalizer

**DSRE-Equalizer(Deep Sound Resolution Enhancer Equalizer)** は、Android上で再生中の音声を取得し、リアルタイムに軽量な音響補助処理を行う実験的なアプリです。

現在の安定版では、元の再生音に対して **Wet Delta / Air Assist** 方式の補助音を薄く重ねる設計になっています。

---

## 概要

DSRE-Equalizer は、Android端末上で再生されている音声をキャプチャし、軽量なコンプレッション、サチュレーション、差分生成、Air Assist処理を通して、明瞭感や空気感を補助的に加えることを目的としたリアルタイム音響処理アプリです。

従来の単純なパススルー方式では、元アプリの通常再生音とDSRE側の再出力音が重なり、二重音や遅延感が目立つ場合がありました。  
そのため、フルレンジの加工音をそのまま重ねるのではなく、加工によって生じた差分成分や高域寄りの補助成分を小さく出力する方向へ調整しています。

---

## 主な機能

- Android上の再生音声をリアルタイム取得
- MINI_DSREベースの軽量DSP処理
- Wet Deltaモード
- Air Assistモード
- 入力ゲイン、補助ゲイン、サチュレーション量などの調整
- 非root環境での動作を前提にした設計
- シンプルなMaterial風UI
- デバッグ用ファイルログを抑制した実用寄り構成

---

## 処理モード

### Mode 6: Full MINI_DSRE

従来型のMINI_DSRE処理です。

```text
input
→ gain
→ compressor
→ saturation
→ output
```

効果は分かりやすい一方で、元の再生音と重なるため、環境によっては二重音が目立つ場合があります。

---

### Mode 7: Wet Delta

加工前後の差分のみを出力するモードです。

```text
dry = input * gain
processed = MINI_DSRE(dry)
wet = processed - dry
output = wet * assistGain
```

元音そのものを再出力するのではなく、加工によって変化した成分だけを補助的に重ねます。  
二重音を抑えたい場合に有効です。

---

### Mode 8: Air Assist

```text
dry = input * gain
processed = MINI_DSRE(dry)
wet = processed - dry
air = high-pass-like component from wet
output = blended assist signal * assistGain
```

Wet Deltaよりもさらに高域寄りの補助成分を重視し、低域・中域の遅延コピー感を抑えることを狙っています。

---

## 推奨初期設定

```text
Mode: 8
Input Gain: 0.30
Threshold: 0.14
Ratio: 2.20
Makeup: 1.05
Saturation Drive: 1.22
Saturation Mix: 0.16
Output Gain: 1.00
Assist Gain: 0.20 - 0.35
Air Mix: 0.80
Air HP Alpha: 0.08
```

二重感が強い場合は、まず `Assist Gain` を下げてください。

```text
Assist Gain: 0.15 - 0.25
```

効果が薄い場合は、少しずつ上げてください。

```text
Assist Gain: 0.30 - 0.40
```

---


## 現在の仕様と制限

DSRE-Equalizerは、Androidの標準的な制約の範囲内で動作するアプリです。

そのため、他アプリの音声出力そのものを直接置き換えるのではなく、取得した音声をDSRE側で処理して補助的に出力します。

この構成では、環境によって以下のような現象が発生する場合があります。

- 元音と補助音が重なって聞こえる
- 再出力側にわずかな遅延を感じる
- 対象アプリや端末によってキャプチャできる音声が異なる
- 音量設定によって効果の感じ方が大きく変わる


---

## 注意事項

このアプリは実験的なリアルタイム音響処理アプリです。

使用する端末、Androidバージョン、再生アプリ、音声出力経路によって挙動が変わる可能性があります。  
また、長時間使用時は端末のバッテリー消費や発熱に注意してください。

---

## 推奨用途

- Android上の再生音声に軽い明瞭感を加えたい場合
- リアルタイム音響処理の実験
- AudioPlaybackCaptureを使ったDSP処理の検証
- 非root環境での内部音声処理ルートの研究

---

## 非推奨用途

- 完全なシステムワイドイコライザーの代替
- 遅延ゼロが必要な用途
- 元音を完全に置き換える用途
- すべてのアプリ音声に必ず効くことを前提にした用途

---

## Disclaimer

DSRE-Equalizer is an experimental audio processing application.  
Behavior may vary depending on device, Android version, playback application, and audio output route.

This application does not guarantee system-wide audio replacement or zero-latency processing.

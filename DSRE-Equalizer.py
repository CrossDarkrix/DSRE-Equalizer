# -*- coding: utf-8 -*-
import json
import os
import sys
import traceback

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.graphics import Color, Ellipse, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput

TAG = 'DSREMain'
CONFIG_NAME = 'mini_dsre_config.json'

MATERIAL = {
    'bg': (0.070, 0.082, 0.102, 1),
    'surface': (0.105, 0.121, 0.149, 1),
    'surface_alt': (0.130, 0.150, 0.185, 1),
    'primary': (0.250, 0.430, 0.860, 1),
    'secondary': (0.180, 0.800, 0.650, 1),
    'danger': (0.980, 0.300, 0.300, 1),
    'text': (0.925, 0.941, 0.965, 1),
    'muted': (0.650, 0.700, 0.780, 1),
    'black': (0.000, 0.000, 0.000, 1),
}

DEFAULT_PARAMS = {
    'gain': 0.30,
    'mode': 8,
    'threshold': 0.14,
    'ratio': 2.20,
    'makeup': 1.05,
    'satDrive': 1.22,
    'satMix': 0.16,
    'outputGain': 1.00,
    'assistGain': 0.25,
    'airMix': 0.80,
    'airHpAlpha': 0.08,
    'language': 'ja',
}

PARAM_SPECS = {
    'mode':        {'min': 6.0,   'max': 8.0,  'step': 1.0,   'decimals': 0, 'integer': True},
    'gain':        {'min': 0.05,  'max': 1.0,  'step': 0.01,  'decimals': 2, 'integer': False},
    'threshold':   {'min': 0.02,  'max': 0.60, 'step': 0.01,  'decimals': 2, 'integer': False},
    'ratio':       {'min': 1.0,   'max': 8.0,  'step': 0.10,  'decimals': 2, 'integer': False},
    'makeup':      {'min': 0.50,  'max': 2.0,  'step': 0.01,  'decimals': 2, 'integer': False},
    'satDrive':    {'min': 0.50,  'max': 3.0,  'step': 0.01,  'decimals': 2, 'integer': False},
    'satMix':      {'min': 0.0,   'max': 1.0,  'step': 0.01,  'decimals': 2, 'integer': False},
    'outputGain':  {'min': 0.20,  'max': 2.0,  'step': 0.01,  'decimals': 2, 'integer': False},
    'assistGain':  {'min': 0.0,   'max': 1.0,  'step': 0.01,  'decimals': 2, 'integer': False},
    'airMix':      {'min': 0.0,   'max': 1.0,  'step': 0.01,  'decimals': 2, 'integer': False},
    'airHpAlpha':  {'min': 0.005, 'max': 0.50, 'step': 0.005, 'decimals': 3, 'integer': False},
}

I18N = {
    'ja': {
        'app_title': 'DSRE-Equalizer v1.0.5',
        'subtitle': 'Quiet Assist / Wet Delta / Air Assist',
        'status': 'ステータス',
        'ready': '待機中',
        'param_section': 'Wet Assist パラメータ',
        'mode_help': 'Mode: 6=Full, 7=Wet Delta, 8=Air Assist',
        'control': '操作',
        'save': '保存',
        'apply': '適用',
        'reset': 'リセット',
        'start': '開始',
        'stop': '停止',
        'info_title': 'DSRE-Equalizer について',
        'info_body': (
            'DSRE-Equalizerは、\nAndroid上で再生中の音声を取得し、\nWet Delta / Air Assistによる\n補助音を薄く重ねる\nリアルタイム音響処理アプリです。\n\n'
            'このアプリは元の音声を完全に置き換えるものではありません。\n元アプリの再生音に対して、加工で発生した差分成分や高域寄りの補助成分を小さく足すことで、\n二重音を抑えながら明瞭感を加えることを目的にしています。\n\n'
            '推奨モードは Mode 8 です。\n二重感が強い場合はAssist Gainを下げ、\n効果が薄い場合は少しずつ上げてください。'
            'DSRE-Equalizerは音声データを外部に送信しません。\nインターネット権限を使用せず、\n設定は端末内部のアプリ専用領域に保存されます。'
        ),
        'language': '言語設定',
        'japanese': '日本語',
        'english': 'English',
        'close': '閉じる',
        'saved': '設定を保存しました',
        'applied': '設定を適用しました',
        'reset_done': '設定をリセットしました',
        'requesting': 'MediaProjectionを要求しています...',
        'start_ignored': 'すでに開始しています',
        'start_failed': '開始に失敗しました',
        'stop_requested': '停止しました',
        'activity_unavailable': 'Activity/Starter が利用できません',
        'start_consent_title': '画面共有と音声処理の確認',
        'start_consent_body': (
            '開始する前に、Androidの画面共有確認では共有対象を「画面全体」にしてください。\n\n'
            'DSRE-Equalizerは、端末上で再生中の音声を取得して、端末内でWet Delta / Air Assist処理を行います。\n\n'
            '取得した音声データを外部サーバーへ送信する設計ではありません。音声処理は端末内で行われ、設定はアプリ専用領域に保存されます。\n\n'
            '内容を確認したらOKを押して、Androidの画面共有許可へ進んでください。'
        ),
        'ok': 'OK',
        'cancel': 'キャンセル',
        'param_mode': 'モード',
        'param_gain': '入力ゲイン',
        'param_threshold': 'しきい値',
        'param_ratio': '比率',
        'param_makeup': 'メイクアップ',
        'param_satDrive': 'サチュレーション Drive',
        'param_satMix': 'サチュレーション Mix',
        'param_outputGain': '出力ゲイン',
        'param_assistGain': '補助ゲイン',
        'param_airMix': 'Air Mix',
        'param_airHpAlpha': 'Air HP Alpha',
    },
    'en': {
        'app_title': 'DSRE-Equalizer v1.0.5',
        'subtitle': 'Quiet Assist / Wet Delta / Air Assist',
        'status': 'Status',
        'ready': 'Ready',
        'param_section': 'Wet Assist Parameters',
        'mode_help': 'Mode: 6=Full, 7=Wet Delta, 8=Air Assist',
        'control': 'Control',
        'save': 'Save',
        'apply': 'Apply',
        'reset': 'Reset',
        'start': 'Start',
        'stop': 'Stop',
        'info_title': 'About DSRE-Equalizer',
        'info_body': (
            'DSRE-Equalizer is a realtime audio assist app for Android. It captures playback audio and adds a subtle Wet Delta / Air Assist component.\n\n'
            'This app does not fully replace the original playback audio. Instead, it adds a small difference or air-like assist signal derived from the processed audio, aiming to reduce doubled-audio artifacts while adding clarity.\n\n'
            'Mode 8 is recommended. If the doubled sound is noticeable, lower Assist Gain. If the effect is too subtle, increase Assist Gain gradually.'
        ),
        'language': 'Language',
        'japanese': '日本語',
        'english': 'English',
        'close': 'Close',
        'saved': 'Settings saved',
        'applied': 'Settings applied',
        'reset_done': 'Settings reset',
        'requesting': 'Requesting MediaProjection...',
        'start_ignored': 'Already running',
        'start_failed': 'Start failed',
        'stop_requested': 'Stopped',
        'activity_unavailable': 'Activity/Starter unavailable',
        'start_consent_title': 'Screen sharing and audio processing confirmation',
        'start_consent_body': (
            'Before starting, please choose “entire screen” in the Android screen sharing confirmation.\n\n'
            'DSRE-Equalizer captures playback audio on this device and processes it locally using Wet Delta / Air Assist.\n\n'
            'The captured audio data is not designed to be sent to external servers. Audio processing is performed on-device, and settings are saved in the app-specific storage area.\n\n'
            'If you understand this, tap OK to continue to the Android screen sharing permission screen.'
        ),
        'ok': 'OK',
        'cancel': 'Cancel',
        'param_mode': 'Mode',
        'param_gain': 'Input Gain',
        'param_threshold': 'Threshold',
        'param_ratio': 'Ratio',
        'param_makeup': 'Makeup',
        'param_satDrive': 'Saturation Drive',
        'param_satMix': 'Saturation Mix',
        'param_outputGain': 'Output Gain',
        'param_assistGain': 'Assist Gain',
        'param_airMix': 'Air Mix',
        'param_airHpAlpha': 'Air HP Alpha',
    },
}

APP_FONT_NAME = None


def register_app_font():
    global APP_FONT_NAME
    candidates = []
    try:
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ja-JP.ttf'))
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_ja-JP.ttf'))
    except Exception:
        pass
    candidates.append(os.path.abspath('_ja-JP.ttf'))
    candidates.append(os.path.abspath('_ja-JP.ttf'))
    candidates.append(os.path.join(os.getcwd(), '_ja-JP.ttf'))
    candidates.append(os.path.join(os.getcwd(), '_ja-JP.ttf'))
    for path in candidates:
        try:
            if path and os.path.exists(path):
                LabelBase.register(name='DSRE_JA_JP', fn_regular=path)
                APP_FONT_NAME = 'DSRE_JA_JP'
                return
        except Exception:
            pass
    APP_FONT_NAME = None


register_app_font()


def tr(lang, key):
    table = I18N.get(lang, I18N['ja'])
    return table.get(key, I18N['ja'].get(key, key))


def is_android_runtime():
    return sys.platform == 'android'


def clamp(v, lo, hi):
    try:
        x = float(v)
    except Exception:
        return lo
    return max(lo, min(hi, x))


def clamp_int(v, lo, hi):
    try:
        x = int(float(v))
    except Exception:
        return lo
    return max(lo, min(hi, x))


class MaterialCard(BoxLayout):
    def __init__(self, radius=16, bg_color=None, **kw):
        super().__init__(**kw)
        self.padding = kw.get('padding', dp(10))
        self.spacing = kw.get('spacing', dp(8))
        with self.canvas.before:
            Color(*(bg_color or MATERIAL['surface']))
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(radius)])
        self.bind(pos=self._sync_canvas, size=self._sync_canvas)

    def _sync_canvas(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size


class CircleInfoButton(Button):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.text = 'i'
        self.bold = True
        self.color = MATERIAL['text']
        self.font_size = '18sp'
        self.size_hint = (None, None)
        self.size = (dp(38), dp(38))
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        if APP_FONT_NAME:
            self.font_name = APP_FONT_NAME
        with self.canvas.before:
            Color(*MATERIAL['black'])
            self._circle = Ellipse(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_circle, size=self._sync_circle)

    def _sync_circle(self, *_):
        self._circle.pos = self.pos
        self._circle.size = self.size


class MaterialButton(Button):
    def __init__(self, kind='primary', **kw):
        super().__init__(**kw)
        self.background_normal = ''
        self.background_down = ''
        self.color = MATERIAL['text']
        self.bold = True
        self.size_hint_y = None
        self.height = kw.get('height', dp(42))
        self.font_size = kw.get('font_size', '13sp')
        self.background_color = {
            'danger': MATERIAL['danger'],
            'secondary': MATERIAL['secondary'],
            'flat': MATERIAL['surface_alt'],
            'black': MATERIAL['black'],
        }.get(kind, MATERIAL['primary'])
        if APP_FONT_NAME:
            self.font_name = APP_FONT_NAME


class MaterialInput(TextInput):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.multiline = False
        self.size_hint_y = None
        self.height = kw.get('height', dp(38))
        self.padding = [dp(10), dp(8), dp(10), dp(8)]
        self.background_normal = ''
        self.background_active = ''
        self.background_color = MATERIAL['surface_alt']
        self.foreground_color = MATERIAL['text']
        self.cursor_color = MATERIAL['secondary']
        self.hint_text_color = MATERIAL['muted']
        self.font_size = kw.get('font_size', '13sp')
        if APP_FONT_NAME:
            self.font_name = APP_FONT_NAME


class MaterialLabel(Label):
    def __init__(self, **kw):
        kw.setdefault('color', MATERIAL['text'])
        kw.setdefault('font_size', '13sp')
        kw.setdefault('halign', 'left')
        kw.setdefault('valign', 'middle')
        if APP_FONT_NAME:
            kw.setdefault('font_name', APP_FONT_NAME)
        super().__init__(**kw)
        self.bind(size=lambda *_: setattr(self, 'text_size', self.size))


class SectionTitle(MaterialLabel):
    def __init__(self, **kw):
        kw.setdefault('color', MATERIAL['secondary'])
        kw.setdefault('font_size', '15sp')
        kw.setdefault('bold', True)
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(26))
        super().__init__(**kw)


class SmallLabel(MaterialLabel):
    def __init__(self, **kw):
        kw.setdefault('color', MATERIAL['muted'])
        kw.setdefault('font_size', '11sp')
        kw.setdefault('size_hint_y', None)
        kw.setdefault('height', dp(22))
        super().__init__(**kw)


class ParamControl(BoxLayout):
    def __init__(self, key, label, default_value, minimum, maximum, step, decimals=2, integer=False, **kw):
        super().__init__(orientation='vertical', size_hint_y=None, height=dp(92), spacing=dp(4), **kw)
        self.key = key
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.step = float(step)
        self.decimals = int(decimals)
        self.integer = bool(integer)
        self._syncing = False
        self.label = SmallLabel(text='')
        self.add_widget(self.label)

        row = BoxLayout(size_hint_y=None, height=dp(38), spacing=dp(6))
        self.minus_button = MaterialButton(text='-', kind='flat', width=dp(40), size_hint_x=None)
        self.input = MaterialInput(text=self.format_value(default_value))
        self.plus_button = MaterialButton(text='+', kind='flat', width=dp(40), size_hint_x=None)
        row.add_widget(self.minus_button)
        row.add_widget(self.input)
        row.add_widget(self.plus_button)
        self.add_widget(row)

        self.slider = Slider(min=self.minimum, max=self.maximum, value=self.to_float(default_value), step=self.step, size_hint_y=None, height=dp(34))
        self.add_widget(self.slider)

        self.minus_button.bind(on_release=lambda *_: self.bump(-self.step))
        self.plus_button.bind(on_release=lambda *_: self.bump(self.step))
        self.slider.bind(value=self.on_slider_value)
        self.input.bind(on_text_validate=lambda *_: self.sync_from_text())
        self.input.bind(focus=self.on_input_focus)
        self.set_label(label)
        self.set_value(default_value)

    @property
    def text(self):
        return self.input.text

    @text.setter
    def text(self, value):
        self.set_value(value)

    def set_label(self, label):
        self.label.text = f'{label}  ({self.minimum:g} - {self.maximum:g})'

    def to_float(self, value):
        try:
            v = float(value)
        except Exception:
            v = self.minimum
        if v < self.minimum:
            v = self.minimum
        if v > self.maximum:
            v = self.maximum
        if self.step > 0:
            v = round((v - self.minimum) / self.step) * self.step + self.minimum
        if self.integer:
            v = int(round(v))
        return v

    def format_value(self, value):
        v = self.to_float(value)
        if self.integer:
            return str(int(round(v)))
        return f'{v:.{self.decimals}f}'

    def set_value(self, value):
        if self._syncing:
            return
        self._syncing = True
        v = self.to_float(value)
        self.input.text = self.format_value(v)
        self.slider.value = v
        self._syncing = False

    def bump(self, delta):
        self.set_value(self.to_float(self.input.text) + float(delta))

    def on_slider_value(self, _slider, value):
        if self._syncing:
            return
        self._syncing = True
        self.input.text = self.format_value(value)
        self._syncing = False

    def sync_from_text(self):
        self.set_value(self.input.text)

    def on_input_focus(self, _widget, focused):
        if not focused:
            self.sync_from_text()


class Root(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation='vertical', spacing=dp(10), padding=dp(10), **kw)
        self.activity = None
        self.starter_cls = None
        self.engine_cls = None
        self.capture_running = False
        self.start_button = None
        self.stop_button = None
        self.language = 'ja'
        self.lang_buttons = {}
        with self.canvas.before:
            Color(*MATERIAL['bg'])
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)
        self._build_ui()
        self.setup_android()
        self.load_params_into_ui()
        Clock.schedule_interval(lambda dt: True, 1.0)

    def _sync_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _build_ui(self):
        header = MaterialCard(orientation='horizontal', size_hint_y=None, height=dp(88), padding=dp(12))
        title_box = BoxLayout(orientation='vertical')
        self.title_label = MaterialLabel(text='', font_size='22sp', bold=True, size_hint_y=None, height=dp(34))
        self.subtitle_label = SmallLabel(text='')
        title_box.add_widget(self.title_label)
        title_box.add_widget(self.subtitle_label)
        header.add_widget(title_box)
        self.info_button = CircleInfoButton()
        self.info_button.bind(on_release=lambda *_: self.show_info_popup())
        header.add_widget(self.info_button)
        self.add_widget(header)

        status = MaterialCard(orientation='vertical', size_hint_y=None, height=dp(112))
        self.status_title = SectionTitle(text='')
        status.add_widget(self.status_title)
        self.status = MaterialLabel(text='', size_hint_y=None, height=dp(36))
        self.meter = SmallLabel(text='mode=8 / assistGain=0.25 / saved to mini_dsre_config.json')
        status.add_widget(self.status)
        status.add_widget(self.meter)
        self.add_widget(status)

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        content.bind(minimum_height=content.setter('height'))
        scroll.add_widget(content)
        self.add_widget(scroll)

        panel = MaterialCard(orientation='vertical', size_hint_y=None)
        panel.bind(minimum_height=panel.setter('height'))
        self.param_title = SectionTitle(text='')
        self.mode_help_label = SmallLabel(text='')
        panel.add_widget(self.param_title)
        panel.add_widget(self.mode_help_label)
        self.inputs = {}
        for key in ['mode', 'gain', 'threshold', 'ratio', 'makeup', 'satDrive', 'satMix', 'outputGain', 'assistGain', 'airMix', 'airHpAlpha']:
            spec = PARAM_SPECS[key]
            w = ParamControl(
                key=key,
                label=tr(self.language, 'param_' + key),
                default_value=DEFAULT_PARAMS[key],
                minimum=spec['min'],
                maximum=spec['max'],
                step=spec['step'],
                decimals=spec['decimals'],
                integer=spec['integer'],
            )
            panel.add_widget(w)
            self.inputs[key] = w
        row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.save_button = MaterialButton(text='', kind='secondary')
        self.apply_button = MaterialButton(text='', kind='primary')
        self.reset_button = MaterialButton(text='', kind='flat')
        self.save_button.bind(on_release=lambda *_: self.save_params_only())
        self.apply_button.bind(on_release=lambda *_: self.apply_params_to_running_engine())
        self.reset_button.bind(on_release=lambda *_: self.reset_params())
        row.add_widget(self.save_button)
        row.add_widget(self.apply_button)
        row.add_widget(self.reset_button)
        panel.add_widget(row)
        content.add_widget(panel)

        control = MaterialCard(orientation='vertical', size_hint_y=None)
        control.bind(minimum_height=control.setter('height'))
        self.control_title = SectionTitle(text='')
        control.add_widget(self.control_title)
        row1 = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.start_button = MaterialButton(text='', kind='primary')
        self.stop_button = MaterialButton(text='', kind='danger')
        self.start_button.bind(on_release=lambda *_: self.start_projection_flow())
        self.stop_button.bind(on_release=lambda *_: self.stop_service())
        row1.add_widget(self.start_button)
        row1.add_widget(self.stop_button)
        control.add_widget(row1)
        content.add_widget(control)
        self.set_capture_running(False)
        self.apply_language()

    def set_capture_running(self, running):
        self.capture_running = bool(running)
        if self.start_button is not None:
            self.start_button.disabled = self.capture_running
            self.start_button.opacity = 0.45 if self.capture_running else 1.0
        if self.stop_button is not None:
            self.stop_button.disabled = not self.capture_running
            self.stop_button.opacity = 1.0 if self.capture_running else 0.45

    def apply_language(self):
        self.title_label.text = tr(self.language, 'app_title')
        self.subtitle_label.text = tr(self.language, 'subtitle')
        self.status_title.text = tr(self.language, 'status')
        if not self.status.text:
            self.status.text = tr(self.language, 'ready')
        self.param_title.text = tr(self.language, 'param_section')
        self.mode_help_label.text = tr(self.language, 'mode_help')
        self.control_title.text = tr(self.language, 'control')
        self.save_button.text = tr(self.language, 'save')
        self.apply_button.text = tr(self.language, 'apply')
        self.reset_button.text = tr(self.language, 'reset')
        self.start_button.text = tr(self.language, 'start')
        self.stop_button.text = tr(self.language, 'stop')
        for key, control in self.inputs.items():
            control.set_label(tr(self.language, 'param_' + key))
        for lang, button in self.lang_buttons.items():
            button.opacity = 1.0 if lang == self.language else 0.65

    def show_info_popup(self):
        box = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(14))
        body = MaterialLabel(text=tr(self.language, 'info_body'), font_size='13sp')
        box.add_widget(body)
        box.add_widget(SectionTitle(text=tr(self.language, 'language')))

        lang_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        self.lang_buttons = {}
        ja_button = MaterialButton(text=tr(self.language, 'japanese'), kind='secondary')
        en_button = MaterialButton(text=tr(self.language, 'english'), kind='flat')
        ja_button.bind(on_release=lambda *_: self.set_language('ja'))
        en_button.bind(on_release=lambda *_: self.set_language('en'))
        lang_row.add_widget(ja_button)
        lang_row.add_widget(en_button)
        self.lang_buttons['ja'] = ja_button
        self.lang_buttons['en'] = en_button
        box.add_widget(lang_row)

        close_button = MaterialButton(text=tr(self.language, 'close'), kind='primary')
        box.add_widget(close_button)
        popup = Popup(title=tr(self.language, 'info_title'), content=box, size_hint=(0.90, 0.72), auto_dismiss=True)
        if APP_FONT_NAME:
            popup.title_font = APP_FONT_NAME
        close_button.bind(on_release=popup.dismiss)
        self.apply_language()
        popup.open()

    def set_language(self, language):
        if language not in I18N:
            language = 'ja'
        self.language = language
        self.apply_language()
        self.save_params_only(silent=True)

    def log(self, msg):
        msg = str(msg)
        self.status.text = msg[:180]
        if is_android_runtime():
            try:
                from jnius import autoclass
                autoclass('android.util.Log').d(TAG, msg)
            except Exception:
                pass

    def setup_android(self):
        if not is_android_runtime():
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            self.activity = PythonActivity.mActivity
            self.starter_cls = autoclass('com.crossdarkrix.dsre_realtime.DSREProjectionServiceStarter')
            self.engine_cls = autoclass('com.crossdarkrix.dsre_realtime.DSREAudioCaptureEngine')
        except Exception:
            pass

    def get_config_path(self):
        if is_android_runtime() and self.activity is not None:
            try:
                d = self.activity.getExternalFilesDir(None)
                if d is not None:
                    return os.path.join(d.getAbsolutePath(), CONFIG_NAME)
            except Exception:
                pass
        return os.path.abspath(CONFIG_NAME)

    def read_params_from_ui(self):
        return {
            'mode': clamp_int(self.inputs['mode'].text, 6, 8),
            'gain': clamp(self.inputs['gain'].text, 0.05, 1.0),
            'threshold': clamp(self.inputs['threshold'].text, 0.02, 0.60),
            'ratio': clamp(self.inputs['ratio'].text, 1.0, 8.0),
            'makeup': clamp(self.inputs['makeup'].text, 0.5, 2.0),
            'satDrive': clamp(self.inputs['satDrive'].text, 0.5, 3.0),
            'satMix': clamp(self.inputs['satMix'].text, 0.0, 1.0),
            'outputGain': clamp(self.inputs['outputGain'].text, 0.2, 2.0),
            'assistGain': clamp(self.inputs['assistGain'].text, 0.0, 1.0),
            'airMix': clamp(self.inputs['airMix'].text, 0.0, 1.0),
            'airHpAlpha': clamp(self.inputs['airHpAlpha'].text, 0.005, 0.50),
            'language': self.language,
        }

    def set_ui_from_params(self, p):
        for k, v in DEFAULT_PARAMS.items():
            if k == 'language':
                continue
            if k in self.inputs:
                self.inputs[k].text = str(p.get(k, v))
        self.language = p.get('language', self.language)
        if self.language not in I18N:
            self.language = 'ja'
        self.apply_language()
        self.update_meter(p)

    def update_meter(self, p):
        self.meter.text = f"mode={int(p.get('mode', 8))} gain={float(p.get('gain', 0.30)):.2f} assist={float(p.get('assistGain', 0.25)):.2f} air={float(p.get('airMix', 0.80)):.2f} hp={float(p.get('airHpAlpha', 0.08)):.3f}"

    def load_params_into_ui(self):
        p = dict(DEFAULT_PARAMS)
        path = self.get_config_path()
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    p.update(loaded)
        except Exception:
            pass
        self.set_ui_from_params(p)

    def save_params_only(self, silent=False):
        p = self.read_params_from_ui()
        path = self.get_config_path()
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(p, f, ensure_ascii=False, indent=2)
            self.update_meter(p)
            if not silent:
                self.log(tr(self.language, 'saved'))
        except Exception:
            pass
        return p

    def apply_params_to_running_engine(self):
        p = self.save_params_only(silent=True)
        if self.engine_cls is None:
            return
        try:
            self.engine_cls.configureMiniDsre(float(p['threshold']), float(p['ratio']), float(p['makeup']), float(p['satDrive']), float(p['satMix']), float(p['outputGain']))
            self.engine_cls.configureMiniDsreAssist(float(p['assistGain']), float(p['airMix']), float(p['airHpAlpha']))
            self.log(tr(self.language, 'applied'))
        except Exception:
            pass

    def reset_params(self):
        p = dict(DEFAULT_PARAMS)
        p['language'] = self.language
        self.set_ui_from_params(p)
        self.save_params_only(silent=True)
        self.log(tr(self.language, 'reset_done'))

    def show_start_consent_popup(self):
        box = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(14))
        body = MaterialLabel(
            text=tr(self.language, 'start_consent_body'),
            font_size='13sp',
            size_hint_y=None,
            height=dp(260),
            valign='top',
        )
        body.text_size = (0, None)
        body.bind(width=lambda widget, width: setattr(widget, 'text_size', (width, None)))
        box.add_widget(body)

        button_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))
        cancel_button = MaterialButton(text=tr(self.language, 'cancel'), kind='flat')
        ok_button = MaterialButton(text=tr(self.language, 'ok'), kind='primary')
        button_row.add_widget(cancel_button)
        button_row.add_widget(ok_button)
        box.add_widget(button_row)

        popup = Popup(title=tr(self.language, 'start_consent_title'), content=box, size_hint=(0.92, 0.62), auto_dismiss=False)
        if APP_FONT_NAME:
            popup.title_font = APP_FONT_NAME
        cancel_button.bind(on_release=popup.dismiss)
        ok_button.bind(on_release=lambda *_: self._accept_start_consent(popup))
        popup.open()

    def _accept_start_consent(self, popup):
        try:
            popup.dismiss()
        except Exception:
            pass
        self.start_projection_after_consent()

    def start_projection_after_consent(self):
        if self.capture_running:
            self.log(tr(self.language, 'start_ignored'))
            return
        if not is_android_runtime() or self.activity is None or self.starter_cls is None:
            self.log(tr(self.language, 'activity_unavailable'))
            return
        try:
            self.set_capture_running(True)
            self.save_params_only(silent=True)
            self.apply_params_to_running_engine()
            self.log(tr(self.language, 'requesting'))
            self.starter_cls.requestProjection(self.activity)
        except Exception as exc:
            self.set_capture_running(False)
            self.log(f"{tr(self.language, 'start_failed')}: {exc}")

    def start_projection_flow(self):
        if self.capture_running:
            self.log(tr(self.language, 'start_ignored'))
            return
        if not is_android_runtime() or self.activity is None or self.starter_cls is None:
            self.log(tr(self.language, 'activity_unavailable'))
            return
        self.show_start_consent_popup()

    def stop_service(self):
        if self.starter_cls is None or self.activity is None:
            self.set_capture_running(False)
            return
        try:
            self.starter_cls.stopProjectionService(self.activity)
        except Exception:
            pass
        finally:
            self.set_capture_running(False)
            self.log(tr(self.language, 'stop_requested'))


class AppMain(App):
    title = 'DSRE Realtime Quiet Assist'

    def build(self):
        return Root()


if __name__ == '__main__':
    AppMain().run()

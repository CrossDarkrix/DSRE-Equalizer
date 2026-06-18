# -*- coding: utf-8 -*-
import json, os, sys, traceback
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
TAG='DSREMain'
CONFIG_NAME='mini_dsre_config.json'
MATERIAL={'bg':(0.070,0.082,0.102,1),'surface':(0.105,0.121,0.149,1),'surface_alt':(0.130,0.150,0.185,1),'primary':(0.250,0.430,0.860,1),'secondary':(0.180,0.800,0.650,1),'danger':(0.980,0.300,0.300,1),'text':(0.925,0.941,0.965,1),'muted':(0.650,0.700,0.780,1)}
DEFAULT_PARAMS={'gain':0.30,'mode':8,'threshold':0.14,'ratio':2.20,'makeup':1.05,'satDrive':1.22,'satMix':0.16,'outputGain':1.00,'assistGain':0.25,'airMix':0.80,'airHpAlpha':0.08}
def is_android_runtime(): return sys.platform=='android'
def clamp(v,lo,hi):
    try: x=float(v)
    except Exception: return lo
    return max(lo,min(hi,x))
def clamp_int(v,lo,hi):
    try: x=int(float(v))
    except Exception: return lo
    return max(lo,min(hi,x))
class MaterialCard(BoxLayout):
    def __init__(self,radius=16,bg_color=None,**kw):
        super().__init__(**kw); self.padding=kw.get('padding',dp(10)); self.spacing=kw.get('spacing',dp(8))
        with self.canvas.before: Color(*(bg_color or MATERIAL['surface'])); self._rect=RoundedRectangle(pos=self.pos,size=self.size,radius=[dp(radius)])
        self.bind(pos=self._sync_canvas,size=self._sync_canvas)
    def _sync_canvas(self,*_): self._rect.pos=self.pos; self._rect.size=self.size
class MaterialButton(Button):
    def __init__(self,kind='primary',**kw):
        super().__init__(**kw); self.background_normal=''; self.background_down=''; self.color=MATERIAL['text']; self.bold=True; self.size_hint_y=None; self.height=kw.get('height',dp(42)); self.font_size=kw.get('font_size','13sp'); self.background_color={'danger':MATERIAL['danger'],'secondary':MATERIAL['secondary'],'flat':MATERIAL['surface_alt']}.get(kind,MATERIAL['primary'])
class MaterialInput(TextInput):
    def __init__(self,**kw):
        super().__init__(**kw); self.multiline=False; self.size_hint_y=None; self.height=kw.get('height',dp(38)); self.padding=[dp(10),dp(8),dp(10),dp(8)]; self.background_normal=''; self.background_active=''; self.background_color=MATERIAL['surface_alt']; self.foreground_color=MATERIAL['text']; self.cursor_color=MATERIAL['secondary']; self.hint_text_color=MATERIAL['muted']; self.font_size=kw.get('font_size','13sp')
class MaterialLabel(Label):
    def __init__(self,**kw): kw.setdefault('color',MATERIAL['text']); kw.setdefault('font_size','13sp'); kw.setdefault('halign','left'); kw.setdefault('valign','middle'); super().__init__(**kw); self.bind(size=lambda *_: setattr(self,'text_size',self.size))
class SectionTitle(MaterialLabel):
    def __init__(self,**kw): kw.setdefault('color',MATERIAL['secondary']); kw.setdefault('font_size','15sp'); kw.setdefault('bold',True); kw.setdefault('size_hint_y',None); kw.setdefault('height',dp(26)); super().__init__(**kw)
class SmallLabel(MaterialLabel):
    def __init__(self,**kw): kw.setdefault('color',MATERIAL['muted']); kw.setdefault('font_size','11sp'); kw.setdefault('size_hint_y',None); kw.setdefault('height',dp(22)); super().__init__(**kw)
class Root(BoxLayout):
    def __init__(self,**kw):
        super().__init__(orientation='vertical',spacing=dp(10),padding=dp(10),**kw); self.activity=None; self.starter_cls=None; self.engine_cls=None
        with self.canvas.before: Color(*MATERIAL['bg']); self._bg=Rectangle(pos=self.pos,size=self.size)
        self.bind(pos=self._sync_bg,size=self._sync_bg); self._build_ui(); self.setup_android(); self.load_params_into_ui(); Clock.schedule_interval(lambda dt: True,1.0)
    def _sync_bg(self,*_): self._bg.pos=self.pos; self._bg.size=self.size
    def _build_ui(self):
        header=MaterialCard(orientation='vertical',size_hint_y=None,height=dp(88),padding=dp(12)); header.add_widget(MaterialLabel(text='DSRE Realtime',font_size='22sp',bold=True,size_hint_y=None,height=dp(34))); header.add_widget(SmallLabel(text='Route A Wet Assist / mode 7 delta / mode 8 air assist')); self.add_widget(header)
        status=MaterialCard(orientation='vertical',size_hint_y=None,height=dp(112)); status.add_widget(SectionTitle(text='Status')); self.status=MaterialLabel(text='Ready',size_hint_y=None,height=dp(36)); self.meter=SmallLabel(text='mode=8 / assistGain=0.25 / saved to mini_dsre_config.json'); status.add_widget(self.status); status.add_widget(self.meter); self.add_widget(status)
        scroll=ScrollView(do_scroll_x=False); content=BoxLayout(orientation='vertical',size_hint_y=None,spacing=dp(10)); content.bind(minimum_height=content.setter('height')); scroll.add_widget(content); self.add_widget(scroll)
        panel=MaterialCard(orientation='vertical',size_hint_y=None); panel.bind(minimum_height=panel.setter('height')); panel.add_widget(SectionTitle(text='Route A Wet Assist Parameters')); panel.add_widget(SmallLabel(text='Mode: 6=Full, 7=Wet Delta, 8=Air Assist'))
        self.inputs={}
        for key,label,default in [('mode','Mode','8'),('gain','Input Gain','0.30'),('threshold','Threshold','0.14'),('ratio','Ratio','2.20'),('makeup','Makeup','1.05'),('satDrive','Saturation Drive','1.22'),('satMix','Saturation Mix','0.16'),('outputGain','Output Gain','1.00'),('assistGain','Assist Gain','0.25'),('airMix','Air Mix','0.80'),('airHpAlpha','Air HP Alpha','0.08')]:
            panel.add_widget(SmallLabel(text=label)); w=MaterialInput(text=default); panel.add_widget(w); self.inputs[key]=w
        row=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8));
        for text,kind,fn in [('Save','secondary',self.save_params_only),('Apply','primary',self.apply_params_to_running_engine),('Reset','flat',self.reset_params)]:
            b=MaterialButton(text=text,kind=kind); b.bind(on_release=lambda *_f, fn=fn: fn()); row.add_widget(b)
        panel.add_widget(row); content.add_widget(panel)
        control=MaterialCard(orientation='vertical',size_hint_y=None); control.bind(minimum_height=control.setter('height')); control.add_widget(SectionTitle(text='Realtime Control'))
        row1=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8)); b1=MaterialButton(text='Start Route A',kind='primary'); b2=MaterialButton(text='Stop',kind='danger'); b1.bind(on_release=lambda *_: self.start_projection_flow()); b2.bind(on_release=lambda *_: self.stop_service()); row1.add_widget(b1); row1.add_widget(b2); control.add_widget(row1)
        row2=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8)); b3=MaterialButton(text='Start Service Only',kind='flat'); b4=MaterialButton(text='Clear Java Log',kind='secondary'); b3.bind(on_release=lambda *_: self.start_plain_service()); b4.bind(on_release=lambda *_: self.clear_java_log()); row2.add_widget(b3); row2.add_widget(b4); control.add_widget(row2); content.add_widget(control)
        log_card=MaterialCard(orientation='vertical',size_hint_y=None,height=dp(260)); log_card.add_widget(SectionTitle(text='Diagnostics')); log_scroll=ScrollView(); self.log_box=TextInput(readonly=True,multiline=True,text='',font_size='12sp',background_normal='',background_active='',background_color=MATERIAL['surface_alt'],foreground_color=MATERIAL['text'],cursor_color=MATERIAL['secondary']); log_scroll.add_widget(self.log_box); log_card.add_widget(log_scroll); content.add_widget(log_card)
    def log(self,msg):
        msg=str(msg); self.log_box.text+=msg+'\n'; self.log_box.cursor=(0,len(self.log_box.text.splitlines())); self.status.text=msg[:180]; print(f'[{TAG}] {msg}',flush=True)
        if is_android_runtime():
            try:
                from jnius import autoclass; autoclass('android.util.Log').d(TAG,msg)
            except Exception: pass
    def setup_android(self):
        if not is_android_runtime(): self.log('Non-Android runtime. Build and run on Android device.'); return
        try:
            from jnius import autoclass; PythonActivity=autoclass('org.kivy.android.PythonActivity'); self.activity=PythonActivity.mActivity; self.starter_cls=autoclass('com.crossdarkrix.dsre_realtime.DSREProjectionServiceStarter'); self.engine_cls=autoclass('com.crossdarkrix.dsre_realtime.DSREAudioCaptureEngine'); self.log('Loaded DSRE Java bridge')
        except Exception as exc: self.log('Android setup failed'); self.log(''.join(traceback.format_exception_only(type(exc),exc)).strip()); self.log(traceback.format_exc())
    def get_config_path(self):
        if is_android_runtime() and self.activity is not None:
            try:
                d=self.activity.getExternalFilesDir(None)
                if d is not None: return os.path.join(d.getAbsolutePath(),CONFIG_NAME)
            except Exception: pass
        return os.path.abspath(CONFIG_NAME)
    def read_params_from_ui(self):
        return {'mode':clamp_int(self.inputs['mode'].text,6,8),'gain':clamp(self.inputs['gain'].text,0.05,1.0),'threshold':clamp(self.inputs['threshold'].text,0.02,0.60),'ratio':clamp(self.inputs['ratio'].text,1.0,8.0),'makeup':clamp(self.inputs['makeup'].text,0.5,2.0),'satDrive':clamp(self.inputs['satDrive'].text,0.5,3.0),'satMix':clamp(self.inputs['satMix'].text,0.0,1.0),'outputGain':clamp(self.inputs['outputGain'].text,0.2,2.0),'assistGain':clamp(self.inputs['assistGain'].text,0.0,1.0),'airMix':clamp(self.inputs['airMix'].text,0.0,1.0),'airHpAlpha':clamp(self.inputs['airHpAlpha'].text,0.005,0.50)}
    def set_ui_from_params(self,p):
        for k,v in DEFAULT_PARAMS.items(): self.inputs[k].text=str(p.get(k,v))
        self.update_meter(p)
    def update_meter(self,p): self.meter.text=f"mode={int(p.get('mode',8))} gain={float(p.get('gain',0.30)):.2f} assist={float(p.get('assistGain',0.25)):.2f} air={float(p.get('airMix',0.80)):.2f} hp={float(p.get('airHpAlpha',0.08)):.3f}"
    def load_params_into_ui(self):
        p=dict(DEFAULT_PARAMS); path=self.get_config_path()
        try:
            if os.path.exists(path):
                with open(path,'r',encoding='utf-8') as f: loaded=json.load(f)
                if isinstance(loaded,dict): p.update(loaded)
        except Exception as exc: self.log(f'Load params failed: {exc}')
        self.set_ui_from_params(p)
    def save_params_only(self):
        p=self.read_params_from_ui(); path=self.get_config_path()
        try:
            os.makedirs(os.path.dirname(path),exist_ok=True)
            with open(path,'w',encoding='utf-8') as f: json.dump(p,f,ensure_ascii=False,indent=2)
            self.update_meter(p); self.log(f'Saved Route A params: {path}')
        except Exception as exc: self.log(f'Save params failed: {exc}')
        return p
    def apply_params_to_running_engine(self):
        p=self.save_params_only()
        if self.engine_cls is None: self.log('Engine class unavailable; saved for next start'); return
        try: self.engine_cls.configureMiniDsre(float(p['threshold']),float(p['ratio']),float(p['makeup']),float(p['satDrive']),float(p['satMix']),float(p['outputGain'])); self.engine_cls.configureMiniDsreAssist(float(p['assistGain']),float(p['airMix']),float(p['airHpAlpha'])); self.log('Applied Route A wet assist params to Java engine')
        except Exception as exc: self.log(f'Apply running failed; saved for next start: {exc}')
    def reset_params(self): self.set_ui_from_params(dict(DEFAULT_PARAMS)); self.save_params_only(); self.log('Reset Route A params')
    def start_projection_flow(self):
        if not is_android_runtime() or self.activity is None or self.starter_cls is None: self.log('Activity/Starter unavailable'); return
        try: self.save_params_only(); self.apply_params_to_running_engine(); self.log('Requesting MediaProjection for Route A Wet Assist...'); self.starter_cls.requestProjection(self.activity); self.log('Java requestProjection returned')
        except Exception as exc: self.log('Projection request failed'); self.log(''.join(traceback.format_exception_only(type(exc),exc)).strip()); self.log(traceback.format_exc())
    def start_plain_service(self):
        if not is_android_runtime() or self.starter_cls is None or self.activity is None: self.log('Starter/Activity unavailable'); return
        try: self.save_params_only(); self.log('Calling startPlainServiceForDebug'); self.starter_cls.startPlainServiceForDebug(self.activity,'plain_debug'); self.log('Plain service start requested')
        except Exception as exc: self.log('Plain service start failed'); self.log(''.join(traceback.format_exception_only(type(exc),exc)).strip()); self.log(traceback.format_exc())
    def stop_service(self):
        if self.starter_cls is None or self.activity is None: self.log('Starter/Activity unavailable'); return
        try: self.starter_cls.stopProjectionService(self.activity); self.log('Stop service/capture requested')
        except Exception as exc: self.log(f'Stop failed: {exc}')
    def clear_java_log(self):
        if self.starter_cls is None or self.activity is None: self.log('Starter/Activity unavailable'); return
        try: self.starter_cls.clearExternalLog(self.activity); self.log('Java bridge log cleared')
        except Exception as exc: self.log(f'Clear Java log failed: {exc}')
class AppMain(App):
    title='DSRE Realtime Route A Wet Assist'
    def build(self): return Root()
if __name__=='__main__': AppMain().run()

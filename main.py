# main.py
import os
import json
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window

# === 设置窗口背景色（深灰，护眼）===
Window.clearcolor = (0.12, 0.12, 0.12, 1)

# === 注册中文字体（优先微软雅黑，兼容英文符号）===
from kivy.core.text import LabelBase

FONT_NAME = "Chinese"
font_registered = False
font_paths = [
    r"C:\Windows\Fonts\msyh.ttc",     # 微软雅黑（对英文符号支持更好）
    r"C:\Windows\Fonts\simhei.ttf",   # 黑体
    r"C:\Windows\Fonts\simsun.ttc",   # 宋体
]

for path in font_paths:
    if os.path.exists(path):
        try:
            LabelBase.register(name=FONT_NAME, fn_regular=path)
            print(f"✅ 中文字体注册成功: {path}")
            font_registered = True
            break
        except Exception as e:
            print(f"⚠️ 字体注册失败 {path}: {e}")

if not font_registered:
    print("❌ 未找到中文字体")


def load_word_list(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"加载词库失败: {e}")
        return []


class WordListenApp(App):
    def build(self):
        self.title = "WordListen"
        self.word_dir = "words"

        # 创建默认词库（使用你的格式：/'eibl/）
        if not os.path.exists(self.word_dir):
            os.makedirs(self.word_dir)
            sample_words = [
                {"word": "able", "phonetic": "/'eibl/", "pos": "a.", "definition": "有能力的，出色的"},
                {"word": "abandon", "phonetic": "/'æbəndən/", "pos": "vt.", "definition": "放弃；抛弃"},
                {"word": "accord", "phonetic": "/'əkɔːrd/", "pos": "vt.", "definition": "使一致；给予（同意）"}
            ]
            with open(os.path.join(self.word_dir, "basic.json"), 'w', encoding='utf-8') as f:
                json.dump(sample_words, f, ensure_ascii=False, indent=2)

        self.current_words = []
        self.current_index = 0
        self.auto_play = False
        self.play_meaning = True

        root = BoxLayout(orientation='vertical', padding=15, spacing=12)

        # === 词库选择 ===
        top = BoxLayout(size_hint_y=None, height=45)
        top.add_widget(Label(text="词库:", size_hint_x=0.2, font_name=FONT_NAME, color=(1, 1, 1, 1)))
        self.word_files = [f for f in os.listdir(self.word_dir) if f.endswith('.json')]
        self.spinner = Spinner(
            text=self.word_files[0] if self.word_files else "无词库",
            values=self.word_files,
            size_hint_x=0.6,
            font_name=FONT_NAME
        )
        self.spinner.bind(text=self.on_wordlist_change)
        top.add_widget(self.spinner)
        refresh = Button(text="刷新", size_hint_x=0.2, font_name=FONT_NAME)
        refresh.bind(on_press=self.refresh_wordlist)
        top.add_widget(refresh)
        root.add_widget(top)

        # === 单词显示区域 ===
        self.word_label = Label(
            text="", font_size=36, halign='center', valign='middle',
            font_name=FONT_NAME, size_hint_y=None, height=60,
            color=(1, 1, 1, 1)
        )
        self.word_label.bind(size=self.word_label.setter('text_size'))

        # ✅ 关键修复：音标不使用中文字体！让系统用默认英文字体渲染
        self.phonetic_label = Label(
            text="", font_size=18, halign='center', valign='middle',
            # font_name=FONT_NAME,  ← ← ← 已注释！避免黑体渲染 ' 异常
            size_hint_y=None, height=30,
            color=(0, 1, 0, 1)  # 绿色
        )
        self.phonetic_label.bind(size=self.phonetic_label.setter('text_size'))

        meaning_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=30, spacing=5)
        self.pos_def_label = Label(
            text="", font_size=16, halign='center', valign='middle',
            font_name=FONT_NAME,
            color=(0.9, 0.9, 0.9, 1)
        )
        self.pos_def_label.bind(size=self.pos_def_label.setter('text_size'))
        meaning_row.add_widget(self.pos_def_label)

        root.add_widget(self.word_label)
        root.add_widget(self.phonetic_label)
        root.add_widget(meaning_row)

        # === 控制面板 ===
        controls = GridLayout(cols=2, spacing=10, size_hint_y=None, height=130)

        auto_layout = BoxLayout(spacing=5, size_hint_x=0.9)
        auto_layout.add_widget(Label(text="自动播放", font_name=FONT_NAME, color=(1, 1, 1, 1)))
        self.auto_check = CheckBox(active=False)
        self.auto_check.bind(active=self.toggle_auto_play)
        auto_layout.add_widget(self.auto_check)
        controls.add_widget(auto_layout)

        interval_layout = BoxLayout(spacing=5, size_hint_x=0.9)
        interval_layout.add_widget(Label(text="间隔(s):", font_name=FONT_NAME, color=(1, 1, 1, 1)))
        self.interval_input = TextInput(
            text="3", multiline=False, input_filter='float',
            font_name=FONT_NAME, size_hint_x=0.4, halign='center'
        )
        interval_layout.add_widget(self.interval_input)
        controls.add_widget(interval_layout)

        meaning_layout = BoxLayout(spacing=5, size_hint_x=0.9)
        meaning_layout.add_widget(Label(text="播放中文", font_name=FONT_NAME, color=(1, 1, 1, 1)))
        self.meaning_check = CheckBox(active=True)
        self.meaning_check.bind(active=self.toggle_play_meaning)
        meaning_layout.add_widget(self.meaning_check)
        controls.add_widget(meaning_layout)

        test_btn = Button(text="🔊 测试语音", size_hint_x=0.8, font_name=FONT_NAME)
        test_btn.bind(on_press=self.test_tts)
        controls.add_widget(test_btn)

        root.add_widget(controls)

        # === 导航按钮 ===
        nav = BoxLayout(spacing=10, size_hint_y=None, height=55)
        prev_btn = Button(text="◀ 上一个", font_name=FONT_NAME, size_hint_x=0.33)
        play_btn = Button(text="🔊 播放当前", font_name=FONT_NAME, size_hint_x=0.33)
        next_btn = Button(text="下一个 ▶", font_name=FONT_NAME, size_hint_x=0.33)
        prev_btn.bind(on_press=self.prev_word)
        play_btn.bind(on_press=self.speak_current)
        next_btn.bind(on_press=self.next_word)
        nav.add_widget(prev_btn)
        nav.add_widget(play_btn)
        nav.add_widget(next_btn)
        root.add_widget(nav)

        if self.word_files:
            self.load_words(os.path.join(self.word_dir, self.word_files[0]))

        return root

    def refresh_wordlist(self, *args):
        self.word_files = [f for f in os.listdir(self.word_dir) if f.endswith('.json')]
        self.spinner.values = self.word_files
        if self.word_files and self.spinner.text not in self.word_files:
            self.spinner.text = self.word_files[0]

    def on_wordlist_change(self, spinner, text):
        if text != "无词库":
            self.load_words(os.path.join(self.word_dir, text))

    def load_words(self, path):
        words = load_word_list(path)
        if words:
            self.current_words = words
            self.current_index = 0
            self.update_display()
        else:
            self.show_popup("错误", "词库为空或格式错误")

    def update_display(self):
        if not self.current_words:
            self.word_label.text = "无单词"
            self.phonetic_label.text = ""
            self.pos_def_label.text = ""
            return
        w = self.current_words[self.current_index]
        self.word_label.text = w.get("word", "")
        self.phonetic_label.text = w.get("phonetic", "")  # 如 /'eibl/
        pos = w.get("pos", "")
        definition = w.get("definition", w.get("meaning", ""))
        self.pos_def_label.text = f"{pos} {definition}".strip()

    def _speak(self, text):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            for voice in voices:
                if any(kw in voice.name for kw in ['Chinese', 'Huihui', 'Yaoyao']) or 'zh' in voice.id.lower():
                    engine.setProperty('voice', voice.id)
                    break
            engine.setProperty('rate', 180)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"TTS 播放失败: {e}")
            self.show_popup("TTS 错误", str(e))

    def speak_current(self, *args):
        if not self.current_words:
            return
        w = self.current_words[self.current_index]
        text = w["word"]
        if self.play_meaning:
            meaning = w.get("definition") or w.get("meaning", "")
            if meaning:
                text += ". " + meaning
        self._speak(text)

    def test_tts(self, *args):
        self._speak("测试语音。Hello, WordListen.")

    def toggle_auto_play(self, checkbox, active):
        if active:
            self.start_auto_play()
        else:
            self.auto_play = False

    def toggle_play_meaning(self, checkbox, active):
        self.play_meaning = active

    # ========================
    # ✅ 自动播放同步逻辑（严格同步）
    # ========================
    def start_auto_play(self):
        self.auto_play = True
        Clock.schedule_once(self._auto_play_step, 0)

    def _auto_play_step(self, dt):
        if not self.auto_play or not self.current_words:
            self.auto_play = False
            Clock.schedule_once(lambda _: setattr(self.auto_check, 'active', False), 0)
            return

        w = self.current_words[self.current_index]
        text = w["word"]
        if self.play_meaning:
            meaning = w.get("definition") or w.get("meaning", "")
            if meaning:
                text += ". " + meaning

        def play_audio():
            self._speak(text)
            try:
                delay = max(0.5, float(self.interval_input.text))
            except ValueError:
                delay = 3.0
            Clock.schedule_once(self._schedule_next, delay)

        threading.Thread(target=play_audio, daemon=True).start()

    def _schedule_next(self, dt):
        if self.auto_play and self.current_words:
            self.next_word()
            Clock.schedule_once(self._auto_play_step, 0)

    def next_word(self, *args):
        if self.current_words:
            self.current_index = (self.current_index + 1) % len(self.current_words)
            self.update_display()

    def prev_word(self, *args):
        if self.current_words:
            self.current_index = (self.current_index - 1) % len(self.current_words)
            self.update_display()

    def show_popup(self, title, msg):
        popup = Popup(
            title=title,
            content=Label(text=msg, font_name=FONT_NAME, color=(0, 0, 0, 1)),
            size_hint=(0.8, 0.4),
            background_color=(0.9, 0.9, 0.9, 1)
        )
        popup.open()


if __name__ == '__main__':
    WordListenApp().run()
import tempfile
import os
import sys
import re
import subprocess
import random
import functools
import keyboard
from pynput import mouse
from PyQt5.QtWidgets import QWidget,QApplication
from PyQt5.QtGui import QPainter,QPixmap,QCursor,QFont,QFontMetrics
from PyQt5.QtMultimedia import QMediaPlayer,QMediaContent
from PyQt5.QtCore import QTimer,QPoint,QUrl,pyqtSignal,QObject,Qt
def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path=os.path.dirname(sys.executable)
    else:
        base_path=os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
PATH_Ratatoskr=os.path.dirname(__file__)
PATH_Rat=resource_path("Rat")
PATH_click_left=resource_path("click_left")
PATH_click_right=resource_path("click_right")
PATH_dialog_box=resource_path("dialogue_box")
PATH_espeak_ng=resource_path("eSpeak NG")
PATH_espeak_ng_exe=os.path.join(PATH_espeak_ng,"espeak-ng.exe")
EXIT_HOTKEY="ctrl+shift+alt+Q"
HIDE_HOTKEY="ctrl+shift+alt+H"
THINK_HOTKEY="ctrl+shift+alt+T"
SPEAK_PLAY_HOTKEY="ctrl+shift+alt+up"
SPEAK_PAUSE_HOTKEY="ctrl+shift+alt+down"
SPEAK_PREVIOUS_HOTKEY="ctrl+shift+alt+left"
SPEAK_NEXT_HOTKEY="ctrl+shift+alt+right"
SPEAK_SPEED_UP_HOTKEY="ctrl+alt+1+up"
SPEAK_SPEED_DOWN_HOTKEY="ctrl+alt+1+down"
SPEAK_PITCH_UP_HOTKEY="ctrl+alt+2+up"
SPEAK_PITCH_DOWN_HOTKEY="ctrl+alt+2+down"
SPEAK_AMPLITUDE_UP_HOTKEY="ctrl+alt+3+up"
SPEAK_AMPLITUDE_DOWN_HOTKEY="ctrl+alt+3+down"
SPEAK_WORDGAP_UP_HOTKEY="ctrl+alt+4+up"
SPEAK_WORDGAP_DOWN_HOTKEY="ctrl+alt+4+down"
SPEAK_CAPITAL_UP_HOTKEY="ctrl+alt+5+up"
SPEAK_CAPITAL_DOWN_HOTKEY="ctrl+alt+5+down"
SPEAK_VOICE_UP_HOTKEY="ctrl+alt+6+up"
SPEAK_VOICE_DOWN_HOTKEY="ctrl+alt+6+down"
cursor_pos=QCursor.pos()
class MouseSignal(QObject):
    click_signal=pyqtSignal(int,int,str)
    scroll_signal=pyqtSignal(int)
class keyboardsignal(QObject):
    think_signal=pyqtSignal()
    hide_signal=pyqtSignal()
    speak_play_signal=pyqtSignal()
    speak_pause_signal=pyqtSignal()
    speak_previous_signal=pyqtSignal()
    speak_next_signal=pyqtSignal()    
    speak_speed_up_signal=pyqtSignal()
    speak_speed_down_signal=pyqtSignal()
    speak_pitch_up_signal=pyqtSignal()
    speak_pitch_down_signal=pyqtSignal()    
    speak_amplitude_up_signal=pyqtSignal()
    speak_amplitude_down_signal=pyqtSignal()
    speak_wordgap_up_signal=pyqtSignal()
    speak_wordgap_down_signal=pyqtSignal()    
    speak_capital_up_signal=pyqtSignal()
    speak_capital_down_signal=pyqtSignal()
    speak_voice_up_signal=pyqtSignal()
    speak_voice_down_signal=pyqtSignal()
class SpeakStateMachine:
    def __init__(self):
        self.current_temp_text_file = None
        self.state="stopped"
        self.current_text=""
        self.sentences=[]
        self.current_sentence_index=0
        self.current_sentence_process=None
        self.speaker_timer=QTimer()
        self.speaker_timer.timeout.connect(self.finish_check_event)
        self.voice_parameters={
        "speed":175,
        "pitch":50,
        "amplitude":100,
        "wordgap":0,
        "capital":0,
        "voice":"cmn",
        }
        self.available_voices=self.load_available_voices()
        self.current_voice_index=0
        self.voice_parameters["voice"]=self.available_voices[self.current_voice_index]
        self.is_manual_change_voice=False
    def speak_event_receive(self,event):
        transitions={
        ("stopped","play"):"playing",
        ("playing","pause"):"paused",
        ("paused","play"):"playing",
        ("playing","stop"):"stopped",
        ("paused","stop"):"stopped",
        ("playing","end"):"stopped",
        }
        next_speak_state=transitions.get((self.state,event))
        if next_speak_state:
            self.state=next_speak_state
            self.speak_event_handle()
        else:
            return
    def speak_event_handle(self):
        if self.state=="playing":
            if self.current_sentence_index==0:
                self.play_init_event()
            else:
                self.play_next_sentence_event()
            pass
        elif self.state=="paused":
            self.pause_event()
            pass
        elif self.state=="stopped":
            self.stop_event()
            pass        
    def play_init_event(self):
        if not self.current_text:
            self.state="stopped"
            return
        self.sentences=self.split_sentences(self.current_text)
        self.current_sentence_index=0
        self.play_next_sentence_event()
    def play_next_sentence_event(self):
        if self.current_sentence_index>=len(self.sentences):
            self.stop_event()
            return
        current_sentence=self.sentences[self.current_sentence_index]
        if not current_sentence.strip():
            self.current_sentence_index+=1
            self.play_next_sentence_event()
            return
        try:
            if not self.is_manual_change_voice:
                has_zh=bool(re.search(r"[\u4e00-\u9fff]",current_sentence))
                self.voice_parameters["voice"]="cmn" if has_zh else "en-us"
            self.speak_sentence_from_file(current_sentence)
            self.speaker_timer.start(100)
        except Exception as e:
            self.current_sentence_index+=1
            self.play_next_sentence_event() 
    def pause_event(self):
        if self.current_sentence_process:
            try:
                self.current_sentence_process.kill()
                self.current_sentence_process.wait(timeout=1)
            except:
                pass
            self.current_sentence_process=None
        if self.current_temp_text_file:
            try:
                os.remove(self.current_temp_text_file)
            except:
                pass
            self.current_temp_text_file=None
        self.speaker_timer.stop()                   
    def stop_event(self):
        self.is_manual_change_voice=False 
        self.state="stopped"
        if self.current_sentence_process:
            try:
                self.current_sentence_process.kill()
                self.current_sentence_process.wait(timeout=1)
            except:
                pass
        if self.current_temp_text_file:
            try:
                os.remove(self.current_temp_text_file)
            except:
                pass
            self.current_temp_text_file=None
        self.current_sentence_process=None
        self.speaker_timer.stop()
        self.current_sentence_index=0
    def sentence_move(self,direction):
        if not self.sentences:
            return
        new_sentence_index=self.current_sentence_index+direction
        if 0<=new_sentence_index<len(self.sentences):
            if self.current_sentence_process:
                try:
                    self.current_sentence_process.kill()
                except:
                    pass
                self.current_sentence_process=None
            self.speaker_timer.stop()
            self.current_sentence_index=new_sentence_index
            if self.state=="playing":
                self.play_next_sentence_event()     
    def split_sentences(self,text):
        sentences=[]
        temp=""
        for t in text:
            temp+=t
            if t in "。！？.!?；;\n":
                sentences.append(temp)
                temp=""
        if temp:
            sentences.append(temp)
        return sentences
    def finish_check_event(self):
        if self.current_sentence_process is None:
            self.speaker_timer.stop()
            return
        poll=self.current_sentence_process.poll()
        if poll is not None:
            self.current_sentence_process=None
            if self.current_temp_text_file:
                try:
                    os.remove(self.current_temp_text_file)
                except:
                    pass
                self.current_temp_text_file=None
            self.current_sentence_index+=1
            self.speaker_timer.stop()
            if self.state=="playing":
                self.play_next_sentence_event()
            else:
                self.current_sentence_process = None
    def speak_sentence_from_file(self,current_sentence):
        fd,path=tempfile.mkstemp(suffix=".txt",text=True)
        os.close(fd)
        with open(path,"w",encoding="utf-8")as f:
            f.write(current_sentence)       
        command=[
            PATH_espeak_ng_exe,
            "--path",PATH_espeak_ng,
            "-s",str(self.voice_parameters["speed"]),
            "-p",str(self.voice_parameters["pitch"]),
            "-a",str(self.voice_parameters["amplitude"]),
            "-g",str(self.voice_parameters["wordgap"]),        
            "-v",str(self.voice_parameters["voice"]),
            "-b","1",
            "-f",path,
            ]
        if self.voice_parameters["capital"]>0:
            command[1:1]=["-k", str(self.voice_parameters["capital"])]
        creationflags=subprocess.CREATE_NO_WINDOW
        self.current_sentence_process=subprocess.Popen(command,creationflags=creationflags)
        self.current_temp_text_file=path
    def machine_button_panel(self,button,value):
        button_limits={
        "speed":(80,450),
        "pitch":(0,99),
        "amplitude":(0,200),
        "wordgap":(0,50),
        "capital":(0,20),
        }
        button_parameter=self.voice_parameters[button]
        min_button_parameter,max_button_parameter=button_limits[button]
        button_parameter_update=max(min_button_parameter,min(max_button_parameter,button_parameter+value))
        self.voice_parameters[button]=button_parameter_update
    def machine_knob_panel(self,knob,direction):
        if knob=="voice":
            if not self.available_voices:
                return          
            self.current_voice_index=(self.current_voice_index+direction)%len(self.available_voices)
            self.voice_parameters["voice"]=self.available_voices[self.current_voice_index]
            print(self.voice_parameters["voice"])
            self.is_manual_change_voice=True
    def load_available_voices(self):
        if not os.path.exists(PATH_espeak_ng_exe):
            return ["cmn","en-us","en-gb","en"]
        creationflags=subprocess.CREATE_NO_WINDOW
        try:
            result=subprocess.run(
                [PATH_espeak_ng_exe,"--path",PATH_espeak_ng,"--voices"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags
            )
        except Exception:
            return ["cmn", "en-us", "en-gb", "en"]
        voices=[]
        for line in result.stdout.splitlines():
            line=line.strip()
            if not line or line.startswith("Pty"):
                continue
            parts=line.split()
            if len(parts)>=4:
                language=parts[1]
                voice_name=parts[3]
                if voice_name.lower().endswith("mbrola-1"):
                    continue
                if "\\mb-" in line or " mb\\" in line:
                    continue
                voices.append(language)
        unique=[]
        for v in voices:
            if v not in unique:
                unique.append(v)
        preferred=["cmn","en-us","en-gb","en","yue","ja","ko"]
        ordered=[v for v in preferred if v in unique]
        ordered+=[v for v in unique if v not in ordered]
        return ordered or ["cmn", "en-us", "en-gb", "en"]
speak_state_machine=SpeakStateMachine()
class Ratatoskr(QWidget):
    def __init__(self):
        super().__init__()
        self.mouse_signals=MouseSignal()
        self.keyboard_signals=keyboardsignal()        
        self.set_hotkey()
        self.mouse_signals.scroll_signal.connect(self.mouse_scrolled_event)
        self.mouse_signals.click_signal.connect(self.mouse_clicked_event) 
        self.keyboard_signals.think_signal.connect(self.on_think_keyboard_press)    
        self.keyboard_signals.hide_signal.connect(self.hide_Ratatoskr)    
        self.keyboard_signals.speak_play_signal.connect(lambda:speak_state_machine.speak_event_receive("play"))
        self.keyboard_signals.speak_pause_signal.connect(lambda:speak_state_machine.speak_event_receive("pause"))
        self.keyboard_signals.speak_previous_signal.connect(lambda:speak_state_machine.sentence_move(-1))
        self.keyboard_signals.speak_next_signal.connect(lambda:speak_state_machine.sentence_move(1))
        self.keyboard_signals.speak_speed_up_signal.connect(lambda:speak_state_machine.machine_button_panel("speed",10))
        self.keyboard_signals.speak_speed_down_signal.connect(lambda:speak_state_machine.machine_button_panel("speed",-10))
        self.keyboard_signals.speak_pitch_up_signal.connect(lambda:speak_state_machine.machine_button_panel("pitch",10))
        self.keyboard_signals.speak_pitch_down_signal.connect(lambda:speak_state_machine.machine_button_panel("pitch",-10))
        self.keyboard_signals.speak_amplitude_up_signal.connect(lambda:speak_state_machine.machine_button_panel("amplitude",10))
        self.keyboard_signals.speak_amplitude_down_signal.connect(lambda:speak_state_machine.machine_button_panel("amplitude",-10))
        self.keyboard_signals.speak_wordgap_up_signal.connect(lambda:speak_state_machine.machine_button_panel("wordgap",10))
        self.keyboard_signals.speak_wordgap_down_signal.connect(lambda:speak_state_machine.machine_button_panel("wordgap",-10))
        self.keyboard_signals.speak_capital_up_signal.connect(lambda:speak_state_machine.machine_button_panel("capital",1))
        self.keyboard_signals.speak_capital_down_signal.connect(lambda:speak_state_machine.machine_button_panel("capital",-1))
        self.keyboard_signals.speak_voice_up_signal.connect(lambda:speak_state_machine.machine_knob_panel("voice",1))
        self.keyboard_signals.speak_voice_down_signal.connect(lambda:speak_state_machine.machine_knob_panel("voice",-1))
        self.Rat_frames=[]
        pngs=sorted([P for P in os.listdir(PATH_Rat)if P.lower().endswith(".png")])
        for P in pngs:
            pix=QPixmap(os.path.join(PATH_Rat,P))
            if not pix.isNull():
                self.Rat_frames.append(pix)
        self.box_frames=[]
        pngs=sorted([P for P in os.listdir(PATH_dialog_box)if P.lower().endswith(".png")])
        for P in pngs:
            pix=QPixmap(os.path.join(PATH_dialog_box,P))
            if not pix.isNull():
                self.box_frames.append(pix)
        if not self.Rat_frames or not self.box_frames:
            sys.exit() 
        self.first_Rat_frame=self.Rat_frames[0]
        self.current_Rat_frame=0
        self.current_box_frame=0
        self.box_state=True#Actually=Empty png
        self.clipboard_state=False
        self.resize(self.first_Rat_frame.width(),self.first_Rat_frame.height())
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.Rat_frame_timer=QTimer()
        self.Rat_frame_timer.timeout.connect(self.get_cursor_pos)
        self.Rat_frame_timer.start(35)
        self.box_frame_timer=QTimer()
        self.box_frame_timer.timeout.connect(self.thought_event)
        self.effects=[]
        self.players=[]     
        self.clipboard_text=""
        self.clipboard_pages=[]
        self.current_clipboard_page=0        
        self.listener=mouse.Listener(on_click=self._on_pynput_click,on_scroll=self._on_pynput_scroll)
        self.listener.daemon=True
        self.listener.start()
        self.show()
    def get_cursor_pos(self):
        global cursor_pos
        need_update=False
        new_cursor_pos=QCursor.pos()
        if cursor_pos!=new_cursor_pos:
            cursor_pos=new_cursor_pos
            self.move(cursor_pos.x()+30,cursor_pos.y()+30)
            need_update=True
            self.update()
        if self.effects:
            for effect in self.effects:
                effect["timer"]-=35
            old_len=len(self.effects)
            self.effects=[e for e in self.effects if e["timer"]>0]
            if self.effects or old_len!=len(self.effects):
                need_update=True
        if need_update:
            self.update()               
    def _on_pynput_scroll(self,x,y,dx,dy):
        self.mouse_signals.scroll_signal.emit(dy)
    def _on_pynput_click(self,x,y,button,pressed):
        if not pressed:
            return
        self.mouse_signals.click_signal.emit(x,y,button.name)
    def on_think_keyboard_press(self):
        if self.box_state:
            self.box_state=False
        else:
            self.box_state=True
        if not self.box_state:
            self.current_box_frame=0
        else:
            self.current_box_frame=len(self.box_frames)-1 if self.box_frames else 0
        self.box_frame_timer.start(70)
        self.update()
    def mouse_scrolled_event(self,dy):
        if dy>0:
            self.current_Rat_frame=(self.current_Rat_frame+1)%len(self.Rat_frames)
        else:
            self.current_Rat_frame=(self.current_Rat_frame-1)%len(self.Rat_frames)
        current_pix=self.Rat_frames[self.current_Rat_frame]
        if current_pix.size()!=self.size():
            self.resize(current_pix.size())
        self.update()
    def mouse_clicked_event(self,x,y,button_name):       
        effect_pos=QPoint(x,y)
        if button_name=="left":
            self.effect_create(PATH_click_left,effect_pos)
        elif button_name=="right":
            self.effect_create(PATH_click_right,effect_pos)
        elif button_name=="middle":
            self.clipboard_show()            
    def thought_event(self):
        if not self.box_frames:
            self.box_frame_timer.stop()
            return
        if not self.box_state:  
            if self.current_box_frame<len(self.box_frames)-1:
                self.current_box_frame+=1
                self.update()            
            else:
                self.box_frame_timer.stop()
        else:  
            if self.current_box_frame>0:
                self.current_box_frame-=1
                self.update()
            else:
                self.box_frame_timer.stop()
    def effect_create(self,path,pos):
        if not os.path.isdir(path):
            return
        files=os.listdir(path)
        pngs=[F for F in files if F.lower().endswith(".png")]
        mp3s=[F for F in files if F.lower().endswith(".mp3")]
        if pngs:
            random_png=random.choice(pngs)
            pix=QPixmap(os.path.join(path,random_png))
            if not pix.isNull():
                effect_pos=QPoint(random.randint(0,max(0,self.width()-pix.width())),random.randint(0,max(0,self.height()-pix.height())))
                self.effects.append({"pix":pix,"pos":effect_pos,"timer":500})
        if mp3s:
            random_mp3=random.choice(mp3s)
            self.make_sound(os.path.join(path,random_mp3))
    def make_sound(self,mp3_path):
        player=QMediaPlayer()
        player.setMedia(QMediaContent(QUrl.fromLocalFile(mp3_path)))
        player.play()
        def on_media_status_changed(status):
            if status==QMediaPlayer.EndOfMedia:
                if player in self.players:
                    self.players.remove(player)
                player.deleteLater()
        player.mediaStatusChanged.connect(on_media_status_changed)
        self.players.append(player)
    def clipboard_show(self):
        if self.width()<=0 or self.height()<=0:
            return
        if not self.clipboard_state:
            self.clipboard_text=QApplication.clipboard().text().strip()
            if not self.clipboard_text:
                return
            self.current_clipboard_page=0
            self.clipboard_pages_fill()
            if self.clipboard_pages:
                self.clipboard_state=True
                self.update()
        else:
            if self.current_clipboard_page+1<len(self.clipboard_pages):
                self.current_clipboard_page+=1
                self.sync_speak_text_to_current_page()
                self.update()
            else:
                speak_state_machine.stop_event()
                speak_state_machine.current_text=""
                speak_state_machine.sentences=[]
                self.clipboard_state=False
                self.clipboard_text=""
                self.clipboard_pages=[]
                self.current_clipboard_page=0
                self.update()
    def clipboard_pages_fill(self):
        if not self.clipboard_text:
            return
        font=QFont("Courier",6)
        fm=QFontMetrics(font)
        line_height=fm.lineSpacing()
        char_width=max(1,fm.horizontalAdvance('A'))
        margin=1*char_width
        max_page_width=self.width()-2*margin
        max_page_height=(self.height()/2)-1*margin
        if max_page_width<=0 or max_page_height<=0:
            return
        max_lines_per_page=int(max(1,max_page_height//line_height))
        lines=[]
        for raw_line in self.clipboard_text.split('\n'):
            line=raw_line.expandtabs(4)
            if not line:
                lines.append("")
                continue
            current_line=""
            for ch in line:
                next_line=current_line+ch
                if current_line and fm.horizontalAdvance(next_line)>max_page_width:
                    lines.append(current_line)
                    current_line=ch
                else:
                    current_line=next_line
            lines.append(current_line)
        self.clipboard_pages=[]
        for i in range(0,len(lines),max_lines_per_page):
            self.clipboard_pages.append('\n'.join(lines[i:i+max_lines_per_page]))
        if not self.clipboard_pages:
            self.clipboard_pages=['']
        if self.current_clipboard_page>=len(self.clipboard_pages):
            self.current_clipboard_page=len(self.clipboard_pages)-1
        self.sync_speak_text_to_current_page()
    def sync_speak_text_to_current_page(self):
        if self.clipboard_pages and 0 <= self.current_clipboard_page<len(self.clipboard_pages):
            speak_state_machine.stop_event()
            speak_state_machine.current_text=self.clipboard_pages[self.current_clipboard_page]
            speak_state_machine.sentences=[]
            speak_state_machine.current_sentence_index=0
    def paintEvent(self,event):
        painter=QPainter(self)
        Rat_pix=self.Rat_frames[self.current_Rat_frame]
        box_pix=self.box_frames[self.current_box_frame]
        painter.drawPixmap(0,0,Rat_pix)
        painter.drawPixmap(0,0,box_pix)
        for effect in self.effects:
            painter.drawPixmap(effect["pos"],effect["pix"])
        if self.clipboard_state and self.clipboard_pages:
            painter.setFont(QFont("Courier",6))
            fm=painter.fontMetrics()
            line_height=fm.lineSpacing()
            painter.setPen(Qt.black)
            char_width=fm.horizontalAdvance('A')
            margin=1*char_width
            baseline=margin+fm.ascent()
            text=self.clipboard_pages[self.current_clipboard_page]
            lines=text.split('\n')
            for line in lines:
                if baseline+fm.descent()>self.height()-margin:
                    break
                painter.drawText(margin,baseline,line)
                baseline+=line_height
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.clipboard_state:
            self.clipboard_pages_fill()
            if self.clipboard_pages:
                if self.current_clipboard_page>=len(self.clipboard_pages):
                    self.current_clipboard_page=len(self.clipboard_pages)-1
                self.update()
    def set_hotkey(self):
        keyboard.add_hotkey(SPEAK_PLAY_HOTKEY,self.SPEAK_PLAY_hotkey_event)
        keyboard.add_hotkey(SPEAK_PAUSE_HOTKEY,self.SPEAK_PAUSE_hotkey_event)
        keyboard.add_hotkey(SPEAK_PREVIOUS_HOTKEY,self.SPEAK_PREVIOUS_hotkey_event)
        keyboard.add_hotkey(SPEAK_NEXT_HOTKEY,self.SPEAK_NEXT_hotkey_event)
        keyboard.add_hotkey(SPEAK_SPEED_UP_HOTKEY,self.SPEAK_SPEED_UP_hotkey_event)
        keyboard.add_hotkey(SPEAK_SPEED_DOWN_HOTKEY,self.SPEAK_SPEED_DOWN_hotkey_event)
        keyboard.add_hotkey(SPEAK_PITCH_UP_HOTKEY,self.SPEAK_PITCH_UP_hotkey_event)
        keyboard.add_hotkey(SPEAK_PITCH_DOWN_HOTKEY,self.SPEAK_PITCH_DOWN_hotkey_event)
        keyboard.add_hotkey(SPEAK_AMPLITUDE_UP_HOTKEY,self.SPEAK_AMPLITUDE_UP_hotkey_event)
        keyboard.add_hotkey(SPEAK_AMPLITUDE_DOWN_HOTKEY,self.SPEAK_AMPLITUDE_DOWN_hotkey_event)
        keyboard.add_hotkey(SPEAK_WORDGAP_UP_HOTKEY,self.SPEAK_WORDGAP_UP_hotkey_event)
        keyboard.add_hotkey(SPEAK_WORDGAP_DOWN_HOTKEY,self.SPEAK_WORDGAP_DOWN_hotkey_event)
        keyboard.add_hotkey(SPEAK_CAPITAL_UP_HOTKEY,self.SPEAK_CAPITAL_UP_hotkey_event)
        keyboard.add_hotkey(SPEAK_CAPITAL_DOWN_HOTKEY,self.SPEAK_CAPITAL_DOWN_hotkey_event)
        keyboard.add_hotkey(SPEAK_VOICE_UP_HOTKEY,self.SPEAK_VOICE_UP_hotkey_event)
        keyboard.add_hotkey(SPEAK_VOICE_DOWN_HOTKEY,self.SPEAK_VOICE_DOWN_hotkey_event)
        keyboard.add_hotkey(EXIT_HOTKEY,self.EXIT_hotkey_event)
        keyboard.add_hotkey(HIDE_HOTKEY,functools.partial(self.HIDE_hotkey_event))
        keyboard.add_hotkey(THINK_HOTKEY,self.THINK_hotkey_event)
    def SPEAK_SPEED_UP_hotkey_event(self):
        self.keyboard_signals.speak_speed_up_signal.emit()
    def SPEAK_SPEED_DOWN_hotkey_event(self):
        self.keyboard_signals.speak_speed_down_signal.emit()
    def SPEAK_PITCH_UP_hotkey_event(self):
        self.keyboard_signals.speak_pitch_up_signal.emit()
    def SPEAK_PITCH_DOWN_hotkey_event(self):
        self.keyboard_signals.speak_pitch_down_signal.emit()
    def SPEAK_AMPLITUDE_UP_hotkey_event(self):
        self.keyboard_signals.speak_amplitude_up_signal.emit()
    def SPEAK_AMPLITUDE_DOWN_hotkey_event(self):
        self.keyboard_signals.speak_amplitude_down_signal.emit()
    def SPEAK_WORDGAP_UP_hotkey_event(self):
        self.keyboard_signals.speak_wordgap_up_signal.emit()
    def SPEAK_WORDGAP_DOWN_hotkey_event(self):
        self.keyboard_signals.speak_wordgap_down_signal.emit()
    def SPEAK_CAPITAL_UP_hotkey_event(self):
        self.keyboard_signals.speak_capital_up_signal.emit()
    def SPEAK_CAPITAL_DOWN_hotkey_event(self):
        self.keyboard_signals.speak_capital_down_signal.emit()
    def SPEAK_VOICE_UP_hotkey_event(self):
        self.keyboard_signals.speak_voice_up_signal.emit()
    def SPEAK_VOICE_DOWN_hotkey_event(self):
        self.keyboard_signals.speak_voice_down_signal.emit()
    def SPEAK_PLAY_hotkey_event(self):
        self.keyboard_signals.speak_play_signal.emit()
    def SPEAK_PAUSE_hotkey_event(self):
        self.keyboard_signals.speak_pause_signal.emit()
    def SPEAK_PREVIOUS_hotkey_event(self):
        self.keyboard_signals.speak_previous_signal.emit()
    def SPEAK_NEXT_hotkey_event(self):
        self.keyboard_signals.speak_next_signal.emit()
    def THINK_hotkey_event(self):
        self.keyboard_signals.think_signal.emit()
    def HIDE_hotkey_event(self):
        self.keyboard_signals.hide_signal.emit()
    def EXIT_hotkey_event(self):
        QTimer.singleShot(0,self.close_the_window)
    def hide_Ratatoskr(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()          
    def close_the_window(self):
        speak_state_machine.stop_event()
        if hasattr(self,"listener"):
            self.listener.stop()
        keyboard.unhook_all_hotkeys()
        for player in self.players:
            player.stop()
            player.deleteLater()
        self.players.clear()
        QApplication.quit()
if __name__=="__main__":
    app=QApplication(sys.argv)
    ratatoskr=Ratatoskr()
    sys.exit(app.exec_())




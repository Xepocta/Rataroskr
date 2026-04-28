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
EXIT_HOTKEY="ctrl+shift+alt+Q"
HIDE_HOTKEY="ctrl+shift+alt+H"
THINK_HOTKEY="ctrl+shift+alt+T"
SPEAK_PLAY_HOTKEY="ctrl+shift+alt+up"
SPEAK_PAUSE_HOTKEY="ctrl+shift+alt+down"
SPEAK_PREVIOUS_HOTKEY="ctrl+shift+alt+left"
SPEAK_NEXT_HOTKEY="ctrl+shift+alt+right"
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
            has_zh=bool(re.search(r"[\u4e00-\u9fff]",current_sentence))
            es_voice="cmn" if has_zh else "en-us"
            self.speak_sentence_from_file(current_sentence, es_voice)
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
    def sentence_move(self,steps):
        if not self.sentences:
            return
        new_sentence_index=self.current_sentence_index+steps
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
    def speak_sentence_from_file(self,current_sentence,es_voice):
        fd,path=tempfile.mkstemp(suffix=".txt",text=True)
        os.close(fd)
        with open(path,"w",encoding="utf-8")as f:
            f.write(current_sentence)
        creationflags=subprocess.CREATE_NO_WINDOW
        self.current_sentence_process=subprocess.Popen(["espeak-ng","-v",es_voice,"-b","1","-f",path],creationflags=creationflags)
        self.current_temp_text_file=path
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
        keyboard.add_hotkey(SPEAK_PLAY_HOTKEY,self.SPEAKER_PLAY_hotkey_event)
        keyboard.add_hotkey(SPEAK_PAUSE_HOTKEY,self.SPEAKER_PAUSE_hotkey_event)
        keyboard.add_hotkey(SPEAK_PREVIOUS_HOTKEY,self.SPEAKER_PREVIOUS_hotkey_event)
        keyboard.add_hotkey(SPEAK_NEXT_HOTKEY,self.SPEAKER_NEXT_hotkey_event)
        keyboard.add_hotkey(EXIT_HOTKEY,self.EXIT_hotkey_event)
        keyboard.add_hotkey(HIDE_HOTKEY,functools.partial(self.HIDE_hotkey_event))
        keyboard.add_hotkey(THINK_HOTKEY,self.THINK_hotkey_event)
    def SPEAKER_PLAY_hotkey_event(self):
        self.keyboard_signals.speak_play_signal.emit()
    def SPEAKER_PAUSE_hotkey_event(self):
        self.keyboard_signals.speak_pause_signal.emit()
    def SPEAKER_PREVIOUS_hotkey_event(self):
        self.keyboard_signals.speak_previous_signal.emit()
    def SPEAKER_NEXT_hotkey_event(self):
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




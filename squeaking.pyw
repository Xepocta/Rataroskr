import sys
import os
import random
import winreg
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QUrl, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QPixmap, QCursor, QFont, QFontMetrics
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from pynput import mouse
import keyboard
import functools

class MouseSignal(QObject):
    click_SiGnAl=pyqtSignal(int,int,str)
    scroll_SiGnAl=pyqtSignal(int)
class Ratatoskr(QWidget):
    def __init__(self,RAT_DiRnAmE):
        super().__init__()
        self.project_PaTh=os.path.dirname(__file__)
        RAT_PaTh=os.path.join(self.project_PaTh,RAT_DiRnAmE)
        self.exit_hotkey_SeT()        
        self.FrAmes=[]
        PnGs=sorted([P for P in os.listdir(RAT_PaTh)if P.lower().endswith(".png")])
        for P in PnGs:
            PiX=QPixmap(os.path.join(RAT_PaTh,P))
            if not PiX.isNull():
                self.FrAmes.append(PiX)
        if not self.FrAmes:
            sys.exit()
        self.current_FrAmE=0
        first_FrAmE=self.FrAmes[0]
        self.EfFeCts=[]
        self.SoUnDs=[] 
        self.PlAyErs=[]
        self.clipboard_TeXt=""
        self.clipboard_InDeX=0
        self.clipboard_CaPaCiTyPage=0
        self.clipboard_AcTiVe=False
        self.clipboard_PaGes=[]
        self.clipboard_CTPaGe=0
        self.resize(first_FrAmE.width(),first_FrAmE.height())
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.mouse_PoS=QCursor.pos()
        self.cache_PiXmApS={}
        self.cache_MeDiA={}        
        self.mouse_SiGnAls=MouseSignal()
        self.mouse_SiGnAls.scroll_SiGnAl.connect(self.mouse_scrolled_signal_ReCeIvE)
        self.mouse_SiGnAls.click_SiGnAl.connect(self.mouse_clicked_SIGNAL_ReCeIvE)
        self.LiStEnR=mouse.Listener(on_click=self._on_pynput_click,on_scroll=self._on_pynput_scroll)
        self.LiStEnR.daemon=True
        self.LiStEnR.start()
        self.TiMeR=QTimer()
        self.TiMeR.timeout.connect(self.RAT_pos_UpDaTe)
        self.TiMeR.start(35)
        self.show()
    def _on_pynput_scroll(self,x,y,dx,dy):
        self.mouse_SiGnAls.scroll_SiGnAl.emit(dy)
    def _on_pynput_click(self,x,y,button,pressed):
        if not pressed:
            return
        self.mouse_SiGnAls.click_SiGnAl.emit(x,y,button.name)
    def mouse_clicked_SIGNAL_ReCeIvE(self,x,y,button_name):
        PoS=QPoint(x,y)
        if button_name=="left":
            self.effects_mp3s_CrEaTe("ClickLeft",PoS)
        elif button_name=="right":
            self.effects_mp3s_CrEaTe("ClickRight",PoS)
        elif button_name=="middle":
            self.clipboard_ShOw()
    def mouse_scrolled_signal_ReCeIvE(self,dy):
        if dy>0:
            self.current_FrAmE=(self.current_FrAmE+1)%(len(self.FrAmes))
        else:
            self.current_FrAmE=(self.current_FrAmE-1)%(len(self.FrAmes))
        new_PiX=self.FrAmes[self.current_FrAmE]
        if new_PiX.size()!=self.size():
            self.resize(new_PiX.size())
        self.update()     
    def cached_pixmap_GeT(self,DiRnAmE,FiLeNaMe):
        PaTh=os.path.join(self.project_PaTh,DiRnAmE,FiLeNaMe)
        if PaTh not in self.cache_PiXmApS:
            PiX=QPixmap(PaTh)
            if not PiX.isNull():
                self.cache_PiXmApS[PaTh]=PiX
            else:
                return None
        return self.cache_PiXmApS[PaTh]
    def cached_media_GeT(self,DiRnAmE,FiLeNaMe):
        PaTh=os.path.join(self.project_PaTh,DiRnAmE,FiLeNaMe)
        if PaTh not in self.cache_MeDiA:
            UrL=QUrl.fromLocalFile(PaTh)
            self.cache_MeDiA[PaTh]=QMediaContent(UrL)
        return self.cache_MeDiA[PaTh]
    def effects_mp3s_CrEaTe(self,DiRnAmE,Pos):
        PaTh=os.path.join(self.project_PaTh,DiRnAmE)
        if not os.path.isdir(PaTh):
            return
        FiLes=os.listdir(PaTh)
        PnGs=[F for F in FiLes if F.lower().endswith(".png")]
        Mp3s=[F for F in FiLes if F.lower().endswith(".mp3")]
        if PnGs:
            png_NaMe=random.choice(PnGs)
            PiX=self.cached_pixmap_GeT(DiRnAmE,png_NaMe)#
            if PiX:
                effect_PoS=QPoint(random.randint(0,max(0,self.width()-PiX.width())),random.randint(0,max(0,self.height()-PiX.height())))
                self.EfFeCts.append({'pix':PiX,'pos':effect_PoS,'timer':500})
        if Mp3s:
            mp3_NaMe=random.choice(Mp3s)
            self.sound_PlAy(DiRnAmE,mp3_NaMe)
    def sound_PlAy(self,DiRnAmE,mp3_NaMe):
        MeDiA=self.cached_media_GeT(DiRnAmE,mp3_NaMe)
        PlAyEr=QMediaPlayer()
        PlAyEr.setMedia(MeDiA)
        PlAyEr.play()
        def on_media_status_changed(status):
            if status==QMediaPlayer.EndOfMedia:
                if PlAyEr in self.PlAyErs:
                    self.PlAyErs.remove(PlAyEr)
                PlAyEr.deleteLater()
        PlAyEr.mediaStatusChanged.connect(on_media_status_changed)
        self.PlAyErs.append(PlAyEr)
    def RAT_pos_UpDaTe(self):
        new_PoS=QCursor.pos()
        if new_PoS!=self.mouse_PoS:
            self.mouse_PoS=new_PoS
            x=new_PoS.x()+12
            y=new_PoS.y()+20
            self.move(x,y)
            self.update()
        for EfFeCt in self.EfFeCts:
            EfFeCt['timer']-=35
        self.EfFeCts=[E for E in self.EfFeCts if E['timer']>0]
    def paintEvent(self,e):
        PaInTeR=QPainter(self)
        PiX=self.FrAmes[self.current_FrAmE]
        PaInTeR.drawPixmap(0,0,PiX)
        for EfFeCt in self.EfFeCts:#
            PaInTeR.drawPixmap(EfFeCt['pos'],EfFeCt['pix'])
        if self.clipboard_AcTiVe and self.clipboard_PaGes:
            PaInTeR.setFont(QFont("Courier",12))
            PaInTeR.setPen(Qt.black)
            MaRgIn=6
            fm=PaInTeR.fontMetrics()
            line_height=fm.lineSpacing()
            baseline=MaRgIn+fm.ascent()
            text=self.clipboard_PaGes[self.clipboard_CTPaGe]
            lines=text.split('\n')
            for line in lines:
                if baseline+fm.descent()>self.height()-MaRgIn:
                    break
                PaInTeR.drawText(MaRgIn,baseline,line)
                baseline+=line_height
    def clipboard_pages_UpDaTe(self):
        if not self.clipboard_TeXt:
            return
        font=QFont("Courier",12)
        fm=QFontMetrics(font)
        margin=6
        max_width=self.width()-2*margin
        max_height=self.height()-2*margin
        if max_width<=0 or max_height<=0:
            return
        char_width=fm.horizontalAdvance('A')
        line_height=fm.lineSpacing()
        max_chars_per_line=max(1,max_width//char_width)
        max_lines_per_page=max(1,max_height//line_height)
        lines=[]
        for line in self.clipboard_TeXt.split('\n'):
            while len(line)>max_chars_per_line:
                lines.append(line[:max_chars_per_line])
                line=line[max_chars_per_line:]
            lines.append(line)
        self.clipboard_PaGes=[]
        for i in range(0,len(lines),max_lines_per_page):
            self.clipboard_PaGes.append('\n'.join(lines[i:i+max_lines_per_page]))
        if not self.clipboard_PaGes:
            self.clipboard_PaGes=['']
        if self.clipboard_CTPaGe>=len(self.clipboard_PaGes):
            self.clipboard_CTPaGe=len(self.clipboard_PaGes)-1
    def clipboard_ShOw(self):
        if not self.clipboard_AcTiVe:
            TeXt=QApplication.clipboard().text().strip()
            if not TeXt:
                return
            self.clipboard_TeXt=TeXt
            self.clipboard_CTPaGe=0
            self.clipboard_pages_UpDaTe()
            if self.clipboard_PaGes:
                self.clipboard_AcTiVe=True
                self.update()
        else:
            if self.clipboard_CTPaGe+1<len(self.clipboard_PaGes):
                self.clipboard_CTPaGe+=1
                self.update()
            else:
                self.clipboard_AcTiVe=False
                self.clipboard_TeXt=""
                self.clipboard_PaGes=[]
                self.clipboard_CTPaGe=0
                self.update()
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if self.clipboard_AcTiVe:
            self.clipboard_pages_UpDaTe()
            if self.clipboard_PaGes:
                if self.clipboard_CTPaGe>=len(self.clipboard_PaGes):
                    self.clipboard_CTPaGe=len(self.clipboard_PaGes)-1
                self.update()
    def exit_hotkey_SeT(self):
        try:
            keyboard.add_hotkey('ctrl+shift+q',functools.partial(self.sk_exit_timer_StArT))
        except Exception as e:
            pass
    def resources_ClEnUp(self):
        if hasattr(self,"LiStEnR"):
            self.LiStEnR.stop()
        for PlAyEr in self.PlAyErs:
            PlAyEr.stop()
            PlAyEr.deleteLater()
        self.PlAyErs.clear()
    def sk_exit_timer_StArT(self):
        QTimer.singleShot(0,self.SK_ExIt)		
    def SK_ExIt(self):
        self.resources_ClEnUp()
        QApplication.quit()
    def closeEvent(self, e):
        self.resources_ClEnUp()
        super().closeEvent(e) 

if __name__=="__main__":
    app=QApplication(sys.argv)
    ratatoskr=Ratatoskr("Rat")
    sys.exit(app.exec())

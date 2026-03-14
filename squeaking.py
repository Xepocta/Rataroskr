import sys 
import os
import random
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QUrl
from PyQt5.QtGui import QPainter, QPixmap, QCursor, QFont
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from pynput import mouse

class Ratatoskr(QWidget):
    def __init__(self,dirname__Rat):
        super().__init__()
        self.basepath__thisproject=os.path.dirname(__file__)
        self.frames=[]
        self.path__Rat=os.path.join(self.basepath__thisproject,dirname__Rat)
        pngs=sorted([p for p in os.listdir(self.path__Rat) if p.lower().endswith(".png")])
        for p in pngs:
            pix=QPixmap(os.path.join(self.path__Rat,p))
            if not pix.isNull():
                self.frames.append(pix)
        if not self.frames:
            sys.exit()
        self.frame__current=0
        frame__first=self.frames[0]
        self.resize(frame__first.width(),frame__first.height())
        self.setWindowFlags(Qt.FramelessWindowHint|Qt.WindowStaysOnTopHint|Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.pos__mouse=QCursor.pos()
        self.text__clipboard=""
        self.index__clipboard=0
        self.capacityPage__clipboard=0
        self.active__clipboard=False
        self.effects=[]
        self.players=[]
        self.sounds=[]
        self.timer=QTimer()
        self.timer.timeout.connect(self.update__Ratposition)
        self.timer.start(16)
        self.pos__mouse=QCursor.pos()
        self.show()
        self.process__mouseEvent()
    def process__mouseEvent(self):
        def event__scroll(_,__,___,delta):
            if delta>0:
                self.frame__current=(self.frame__current+1)%len(self.frames)
            else:
                self.frame__current=(self.frame__current-1)%len(self.frames)
        def event__click(x,y,button,pressed):
            if not pressed:
                return
            pos=QPoint(x,y)
            if button==mouse.Button.left:
                self.create_effect("ClickLeft",pos)
            elif button==mouse.Button.right:
                self.create_effect("ClickRight",pos)
            elif button==mouse.Button.middle:
                self.show__clipboard()
        Listener__jump=mouse.Listener(on_click=event__click,on_scroll=event__scroll)
        Listener__jump.daemon=True
        Listener__jump.start()
    def update__Ratposition(self):
        self.pos__mouse=QCursor.pos()
        pix=self.frames[self.frame__current]
        x=self.pos__mouse.x()+12
        y=self.pos__mouse.y()+20
        self.move(x,y)
        if self.width()!=pix.width()or self.height()!=pix.height():
            self.resize(pix.width(),pix.height())
        for effect in self.effects[:]:
            effect['timer']-=16
            if effect['timer']<=0:
                self.effects.remove(effect)
        self.update()
    def paintEvent(self,e):
        painter=QPainter(self)
        pix=self.frames[self.frame__current]
        painter.drawPixmap(0,0,pix)
        for effect in self.effects:
            painter.drawPixmap(effect['pos'],effect['pix'])
        if self.active__clipboard and self.text__clipboard:
            painter.setFont(QFont("Courier",12))
            painter.setPen(Qt.black)
            margin=6
            height__line=14
            width__char=8
            width__area=self.width()-2*margin
            height__area=self.height()//2-2*margin
            maxchars_perline=width__area//width__char
            maxlines=height__area//height__line
            self.capacityPage__clipboard=maxchars_perline*maxlines
            text__show=self.text__clipboard[self.index__clipboard:self.index__clipboard+self.capacityPage__clipboard]
            x,y=margin,margin
            text__lineshow=""
            for char in text__show:
                text__lineshow+=char
                if len(text__lineshow)>=maxchars_perline or char in '\n\r':
                    painter.drawText(x,y+height__line-2,text__lineshow.rstrip())
                    text__lineshow=""
                    y+=height__line
                    if y+height__line>height__area:
                        break
            if text__lineshow:
                painter.drawText(x,y+height__line-2,text__lineshow)
    def create_effect(self,dirname__click,pos):
        path=os.path.join(self.basepath__thisproject,dirname__click)
        if not os.path.isdir(path):
            return
        pngs=[f for f in os.listdir(path) if f.lower().endswith(".png")]
        if not pngs:
            return
        pngd=random.choice(pngs)
        pix=QPixmap(os.path.join(path,pngd))
        pos__effect=QPoint(random.randint(0,max(0,self.width()-pix.width())),random.randint(0, max(0, self.height()-pix.height())))
        self.effects.append({'pix':pix,'pos':pos__effect,'timer':500})
        mp3s=[f for f in os.listdir(path) if f.lower().endswith(".mp3")]
        if mp3s:
            self.play__sound(os.path.join(path,random.choice(mp3s)))
    def play__sound(self,sound):
        player=QMediaPlayer()
        player.setMedia(QMediaContent(QUrl.fromLocalFile(sound)))
        def cleanup(status):
            if status==QMediaPlayer.EndOfMedia:
                if player in self.players:
                    self.players.remove(player)
                player.deleteLater()
        player.mediaStatusChanged.connect(cleanup)
        player.play()
        self.players.append(player)
    def show__clipboard(self):
        text=QApplication.clipboard().text().strip()
        if not text:
            return
        if self.active__clipboard:
            self.index__clipboard+=self.capacityPage__clipboard
            if self.index__clipboard>=len(self.text__clipboard):
                self.active__clipboard=False
                self.index__clipboard=0
                self.text__clipboard=""
            self.update()
            return
        self.text__clipboard=text
        self.index__clipboard=0
        self.active__clipboard=True
        self.update()
if __name__=="__main__":
    app=QApplication(sys.argv)
    ratatoskr=Ratatoskr("Rat")
    sys.exit(app.exec_())

"""Interface gráfica 2D sobreposta ao OpenGL (sem biblioteca de UI externa)."""
import pygame
from .mission import STAGES,PERIOD

class MissionHUD:
    def __init__(self,width,height):
        self.w,self.h=width,height
        self.x=width/1280
        self.y=height/720
        self.surface=pygame.Surface((width,height),pygame.SRCALPHA,32)
        self.fonts={}
        for name,size,bold in [('hero',35,True),('heading',19,True),('large',25,True),
                                ('normal',15,False),('tiny',12,False),('micro',10,True)]:
            f=pygame.font.SysFont('dejavusansmono',max(10,round(size*self.y)),bold=bold)
            self.fonts[name]=f
        self.cyan=(85,226,239)
        self.amber=(242,183,98)
        self.white=(236,242,241)
        self.muted=(153,187,191)
    def _p(self,x,y):return int(x*self.x),int(y*self.y)
    def _rect(self,s,color,x,y,w,h,border=0,r=0):
        pygame.draw.rect(s,color,pygame.Rect(*self._p(x,y),*self._p(w,h)),
                         max(0,round(border*self.x)),border_radius=round(r*self.x))
    def _line(self,s,color,p0,p1,width=1):
        pygame.draw.line(s,color,self._p(*p0),self._p(*p1),max(1,int(width*self.x)))
    def _text(self,s,value,x,y,kind='normal',color=None):
        col=color or self.white
        font=self.fonts[kind]
        txt=font.render(str(value),True,col)
        s.blit(txt,self._p(x,y))
        return txt.get_width()/self.x
    def _panel(self,s,x,y,w,h):
        self._rect(s,(9,24,35,184),x,y,w,h,r=9)
        self._rect(s,(102,171,187,90),x,y,w,h,border=1,r=9)
        self._rect(s,(*self.cyan,215),x,y,3,29,r=2)
    def draw(self,pose,elapsed,fps,paused,follow):
        s=self.surface
        s.fill((0,0,0,0))
        # Moldura/retícula de gravação
        for x,dx in [(28,1),(1252,-1)]:
            for y,dy in [(26,1),(694,-1)]:
                self._line(s,(136,188,196,140),(x,y),(x+dx*21,y),2)
                self._line(s,(136,188,196,140),(x,y),(x,y+dy*21),2)
        # Título e indicador de missão ativa
        self._rect(s,(13,29,41,191),44,42,340,101,r=11)
        self._rect(s,(*self.amber,255),62,60,5,54,r=2)
        self._text(s,'MARS / 09',80,51,'micro',self.amber)
        self._text(s,'MISSÃO MARTE',79,67,'hero')
        self._text(s,'ROVER  +  DRONE  /  EXPEDIÇÃO ARES',82,112,'tiny',self.muted)
        # Faixa superior direita
        self._rect(s,(12,29,40,183),888,42,345,78,r=10)
        self._text(s,'SINAL OPERACIONAL',906,54,'micro',self.muted)
        self._text(s,'●',905,82,'heading',self.cyan)
        self._text(s,'TRANSMISSÃO ATIVA',936,83,'normal',self.white)
        self._text(s,f'{fps:02.0f} FPS',1133,83,'tiny',self.muted)
        # Cartão do estágio
        self._panel(s,44,166,350,137)
        self._text(s,'ETAPA ATUAL  /  {:02d}'.format(pose.stage_index+1),61,180,'tiny',self.amber)
        self._text(s,pose.stage_name,61,202,'large',self.white)
        self._text(s,pose.status,61,242,'tiny',self.muted)
        self._rect(s,(72,112,126,112),61,277,314,4,r=2)
        self._rect(s,(*self.cyan,240),61,277,314*pose.stage_progress,4,r=2)
        # Dados da missão
        self._panel(s,44,317,250,133)
        self._text(s,'TELEMETRIA / ROVER',61,331,'tiny',self.amber)
        x,z=pose.rover_position[0],pose.rover_position[2]
        self._text(s,'POS X',61,363,'tiny',self.muted)
        self._text(s,f'{x:+06.2f}',135,359,'normal')
        self._text(s,'POS Z',61,390,'tiny',self.muted)
        self._text(s,f'{z:+06.2f}',135,386,'normal')
        self._text(s,'RODAS: 6 / 6',61,422,'tiny',self.cyan)
        # Cartão drone à direita
        self._panel(s,1015,169,220,132)
        self._text(s,'UAV / SCOUT-04',1032,184,'tiny',self.amber)
        self._text(s,'ALTITUDE',1032,210,'tiny',self.muted)
        self._text(s,f'{pose.drone_position[1]:04.1f} m',1030,230,'large')
        self._text(s,'SCAN ATIVO' if pose.scan_strength>.1 else 'AGUARDANDO SINAL',1032,272,'tiny',self.cyan)
        self._panel(s,1015,313,220,102)
        self._text(s,'DADOS DA MISSÃO',1032,328,'tiny',self.amber)
        self._text(s,'CICLO',1032,354,'tiny',self.muted)
        self._text(s,f'{pose.cycle_number:02d}',1152,350,'normal',self.white)
        self._text(s,'TEMPO',1032,378,'tiny',self.muted)
        self._text(s,f'{int(elapsed//60):02d}:{int(elapsed%60):02d}',1148,373,'normal',self.white)
        # indicador de alvo no espaço da tela (estilo HUD, não posição 3D real)
        self._line(s,(*self.cyan,90),(628,365),(649,365),2)
        self._line(s,(*self.cyan,90),(638,354),(638,375),2)
        self._rect(s,(*self.cyan,105),631,358,14,14,border=1)
        # Faixa de linha temporal e controles
        self._rect(s,(9,24,35,210),44,563,1191,120,r=11)
        self._text(s,'SEQUÊNCIA DE OPERAÇÃO',61,578,'tiny',self.amber)
        self._text(s,f'{pose.overall_progress*100:05.1f} %',1131,577,'tiny',self.cyan)
        beginning=0
        total_width=1157
        for i,(_,duration,_) in enumerate(STAGES):
            start=beginning/PERIOD*total_width
            width=(duration/PERIOD)*total_width
            color=(*self.cyan,225) if i<pose.stage_index else ((232,172,91,248) if i==pose.stage_index else (66,91,105,175))
            self._rect(s,color,61+start,611,max(2,width-4),9,r=2)
            beginning+=duration
        self._text(s,'01  INÍCIO',61,629,'tiny',self.muted)
        self._text(s,'04  INSPEÇÃO',367,629,'tiny',self.muted)
        self._text(s,'07  EXPLORAÇÃO',728,629,'tiny',self.muted)
        self._text(s,'08  FIM',1100,629,'tiny',self.muted)
        self._line(s,(95,136,146,105),(61,652),(1217,652))
        self._text(s,'WASD MOVER   SETAS ORBITAR   Q/E ZOOM   R/F ALTURA',61,661,'micro',self.white)
        self._text(s,'P PAUSAR   C SEGUIR   H HUD   1-3 CÂMERAS   F9 FOTO',645,661,'micro',self.muted)
        # Overlay de pausa centralizado
        if paused:
            self._rect(s,(3,9,15,125),0,0,1280,720)
            self._rect(s,(12,28,39,225),432,269,416,160,r=14)
            self._rect(s,(*self.cyan,145),432,269,416,160,border=1,r=14)
            self._text(s,'⏸',615,287,'heading',self.amber)
            self._text(s,'ANIMAÇÃO PAUSADA',478,323,'large',self.white)
            self._text(s,'PRESSIONE P PARA CONTINUAR',494,382,'tiny',self.muted)
        if follow:
            self._rect(s,(13,35,48,185),515,43,264,29,r=7)
            self._text(s,'● CÂMERA SEGUINDO ROVER',528,49,'micro',self.cyan)
        return s

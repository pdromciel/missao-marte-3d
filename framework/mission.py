"""Máquina de estados determinística da missão. Integração verdadeira entre os 2 atores.
O drone só investiga depois que o rover para; o rover só retoma após retorno.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
from .math3d import lerp,ease_in_out,smoothstep,angle_for_motion

STAGES=[
    ('INICIALIZANDO',2.0,'Sistemas online. Preparando exploração.'),
    ('EXPLORANDO',9.0,'Rover percorrendo o setor Alpha.'),
    ('PONTO DETECTADO',1.7,'Rover imobilizado. Drone autorizado.'),
    ('INSPECIONANDO',8.0,'Drone analisando formação rochosa.'),
    ('RETORNANDO',4.5,'Drone retornando à formação.'),
    ('ROTA LIBERADA',1.5,'Análise concluída. Nova rota calculada.'),
    ('AVANÇANDO',9.0,'Rover retoma exploração em segurança.'),
    ('MISSÃO CONCLUÍDA',3.0,'Setor analisado. Reiniciando sequência.'),
]
PERIOD=sum(x[1] for x in STAGES)

@dataclass
class MissionPose:
    stage_index:int
    stage_name:str
    status:str
    stage_progress:float
    overall_progress:float
    rover_position:np.ndarray
    rover_yaw:float
    drone_position:np.ndarray
    drone_yaw:float
    rover_travel:float
    scan_strength:float
    cycle_number:int

class Mission:
    def __init__(self):
        self.start=np.array((-10.,7.),dtype=np.float32)
        self.stop=np.array((-3.0,1.4),dtype=np.float32)
        self.turn=np.array((1.25,3.3),dtype=np.float32)
        self.finish=np.array((9.0,-4.8),dtype=np.float32)
        self.target=np.array((1.65,-2.2),dtype=np.float32)
        self.heading_start=angle_for_motion(*(self.stop-self.start))
        self.heading_mid=angle_for_motion(*(self.turn-self.stop))
        self.heading_finish=angle_for_motion(*(self.finish-self.turn))
        self.first_distance=float(np.linalg.norm(self.stop-self.start))
        self.second_distance=float(np.linalg.norm(self.turn-self.stop)+np.linalg.norm(self.finish-self.turn))
    def sample(self,time_seconds:float):
        t=max(0.,float(time_seconds));cycle=int(t/PERIOD)
        t%=PERIOD
        idx=0
        for i,(_,length,_) in enumerate(STAGES):
            if t<length or i==len(STAGES)-1:
                idx=i;break
            t-=length
        label,duration,status=STAGES[idx]
        u=t/duration
        travelled=0.
        rover=self.start.copy();heading=self.heading_start
        if idx==0:
            rover=self.start.copy()
        elif idx==1:
            f=ease_in_out(u)
            rover=lerp(self.start,self.stop,f)
            travelled=self.first_distance*f
        elif idx<6:
            rover=self.stop.copy();travelled=self.first_distance
        elif idx==6:
            f=ease_in_out(u)
            if f<.43:
                q=ease_in_out(f/.43)
                rover=lerp(self.stop,self.turn,q)
                heading=self.heading_mid
                travelled=self.first_distance+float(np.linalg.norm(self.turn-self.stop))*q
            else:
                q=ease_in_out((f-.43)/.57)
                rover=lerp(self.turn,self.finish,q)
                heading=self.heading_finish
                travelled=self.first_distance+float(np.linalg.norm(self.turn-self.stop))+float(np.linalg.norm(self.finish-self.turn))*q
        else:
            rover=self.finish.copy();heading=self.heading_finish
            travelled=self.first_distance+self.second_distance
        if idx==6:
            # giro mais orgânico ao passar no waypoint
            a=smoothstep(min(u/.35,1.))
            if u<.35:
                heading=self.heading_start+(self.heading_mid-self.heading_start)*a
            elif u<.58:
                heading=self.heading_mid+(self.heading_finish-self.heading_mid)*smoothstep((u-.35)/.23)
            else:
                heading=self.heading_finish
        follow=np.array((rover[0]-.7,3.7,rover[1]+1.25),dtype=np.float32)
        drone=follow.copy();drone_yaw=heading
        scan=0.
        if idx==0:
            drone[1]=.8+2.9*ease_in_out(u)
        elif idx==2:
            drone[1]+=.12*math.sin(u*math.pi)
        elif idx==3:
            # primeira aproximação, depois órbita de inspeção.
            anchor=np.array((self.target[0],2.35,self.target[1]),dtype=np.float32)
            if u<.38:
                p=ease_in_out(u/.38)
                drone=lerp(follow,anchor+np.array((1.1,0.8,.3),dtype=np.float32),p)
            else:
                q=(u-.38)/.62
                theta=math.pi*.12+q*math.pi*1.7
                drone=anchor+np.array((1.35*math.cos(theta),.35*math.sin(q*math.pi*2),1.35*math.sin(theta)),dtype=np.float32)
                scan=min(1.,smoothstep(q/.15))*min(1.,smoothstep((1.-q)/.13))
            drone_yaw=-math.pi*.4+u*math.pi*.7
        elif idx==4:
            theta=math.pi*.12+math.pi*1.7
            anchor=np.array((self.target[0]+1.35*math.cos(theta),2.35,self.target[1]+1.35*math.sin(theta)),dtype=np.float32)
            drone=lerp(anchor,follow,ease_in_out(u))
            drone_yaw=heading
        elif idx==5:
            drone=follow
        elif idx==7:
            drone=follow
            drone[1]+= .25*smoothstep(u)
        drone[1]+=.09*math.sin(time_seconds*2.2)
        return MissionPose(idx,label,status,u,(time_seconds%PERIOD)/PERIOD,
             np.array((rover[0],.78,rover[1]),dtype=np.float32),heading,
             drone.astype(np.float32),drone_yaw,travelled,scan,cycle+1)

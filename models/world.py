"""Rover, drone e paisagem marciana usando um grafo de cena hierárquico."""
from __future__ import annotations
import math
import random
import numpy as np
from framework import geometry as g
from framework.scene import Node, Mesh, Material, part

class Art:
    def __init__(self):
        self.cube=g.box()
        self.cylinder=g.cylinder(20)
        self.sphere=g.sphere(16,10)
        self.cone=g.cone(10)
        self.ring=g.ring(64)
        self.ground,self.ground_height=g.terrain()
        def mat(hexcode, roughness=.6,emissive=0.,texture=None,double=False):
            h=hexcode.lstrip('#')
            return Material(tuple(int(h[i:i+2],16)/255 for i in (0,2,4)),roughness,emissive,texture,double)
        self.sand=mat('#d89566',.94,texture='mars_ground.png')
        self.red=mat('#bf644a',.98)
        self.orange=mat('#f08e3c',.58)
        self.orange_light=mat('#f3bd6c',.48)
        self.white=mat('#e9e5d8',.57)
        self.cream=mat('#c6c5b9',.75)
        self.charcoal=mat('#28343b',.87)
        self.rubber=mat('#252c33',.95)
        self.metal=mat('#7e93a2',.36)
        self.chrome=mat('#bdcbd0',.29)
        self.solar=mat('#193d57',.19)
        self.solar_grid=mat('#5381a0',.33)
        self.cyan=mat('#55ddf2',.18,emissive=.78,double=True)
        self.cyan_dim=mat('#2f7e9b',.4,emissive=.22,double=True)
        self.gold=mat('#f2c46e',.43,emissive=.27)
        self.mars_rock=mat('#a45440',.94)
        self.rock_light=mat('#c37750',.93)
        self.rock_dark=mat('#884330',.98)
        self.distant=mat('#a15a48',1.)
        self.violet=mat('#906b7b',.76)


def add_bars(parent,geo,material,p0,p1,width,name='barra'):
    """Cria haste alinhada entre dois pontos (boa para pernas e antenas)."""
    d=np.asarray(p1,dtype=np.float32)-np.asarray(p0,dtype=np.float32)
    length=float(np.linalg.norm(d))
    if length<1e-6:
        return None
    direction=d/length
    # Cilindro/cubo com eixo local Y; rotação Y, depois X e Z.
    # Eixo vertical y pode apontar em qualquer direção 3D pela inclinação e azimute.
    yaw=math.atan2(direction[0],direction[2])
    pitch=math.acos(float(np.clip(direction[1],-1.,1.)))
    # RotY * RotX aplicada ao eixo Y: (sin(yaw)*sin(pitch),cos(pitch),cos(yaw)*sin(pitch))
    # RotX(pitch) Y=(0,cos(pitch),sin(pitch)).
    return part(parent,name,geo,material,pos=(np.array(p0)+np.array(p1))*0.5,
                scale=(width,length,width),rot=(pitch,yaw,0))

class Rover:
    def __init__(self,art:Art):
        self.art=art
        a=art
        self.root=Node('ROVER | veículo explorador')
        self.wheels=[]
        self.mast=None
        part(self.root,'chassi principal',a.cube,a.white,pos=(0,.08,0),scale=(2.12,.58,3.20))
        part(self.root,'carapaça superior',a.cube,a.cream,pos=(0,.42,.05),scale=(1.9,.22,2.5))
        part(self.root,'faixa frontal laranja',a.cube,a.orange,pos=(0,.09,-1.62),scale=(1.92,.29,.14))
        part(self.root,'painel frontal escuro',a.cube,a.charcoal,pos=(0,-.12,-1.63),scale=(1.45,.16,.06))
        part(self.root,'defensa inferior',a.cube,a.metal,pos=(0,-.37,-1.65),scale=(2.30,.12,.18))
        part(self.root,'luz dianteira esquerda',a.cube,a.cyan,pos=(-.78,.14,-1.73),scale=(.23,.16,.07),cast=False)
        part(self.root,'luz dianteira direita',a.cube,a.cyan,pos=(.78,.14,-1.73),scale=(.23,.16,.07),cast=False)
        part(self.root,'tampa traseira',a.cube,a.orange,pos=(0,.20,1.63),scale=(1.65,.28,.14))
        part(self.root,'grade lateral esquerda',a.cube,a.orange,pos=(-1.09,.19,.30),scale=(.08,.23,1.55))
        part(self.root,'grade lateral direita',a.cube,a.orange,pos=(1.09,.19,.30),scale=(.08,.23,1.55))
        # proteção superior e painéis solares
        for side in (-1,1):
            support=Node('braço do painel solar',position=(side*1.10,.43,.35),rotation=(0,0,side*-.17))
            self.root.add(support)
            part(support,'bandeja painel',a.cube,a.orange,pos=(side*.33,.0,0),scale=(.82,.09,2.18))
            part(support,'células fotovoltaicas',a.cube,a.solar,pos=(side*.33,.065,0),scale=(.69,.025,2.02))
            for z in (-.66,-.22,.22,.66):
                part(support,'trilha painel',a.cube,a.solar_grid,pos=(side*.33,.09,z),scale=(.69,.009,.025),cast=False)
            part(support,'lateral do painel',a.cube,a.chrome,pos=(side*.76,.09,0),scale=(.035,.06,2.0))
        # 6 rodas e suspensão; pivôs de roda são nós animados hierarquicamente
        for side in (-1,1):
            for j,z in enumerate((-1.20,.0,1.25)):
                x=side*1.16
                part(self.root,'suporte suspensão',a.cube,a.metal,pos=(side*1.0,-.30,z),scale=(.33,.16,.22))
                wheelpivot=self.root.add(Node(f'roda {"E" if side<0 else "D"}{j+1}',position=(x,-.45,z)))
                self.wheels.append(wheelpivot)
                part(wheelpivot,'pneu',a.cylinder,a.rubber,scale=(.39,.22,.39),rot=(0,0,math.pi/2))
                part(wheelpivot,'aro',a.cylinder,a.metal,pos=(side*.13,0,0),scale=(.245,.13,.245),rot=(0,0,math.pi/2))
                part(wheelpivot,'miolo',a.cylinder,a.orange,pos=(side*.205,0,0),scale=(.085,.07,.085),rot=(0,0,math.pi/2))
                for k in range(9):
                    an=k*math.tau/9
                    part(wheelpivot,'gomo do pneu',a.cube,a.charcoal,
                         pos=(0,.383*math.cos(an),.383*math.sin(an)),
                         scale=(.43,.075,.14),rot=(an,0,0))
        # Sensor montado como subgrafo, podendo orientar-se independentemente do rover
        self.mast=self.root.add(Node('pivô do mastro',position=(0,.56,-.48)))
        part(self.mast,'base do mastro',a.cylinder,a.orange,pos=(0,.08,0),scale=(.34,.17,.34))
        part(self.mast,'haste telescópica',a.cylinder,a.chrome,pos=(0,.65,0),scale=(.08,.95,.08))
        part(self.mast,'pescoço',a.cube,a.metal,pos=(0,1.16,-.05),scale=(.27,.18,.35))
        part(self.mast,'câmera estereoscópica',a.cube,a.white,pos=(0,1.25,-.20),scale=(.78,.31,.44))
        for x in (-.25,.25):
            part(self.mast,'visor da câmera',a.cylinder,a.solar,pos=(x,1.26,-.46),
                 scale=(.13,.05,.13),rot=(math.pi/2,0,0))
            part(self.mast,'lente emissiva',a.cylinder,a.cyan,pos=(x,1.26,-.505),
                 scale=(.065,.022,.065),rot=(math.pi/2,0,0),cast=False)
        part(self.mast,'sensor iluminado',a.sphere,a.cyan,pos=(0,1.44,-.22),scale=(.09,.09,.09),cast=False)
        # Antena parabólica simplificada
        antenna=self.root.add(Node('antena secundária',position=(.57,.67,1.04)))
        part(antenna,'poste antena',a.cylinder,a.chrome,pos=(0,.41,0),scale=(.035,.72,.035))
        part(antenna,'disco receptor',a.cylinder,a.white,pos=(0,.86,0),scale=(.38,.045,.38),rot=(.18,0,-.23))
        part(antenna,'miolo receptor',a.sphere,a.gold,pos=(0,.93,0),scale=(.09,.09,.09),cast=False)
        self.antenna=antenna

    def update(self,pose,t):
        self.root.position[:]=pose.rover_position
        self.root.rotation[1]=pose.rover_yaw
        for wheel in self.wheels:
            wheel.rotation[0]=pose.rover_travel/.39
        self.mast.rotation[1]=.17*math.sin(t*.7)+pose.scan_strength*.15
        self.antenna.rotation[1]=t*.30

class Drone:
    def __init__(self,art:Art):
        self.art=art
        a=art
        self.root=Node('DRONE | reconhecimento aéreo')
        self.rotors=[]
        part(self.root,'corpo do drone',a.cube,a.white,scale=(.86,.28,.97))
        part(self.root,'tampa superior',a.cube,a.orange,pos=(0,.17,0),scale=(.65,.08,.72))
        part(self.root,'sensor central',a.sphere,a.solar,pos=(0,-.22,-.15),scale=(.24,.21,.24))
        part(self.root,'lente da câmera',a.sphere,a.cyan,pos=(0,-.23,-.33),scale=(.11,.11,.06),cast=False)
        part(self.root,'luz de status',a.sphere,a.cyan,pos=(0,.235,-.28),scale=(.07,.05,.07),cast=False)
        for angle in (math.pi/4,-math.pi/4):
            part(self.root,'haste cruzada',a.cube,a.charcoal,scale=(2.65,.11,.15),rot=(0,angle,0))
        for side_x in (-1,1):
            for side_z in (-1,1):
                x,z=side_x*.96,side_z*.96
                part(self.root,'cubo do motor',a.cylinder,a.orange,pos=(x,.08,z),scale=(.20,.22,.20))
                part(self.root,'cúpula motor',a.cylinder,a.chrome,pos=(x,.23,z),scale=(.13,.055,.13))
                rotor=self.root.add(Node('hélice em rotação',position=(x,.30,z)))
                self.rotors.append(rotor)
                part(rotor,'eixo',a.cylinder,a.charcoal,scale=(.07,.06,.07))
                part(rotor,'pá A',a.cube,a.chrome,pos=(.29,.01,0),scale=(.57,.025,.11),cast=False)
                part(rotor,'pá B',a.cube,a.chrome,pos=(-.29,.01,0),scale=(.57,.025,.11),cast=False)
                part(self.root,'lanterna rotor',a.sphere,a.cyan if side_x==side_z else a.gold,
                     pos=(x,.06,z),scale=(.09,.055,.09),cast=False)
        for side in (-1,1):
            add_bars(self.root,a.cylinder,a.metal,(side*.31,-.16,.24),(side*.49,-.57,.33),.043,'perna de pouso')
            add_bars(self.root,a.cylinder,a.metal,(side*.31,-.16,-.24),(side*.49,-.57,-.33),.043,'perna de pouso')
            part(self.root,'sapata',a.cube,a.charcoal,pos=(side*.49,-.60,0),scale=(.13,.08,.92))
        self.scan_indicator=self.root.add(Node('feixe vertical de leitura'))
        part(self.scan_indicator,'luz do sensor',a.cylinder,a.cyan,scale=(.025,.6,.025),cast=False)
        self.scan_indicator.scale[:]=(.0,.0,.0)
    def update(self,pose,t):
        self.root.position[:]=pose.drone_position
        self.root.rotation[1]=pose.drone_yaw
        self.root.rotation[2]=.06*math.sin(t*1.4)
        for i,rotor in enumerate(self.rotors):
            rotor.rotation[1]=t*(27.0 if i%2==0 else -27.0)
        self.scan_indicator.position[:]=(0,-.78,0)
        s=max(0.,pose.scan_strength)
        self.scan_indicator.scale[:]=(s,s*1.3,s)

class Environment:
    def __init__(self,art:Art):
        a=art
        self.root=Node('PLANETA MARTE | cenário')
        part(self.root,'solo rochoso com textura',a.ground,a.sand,cast=False)
        rng=random.Random(2026)
        # Pedras de três cores, com distribuição reprodutível e caminho livre.
        colors=[a.mars_rock,a.rock_light,a.rock_dark,a.red]
        for i in range(195):
            x=rng.uniform(-34,34);z=rng.uniform(-34,34)
            # corredores da missão e zona de inspeção precisam estar desobstruídos
            if (-13<x<11 and -9<z<11):
                continue
            size=rng.uniform(.13,.60)**1.25
            y=a.ground_height(x,z)+size*.22
            rock=Node(f'fragmento marciano {i}',position=(x,y,z),rotation=(0,rng.random()*6.28,0))
            self.root.add(rock)
            part(rock,'rocha',a.sphere,rng.choice(colors),scale=(size*1.4,size*.45,size*1.1))
        # Cadeia de montanhas de baixo polígono, no horizonte
        for i in range(26):
            theta=math.tau*i/26
            radius=rng.uniform(32,42)
            x=radius*math.cos(theta);z=radius*math.sin(theta)
            tall=rng.uniform(2.8,7.0)
            part(self.root,'mesa distante',a.cone,a.distant,
                 pos=(x,tall*.44,z),scale=(rng.uniform(2.,5.),tall,rng.uniform(2.,5.)),
                 rot=(0,rng.uniform(-1.,1.),0))
        # Cratera circular distante: anel de rochas e depressão estilizada
        for i in range(18):
            theta=math.tau*i/18
            r=3.3+ rng.uniform(-.24,.24)
            x,z=-16+r*math.cos(theta),-6+r*math.sin(theta)
            size=rng.uniform(.42,.9)
            part(self.root,'anel da cratera',a.sphere,rng.choice(colors),
                 pos=(x,a.ground_height(x,z)+size*.22,z),
                 scale=(size*1.3,size*.47,size))
        # Estação de partida / zona Alpha
        self.station=Node('base Alpha',position=(-10.,0.,7.))
        self.root.add(self.station)
        part(self.station,'placa base Alpha',a.cylinder,a.charcoal,pos=(0,-.03,0),scale=(3.9,.10,3.9),cast=False)
        part(self.station,'anel iluminado base',a.ring,a.cyan_dim,pos=(0,.058,0),scale=(3.65,1,3.65),cast=False)
        # torre sinalizadora lateral
        tower=Node('torre de comunicação',position=(-12.5,.0,9.6))
        self.root.add(tower)
        part(tower,'sapata torre',a.cylinder,a.chrome,pos=(0,.10,0),scale=(.52,.18,.52))
        part(tower,'poste de comunicação',a.cylinder,a.metal,pos=(0,1.55,0),scale=(.065,2.9,.065))
        part(tower,'topo torre',a.sphere,a.orange,pos=(0,3.02,0),scale=(.23,.23,.23))
        part(tower,'farol sinalizador',a.sphere,a.cyan,pos=(0,3.3,0),scale=(.16,.16,.16),cast=False)
        for side in (-1,1):
            add_bars(tower,a.cylinder,a.metal,(0,.36,0),(side*.71,.02,.0),.032)
        # Ponto de inspeção (rocha grande e marcação de risco)
        self.scan_target=Node('alvo de inspeção',position=(1.65,0,-2.2))
        self.root.add(self.scan_target)
        part(self.scan_target,'rocha principal',a.sphere,a.rock_dark,pos=(0,.69,0),scale=(1.38,.82,1.12))
        part(self.scan_target,'segunda camada',a.sphere,a.rock_light,pos=(-.50,.31,.58),scale=(.89,.46,.67))
        part(self.scan_target,'veio da rocha',a.cube,a.gold,pos=(.22,1.25,-.62),scale=(.08,.12,.42),rot=(.32,-.35,.18))
        part(self.scan_target,'círculo da área de análise',a.ring,a.cyan_dim,
             pos=(0,.17,0),scale=(2.48,1,2.48),cast=False)
        self.scan_ring=self.scan_target.add(Node('pulso de leitura',position=(0,.18,0)))
        part(self.scan_ring,'pulso',a.ring,a.cyan,scale=(1.75,1,1.75),cast=False)
        self.scan_ring.scale[:]=(0.001,1.,0.001)
        for i in range(4):
            ang=math.tau*i/4
            pos=(2.6*math.cos(ang),.16,2.6*math.sin(ang))
            part(self.scan_target,'baliza de inspeção',a.cylinder,a.gold,pos=pos,scale=(.09,.30,.09))
        # Rastro de marcadores geométricos no caminho: pista de exploração
        for i in range(12):
            f=i/11
            x=-9.8+6.4*f
            z=7.-5.2*f
            part(self.root,'marcador de rota',a.cube,a.cyan_dim,
                 pos=(x,a.ground_height(x,z)+.10,z),scale=(.13,.025,.22),
                 rot=(0,.67,0),cast=False)
        # Pedras próximas que não interceptam a rota
        for x,z,s in [(-11,2.3,.8),(-6,-5,1.3),(-9,-3,1.0),
                      (4,-6.4,1.3),(8,2,1.6),(10,3.3,.9),
                      (4,7,.95),(11,-9,.8),(-15,12,1.3)]:
            part(self.root,'matacão rochoso',a.sphere,a.mars_rock,
                 pos=(x,s*.33,z),scale=(s*1.3,s*.58,s*1.1),rot=(0,rng.uniform(-2,2),0))
        # pequenas placas que dão escala e direção à cena
        for x,z in [(-12,0),(10,0),(-1,10)]:
            part(self.root,'marcador vertical',a.cylinder,a.chrome,pos=(x,.45,z),scale=(.055,.78,.055))
            part(self.root,'topo marcador',a.sphere,a.orange,pos=(x,.9,z),scale=(.13,.13,.13))

    def update(self,pose,t):
        s=pose.scan_strength
        self.scan_ring.scale[:]=((1.5+.22*math.sin(t*5))*max(s,.001),1.,
                                  (1.5+.22*math.sin(t*5))*max(s,.001))
        self.scan_ring.rotation[1]=t*.8

class MarsWorld:
    def __init__(self):
        self.art=Art()
        self.root=Node('CENA COMPLETA')
        self.environment=Environment(self.art)
        self.rover=Rover(self.art)
        self.drone=Drone(self.art)
        self.root.add(self.environment.root)
        self.root.add(self.rover.root)
        self.root.add(self.drone.root)
    def update(self,pose,t):
        self.environment.update(pose,t)
        self.rover.update(pose,t)
        self.drone.update(pose,t)
    def meshes(self):
        return list(self.root.traverse())

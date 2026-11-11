"""Câmera orbital em perspectiva, controlada por teclado e mouse."""
import math
import numpy as np
from .math3d import look_at,perspective

class OrbitCamera:
    def __init__(self):
        self.target=np.array((-.8,1.3,.0),dtype=np.float32)
        self.yaw=math.radians(39)
        self.pitch=math.radians(28)
        self.distance=23.0
        self.fov=52.0
    @property
    def eye(self):
        c=math.cos(self.pitch)
        return self.target+np.array((math.sin(self.yaw)*c*self.distance,
                    math.sin(self.pitch)*self.distance,
                    math.cos(self.yaw)*c*self.distance),dtype=np.float32)
    def view(self):
        return look_at(self.eye,self.target)
    def projection(self,aspect):
        return perspective(self.fov,aspect,.1,180.)
    def orbit(self,dyaw,dpitch):
        self.yaw+=dyaw
        self.pitch=max(math.radians(12),min(math.radians(75),self.pitch+dpitch))
    def zoom(self,delta):
        self.distance=max(8.,min(56.,self.distance+delta))
    def pan(self,side,forward):
        right=np.array((math.cos(self.yaw),0.,-math.sin(self.yaw)),dtype=np.float32)
        horizontal=np.array((-math.sin(self.yaw),0.,-math.cos(self.yaw)),dtype=np.float32)
        self.target+=right*side + horizontal*forward
    def preset(self,number):
        if number==1:
            self.target[:]=(-.8,1.3,0.);self.yaw=math.radians(39)
            self.pitch=math.radians(28);self.distance=23
        elif number==2:
            self.target[:]=(-2.,.9,.0);self.yaw=math.radians(3)
            self.pitch=math.radians(60);self.distance=22
        elif number==3:
            self.target[:]=(-1.,1.2,-1.);self.yaw=math.radians(78)
            self.pitch=math.radians(22);self.distance=19

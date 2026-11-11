#version 330 core
in vec2 vUV;
out vec4 FragColor;
uniform float uTime;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
void main(){
    float y=clamp(vUV.y,0.,1.);
    vec3 horizon=vec3(.68,.35,.29);
    vec3 zenith=vec3(.13,.16,.27);
    float blend=smoothstep(.06,1.,y);
    vec3 col=mix(horizon,zenith,pow(blend,.72));
    // Atmosfera poeirenta perto do horizonte, faixas muito suaves.
    col+=vec3(.07,.033,.026)*exp(-pow((y-.24)/.13,2.));
    vec2 sun=(vUV-vec2(.75,.74))*vec2(1.8,1.0);
    float disc=1.-smoothstep(.018,.042,length(sun));
    float halo=exp(-length(sun)*6.5);
    col+=vec3(.65,.34,.15)*halo*.56;
    col+=vec3(1.,.65,.36)*disc*.8;
    vec2 grid=floor(vUV*vec2(490.,250.));
    float star=step(.9988,hash(grid))*smoothstep(.62,.9,y);
    col+=vec3(.42,.55,.72)*star*.75;
    FragColor=vec4(col,1.0);
}

#version 330 core
in vec3 vWorldPos;
in vec3 vNormal;
in vec2 vUV;
in vec4 vLightPos;
out vec4 FragColor;

uniform sampler2D uTexture;
uniform sampler2DShadow uShadowMap;
uniform bool uHasTexture;
uniform vec3 uColor;
uniform vec3 uLightDirection;
uniform vec3 uCameraPos;
uniform float uRoughness;
uniform float uEmission;

float shadowAmount(vec3 n, vec3 toLight) {
    vec3 projected = vLightPos.xyz / max(vLightPos.w, 0.00001);
    projected = projected * .5 + .5;
    if (projected.z > 1.0 || projected.z < 0.0 ||
        projected.x < 0.0 || projected.x > 1.0 ||
        projected.y < 0.0 || projected.y > 1.0) return 0.0;
    float bias = max(.00068 * (1.0 - dot(n, toLight)), .00019);
    vec2 texel = 1.0 / vec2(textureSize(uShadowMap,0));
    float visible = 0.0;
    for (int x=-1; x<=1; x++) {
        for (int y=-1; y<=1; y++) {
            vec2 offset=vec2(x,y)*texel*1.15;
            visible += texture(uShadowMap, vec3(projected.xy + offset, projected.z - bias));
        }
    }
    return 1.0 - (visible / 9.0);
}

void main() {
    vec3 base = uColor;
    if (uHasTexture) base *= texture(uTexture,vUV).rgb;
    vec3 n=normalize(vNormal);
    vec3 L=normalize(uLightDirection);
    vec3 viewDir=normalize(uCameraPos-vWorldPos);
    vec3 halfway=normalize(L+viewDir);
    float lambert=max(dot(n,L),0.0);
    float shadow=shadowAmount(n,L);
    float lightAmount=.43+lambert*.80*(1.0-.80*shadow);
    float shininess=mix(5.0,90.0,1.0-uRoughness);
    float specular=pow(max(dot(n,halfway),0.0),shininess) * .38 *
        (1.0-uRoughness) * (1.0-shadow) * step(.01,lambert);
    vec3 color=base*lightAmount+vec3(1.0,.89,.74)*specular;
    color+=base*uEmission;
    color=pow(max(color,vec3(0.0)),vec3(1.0/2.2));
    float dist=length(uCameraPos-vWorldPos);
    float fog=1.0-exp(-pow(dist*.016,2.0));
    vec3 fogColor=vec3(.70,.425,.342);
    color=mix(color,fogColor,clamp(fog,0.0,.76));
    FragColor=vec4(color,1.0);
}

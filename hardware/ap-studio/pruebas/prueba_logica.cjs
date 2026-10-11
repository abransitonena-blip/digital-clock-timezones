// Pruebas de AP LÓGICA en AP Studio (motor JS, escalera <-> texto, plantillas). node ap-studio/pruebas/prueba_logica.cjs
// Toma el código directo de index.html: prueba lo mismo que corre en la app.
const fs=require("fs"),path=require("path");
const s=fs.readFileSync(path.join(__dirname,"..","index.html"),"utf8");
const pz=(a,b)=>s.slice(s.indexOf(a),s.indexOf(b));
const src=pz("/* ---------- AP LÓGICA: el mismo motor","/* ---------- AP LÓGICA: dibujo")+pz("const PLANTILLAS","function hojaPlantillas");
const {Plc,genIL,deIL,insDe,insIgual,PLANTILLAS}=new Function(src+"\nreturn {Plc,genIL,deIL,insDe,insIgual,PLANTILLAS};")();
let f=0;const R=(c,m)=>{if(!c){f++;console.log("falla:",m)}};
class Sim{constructor(){this.I=[];this.Q=[];this.L=[];this.P=false;this.A=[]}leerBit(a,i){return a=="I"?!!this.I[i]:a=="Q"?!!this.Q[i]:a=="L"?!!this.L[i]:a=="P"?this.P:a=="S"?i==3:false}
 valor(a,i){return a=="A"?(this.A[i]??NaN):NaN}esc(a,i,v){if(a=="Q")this.Q[i]=v;if(a=="L")this.L[i]=v;if(a=="P")this.P=v}}
const run=(p,e,ms)=>{for(let t=0;t<ms;t+=10)p.ciclo(e,10)};
{const p=new Plc(),e=new Sim();R(p.compilar("LD I1\nOR Q1\nANDN I2\nOUT Q1"),"c1");e.I[1]=1;run(p,e,20);R(e.Q[1],"latch");e.I[1]=0;run(p,e,20);R(e.Q[1],"keep");e.I[2]=1;run(p,e,20);R(!e.Q[1],"stop")}
{const p=new Plc(),e=new Sim();R(p.compilar("LD I1\nTON T1 500\nLD T1\nOUT Q1\nLD I2\nTOF T2 300\nLD T2\nOUT Q2\nLDP I3\nTP T3 200\nLD T3\nOUT Q3"),"c2");
 e.I[1]=1;run(p,e,490);R(!e.Q[1],"ton1");run(p,e,30);R(e.Q[1],"ton2");e.I[3]=1;run(p,e,100);R(e.Q[3],"tp1");run(p,e,200);R(!e.Q[3],"tp2")}
{const p=new Plc(),e=new Sim();p.compilar("LDP I1\nCTU C1 3\nLD C1\nOUT Q1\nLD I2\nRST C1");for(let k=0;k<3;k++){e.I[1]=1;run(p,e,20);e.I[1]=0;run(p,e,20)}R(p.c[1].cv==3&&e.Q[1],"ctu")}
for(const [t,ok] of [["LD I1\nOUT X3",0],["AND I1\nOUT Q1",0],["LD I1\nLD I2\nOUT Q1",0],["LD A1\nOUT Q1",0],["LD I1\nTON C1 100",0],["LD M200\nOUT Q1",0],["ld i1 ; c\nout q1",1]]){const p=new Plc();R(p.compilar(t)==!!ok,"err "+t)}
// ida y vuelta: texto -> escalera -> texto da las mismas instrucciones
const casos=["LD I1\nOR Q1\nANDN I2\nOUT Q1","LD I1\nAND I2\nLD I3\nAND I4\nORB\nOUT Q1","LD I1\nOR I2\nLD I3\nOR I4\nANB\nOUT Q1\nSET M70",
 "LDP I5\nSET M70\nLDF I5\nRST M2","LD A1 > 3.5\nSET Q4","LD S3\nOUT Q5",...PLANTILLAS.map(p=>p.il)];
for(const c of casos){const d=deIL(c);R(d.rs,"deIL "+c+" "+d.err);if(!d.rs)continue;const g=genIL(d.rs);R(insIgual(insDe(g.txt),insDe(c)),"vuelta "+JSON.stringify(c)+" -> "+JSON.stringify(g.txt))}
R(deIL("LD I1\nNOT\nOUT Q1").err,"not");
// el mapa apunta a las instrucciones correctas
{const d=deIL("LD I1\nOR Q1\nANDN I2\nOUT Q1").rs,g=genIL(d);R(g.mapa["0.0.0.0"]==0&&g.mapa["0.0.1.0"]==1&&g.mapa["0.1.0.0"]==2&&g.mapa["0.o0"]==3,"mapa "+JSON.stringify(g.mapa))}
// alternancia de bombas: arranques alternos
{const p=new Plc(),e=new Sim();p.compilar(PLANTILLAS[5].il);const q=[];for(let k=0;k<4;k++){e.I[1]=1;run(p,e,30);q.push(e.Q[1]?1:e.Q[2]?2:0);e.I[1]=0;run(p,e,30)}R(q.join()=="1,2,1,2","alternancia "+q)}
{const p=new Plc();p.compilar("LD I1\nOUT Q1");const j=p.json(1,10);R(j.n==2&&j.m.length==32&&j.t.length==16,"json")}
console.log(f?f+" FALLAS":"AP LÓGICA JS: todo bien");process.exit(f?1:0)

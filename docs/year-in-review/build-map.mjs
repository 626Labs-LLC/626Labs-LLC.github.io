import fs from 'fs';
import {createRequire} from 'module';
const require=createRequire(import.meta.url);
const topo=require('topojson-client'), d3=require('d3-geo'), iso=require('i18n-iso-countries');
const w=JSON.parse(fs.readFileSync('node_modules/world-atlas/countries-110m.json','utf8'));
const sa=JSON.parse(fs.readFileSync('C:/Users/estev/Projects/626labs-hub/data/store-analytics.json','utf8'));
const fc=topo.feature(w,w.objects.countries);
const proj=d3.geoNaturalEarth1().fitExtent([[4,4],[956,496]],{type:'Sphere'});
const path=d3.geoPath(proj).digits?d3.geoPath(proj).digits(1):d3.geoPath(proj);
const paths={},names={};
for(const f of fc.features){
  const a2=iso.numericToAlpha2(String(f.id).padStart(3,'0'));
  if(!a2) continue;
  const d=path(f); if(!d) continue;
  paths[a2]=d; names[a2]=f.properties.name;
}
const totals={},byApp={};
const appNames={};
for(const [id,a] of Object.entries(sa.apps)){
  appNames[id]=a.name||a.title||id;
  for(const [c,n] of Object.entries(a.installsByMarket||{})){
    totals[c]=(totals[c]||0)+n; (byApp[c]=byApp[c]||{})[id]=n;
  }
}
const rows=Object.entries(totals).map(([c,n])=>({c,n,name:iso.getName(c,'en')||names[c]||c,drawn:!!paths[c],apps:byApp[c]})).sort((a,b)=>b.n-a.n||a.name.localeCompare(b.name));
const LL={SG:[1.35,103.82],HK:[22.3,114.17],BH:[26.07,50.55],VI:[18.34,-64.9],BB:[13.19,-59.54],MO:[22.2,113.54],MV:[3.2,73.22],MU:[-20.3,57.55],RE:[-21.1,55.5],VC:[12.98,-61.29],AS:[-14.3,-170.7],AG:[17.06,-61.8],AW:[12.5,-69.97],BM:[32.3,-64.75],IO:[-6.3,71.9],GD:[12.12,-61.68],GP:[16.25,-61.58],GU:[13.44,144.79],MT:[35.9,14.4],MQ:[14.64,-61.02],MP:[15.2,145.75],SM:[43.94,12.46]};
const dots=rows.filter(r=>!r.drawn).map(r=>{const p=proj([LL[r.c][1],LL[r.c][0]]);return {c:r.c,x:+p[0].toFixed(1),y:+p[1].toFixed(1)}});
fs.writeFileSync('map.json',JSON.stringify({paths,dots,rows,appNames,sphere:path({type:'Sphere'})}));
console.log(rows.length,'markets', rows.filter(r=>!r.drawn).length,'undrawn:',rows.filter(r=>!r.drawn).map(r=>r.c+':'+r.n).join(' '));
console.log('sum',rows.reduce((s,r)=>s+r.n,0),'paths',Object.keys(paths).length,'bytes',fs.statSync('map.json').size);
console.log(JSON.stringify(appNames));

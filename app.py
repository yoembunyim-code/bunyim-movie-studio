<!doctype html>
<html lang="km">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VoiceClone Studio Pro – សម្រាយរឿងកម្រិតអាជីព (គ្មាន API Key)</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Khmer:wght@400;600;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#05070C;--card:#0D121F;--ink:#E2E8F0;--mute:#94A3B8;--line:#1E293B;--acc:#0EA5E9;--acc2:#1E1B4B;--ok:#34D399;--bad:#F87171}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 "Noto Sans Khmer",system-ui,sans-serif}
main{max-width:1280px;margin:0 auto;padding:18px 14px 60px}
h1{font-size:24px;margin:0;background:linear-gradient(135deg,#38BDF8,#818CF8);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
h2{font-size:16px;margin:0 0 10px;color:#38BDF8}
.sub{color:var(--mute);margin:2px 0 16px;font-size:14px}
.grid{display:grid;grid-template-columns:minmax(300px,400px) 1fr;gap:16px}
@media(max-width:820px){.grid{grid-template-columns:1fr}}
section{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px;box-shadow:0 4px 12px rgba(0,0,0,0.4)}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:8px 0}
button,select,input,textarea{font:inherit;color:inherit}
button{background:linear-gradient(135deg,#0EA5E9,#2563EB);color:#fff;border:0;border-radius:8px;padding:8px 14px;cursor:pointer;font-weight:600;transition:all 0.3s}
button:hover{opacity:0.9;transform:translateY(-1px)}
button:disabled{opacity:.5;cursor:wait}
button.g{background:var(--acc2);color:#C7D2FE;border:1px solid var(--line)}
button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
input,select,textarea{background:#111827;border:1px solid #374151;border-radius:8px;padding:6px 10px}
video{width:100%;max-height:380px;background:#000;border-radius:8px}
textarea{width:100%}
#msg{min-height:24px;color:var(--mute);font-size:14px}#msg.err{color:var(--bad)}#msg.ok{color:var(--ok)}
.wrap{overflow:auto;max-height:520px}
table{border-collapse:collapse;width:100%;min-width:720px}
th{position:sticky;top:0;background:var(--card);text-align:left;color:var(--mute);padding:8px;font-size:13px}
td{padding:6px;vertical-align:top;border-bottom:1px solid var(--line)}
td input[type=number]{width:72px}td textarea{min-height:56px;font-size:14px}
tr.on td{background:var(--acc2)}
.note{color:var(--mute);font-size:13px}
input[type=range]{padding:0}
.ai{border:1px dashed var(--acc);border-radius:10px;padding:10px;margin-top:10px;background:#0B101D}
</style>
</head>
<body>
<main>
<h1>🎙️ VOICECLONE STUDIO PRO</h1>
<p class="sub">ប្រព័ន្ធបកប្រែវីដេអូរឿង និងដាក់សំឡេង AI តាមតួអង្គ (ប្រុស · ស្រី · ចាស់ · សម្រាយ) យ៉ាងជាក់លាក់</p>

<div class="grid">
<section>
  <h2>📺 គ្រប់គ្រងវីដេអូ និងសំឡេង</h2>
  <div class="bar">
    <button class="g" id="bVid">📁 បើកវីដេអូ</button>
    <button class="g" id="bSrt">📄 នាំចូល SRT</button>
  </div>
  <input type="file" id="fVid" accept="video/*,audio/*" hidden>
  <input type="file" id="fSrt" accept=".srt,.txt" hidden>
  <video id="vid" controls playsinline></video>
  <div class="bar">
    <label><input type="checkbox" id="mute" checked> បិទសំឡេងដើមវីដេអូ</label>
    <label>កម្រិត BGM <input type="range" id="vol" min="0" max="1" step="0.05" value="0.1" style="width:80px"></label>
  </div>

  <div class="ai">
    <h2>🧠 AI ស្តាប់សំឡេង (Whisper Engine)</h2>
    <div class="bar">
      <label>ភាសាដើម <select id="src"></select></label>
      <label>ម៉ូដែល <select id="model">
        <option value="Xenova/whisper-tiny">tiny (លឿន)</option>
        <option value="Xenova/whisper-base" selected>base (ស្តង់ដារ)</option>
        <option value="Xenova/whisper-small">small (ច្បាស់ល្អ)</option>
      </select></label>
    </div>
    <div class="bar">
      <button id="bAsr">🧠 ស្តាប់ទាញយកអត្ថបទពីវីដេអូ</button>
    </div>
    <div class="bar">
      <label>Gemini Key <input type="password" id="gkey" placeholder="AIza..." style="width:180px"></label>
      <button id="bGem" class="g">✨ Gemini វិភាគតួអង្គ</button>
    </div>
    <p class="note">ដំណើរការក្នុងเครื่องរបស់អ្នកដោយសុវត្ថិភាព មិនបារម្ភរឿងបែកធ្លាយទិន្នន័យ។</p>
  </div>

  <h2 style="margin-top:12px">📝 បិទភ្ជាប់ស្គ្រីបបន្ថែម</h2>
  <textarea id="script" rows="3" placeholder="មួយបន្ទាត់ = មួយឃ្លា"></textarea>
  <div class="bar"><button class="g" id="bScript">បញ្ចូលទៅតារាង</button><button class="g" id="bAdd">＋ បន្ថែមឃ្លាថ្មី</button></div>
</section>

<section>
  <h2>🎛️ តារាងគ្រប់គ្រងម៉ោង និងសំឡេងតួអង្គ (Pro Timeline)</h2>
  <div class="bar">
    <label>ភាសាគោលដៅ <select id="lang"></select></label>
    <button id="bTr">🌐 បកប្រែខ្មែរទាំងអស់</button>
    <button id="bPlay">▶ ចាក់វីដេអូ + សំឡេង AI</button>
    <button class="g" id="bStop">■ ឈប់</button>
    <button class="g" id="bGuess">🎭 ស្មានតួអង្គស្វ័យប្រវត្តិ</button>
    <button class="g" id="bDl">⬇ ទាញយក SRT</button>
  </div>
  <div class="bar">
    <label>សំឡេងប្រុស <select id="vM"></select></label>
    <label>សំឡេងស្រី <select id="vF"></select></label>
    <label><input type="checkbox" id="fit" checked> កម្រិតល្បឿនត្រូវមាត់ (Time-Stretch)</label>
  </div>
  <div id="msg"></div>
  <div class="wrap"><table>
    <thead><tr><th>Start</th><th>End</th><th>អត្ថបទដើម</th><th>អត្ថបទបកប្រែខ្មែរ</th><th>តួអង្គ</th><th>សកម្មភាព</th></tr></thead>
    <tbody id="rows"></tbody>
  </table></div>
  <p class="note">💡 ពិនិត្យម៉ោង Start និង End ក្នុងតារាងឱ្យបានត្រឹមត្រូវ ដើម្បីធានាថាសំឡេងនិយាយត្រូវចំពេលតួអង្គមាត់កម្រើក។</p>
</section>
</div>
</main>

<script>
const $=s=>document.querySelector(s), sleep=ms=>new Promise(r=>setTimeout(r,ms));
const LANGS=[['ខ្មែរ','km','km-KH'],['English','en','en-US'],['中文','zh-CN','zh-CN'],['ไทย','th','th-TH']];
const SRC=[['ស្វ័យប្រវត្តិ','',''],['English','english','en-US'],['中文','chinese','zh-CN'],['ไทย','thai','th-TH'],['ខ្មែរ','khmer','km-KH']];
const PROF={
  'អ្នកសម្រាយរឿង':{g:'M',p:1,r:0.95},
  'តួប្រុស':{g:'M',p:0.9,r:1},
  'តួស្រី':{g:'F',p:1.1,r:1},
  'តួចាស់':{g:'M',p:0.75,r:0.85},
  'តួអង្គរង':{g:'F',p:1,r:1}
};
let rows=[], vid=$('#vid'), vidFile=null, lastAudio=null;
$('#lang').innerHTML=LANGS.map((l,i)=>`<option value="${i}"${i===0?' selected':''}>${l[0]}</option>`).join('');
$('#src').innerHTML=SRC.map((l,i)=>`<option value="${i}"${i===1?' selected':''}>${l[0]}</option>`).join('');
const L=()=>LANGS[$('#lang').value];
const S=()=>SRC[$('#src').value];
const say=(t,c='')=>{const m=$('#msg');m.textContent=t;m.className=c};

/* ---------- Voices Setup ---------- */
let VO=[];
function loadVoices(){
  const code=L()[2].slice(0,2);
  VO=speechSynthesis.getVoices().filter(v=>v.lang.toLowerCase().startsWith(code) || v.lang.toLowerCase().includes('km'));
  if(!VO.length) VO=speechSynthesis.getVoices(); // Fallback
  const opt=VO.map((v,i)=>`<option value="${i}">${v.name} (${v.lang})</option>`).join('')||'<option value="-1">(គ្មានសំឡេង)</option>';
  $('#vM').innerHTML=opt; $('#vF').innerHTML=opt;
  const find=re=>VO.findIndex(v=>re.test(v.name));
  const m=find(/piseth|male|david|guy|mark|ryan/i), f=find(/sreymom|female|zira|aria|jenny/i);
  if(m>=0)$('#vM').value=m; if(f>=0)$('#vF').value=f;
}
speechSynthesis.onvoiceschanged=loadVoices; loadVoices();
$('#lang').onchange=loadVoices;
const pick=g=>VO[+(g==='F'?$('#vF').value:$('#vM').value)] || VO[0];

/* ---------- Parsing & SRT ---------- */
const tc=s=>{const m=s.trim().match(/(?:(\d+):)?(\d+):(\d+)[,.](\d+)/);return m?(+(m[1]||0))*3600+(+m[2])*60+(+m[3])+(+m[4].padEnd(3,'0'))/1000:0};
const fmt=t=>{const h=Math.floor(t/3600),m=Math.floor(t%3600/60),s=Math.floor(t%60),ms=Math.round((t%1)*1000);return [h,m,s].map(n=>String(n).padStart(2,'0')).join(':')+','+String(ms).padStart(3,'0')};
function parseText(t){
  t=t.replace(/\r/g,'').trim(); if(!t) return [];
  if(t.includes('-->')) return t.split(/\n\s*\n/).map(b=>{const l=b.split('\n').filter(Boolean),i=l.findIndex(x=>x.includes('-->'));if(i<0)return null;const [a,e]=l[i].split('-->');return {s:tc(a),e:tc(e),o:l.slice(i+1).join(' ')}}).filter(Boolean);
  return t.split('\n').filter(x=>x.trim()).map((x,i)=>({s:i*3,e:i*3+3,o:x.trim()}));
}
const setRows=list=>{rows=list.map(r=>({...r,t:'',v:'អ្នកសម្រាយរឿង'}));render()};

/* ---------- Table Render ---------- */
function render(){
  const tb=$('#rows');tb.innerHTML='';
  rows.forEach((r,i)=>{
    const tr=document.createElement('tr');tr.id='r'+i;
    tr.innerHTML=`<td><input type="number" step="0.1" min="0" value="${r.s.toFixed(1)}"></td>
    <td><input type="number" step="0.1" min="0" value="${r.e.toFixed(1)}"></td>
    <td><textarea>${r.o}</textarea></td>
    <td><textarea>${r.t}</textarea></td>
    <td><select>${Object.keys(PROF).map(v=>`<option${v===r.v?' selected':''}>${v}</option>`).join('')}</select></td>
    <td><button class="g" title="ស្តាប់">▶</button></td>`;
    const [s,e,o,t,v,b]=tr.querySelectorAll('input,textarea,select,button');
    s.oninput=()=>r.s=+s.value; e.oninput=()=>r.e=+e.value; o.oninput=()=>r.o=o.value; t.oninput=()=>r.t=t.value; v.onchange=()=>r.v=v.value;
    s.ondblclick=()=>{vid.currentTime=r.s};
    b.onclick=()=>speak(r);
    tb.appendChild(tr);
  });
}
const sync=()=>rows.forEach((r,i)=>{const x=$('#r'+i);if(x){x.querySelectorAll('textarea')[1].value=r.t;x.querySelector('select').value=r.v}});

/* ---------- Inputs & Video ---------- */
$('#bVid').onclick=()=>$('#fVid').click();
$('#fVid').onchange=e=>{vidFile=e.target.files[0];if(vidFile){vid.src=URL.createObjectURL(vidFile);say('បានបើកវីដេអូជោគជ័យ','ok')}};
$('#bSrt').onclick=()=>$('#fSrt').click();
$('#fSrt').onchange=async e=>{const f=e.target.files[0];if(f){setRows(parseText(await f.text()));say('នាំចូល SRT បាន '+rows.length+' ឃ្លា','ok')}};
$('#bScript').onclick=()=>{setRows(parseText($('#script').value));say('បញ្ចូលបាន '+rows.length+' ឃ្លា','ok')};
$('#bAdd').onclick=()=>{const t=vid.currentTime||0;rows.push({s:t,e:t+3,o:'',t:'',v:'អ្នកសម្រាយរឿង'});rows.sort((a,b)=>a.s-b.s);render()};

/* ---------- Whisper AI (Speech to Text) ---------- */
let asr=null, asrModel='';
async function getAudio16k(){
  const buf=await vidFile.arrayBuffer();
  const AC=window.AudioContext||window.webkitAudioContext;
  const ac=new AC({sampleRate:16000});
  const ab=await ac.decodeAudioData(buf);
  const n=ab.numberOfChannels, len=ab.length, out=new Float32Array(len);
  for(let c=0;c<n;c++){const d=ab.getChannelData(c);for(let i=0;i<len;i++)out[i]+=d[i]/n}
  ac.close&&ac.close(); return out;
}
$('#bAsr').onclick=async function(){
  if(!vidFile) return say('សូមបើកវីដេអូជាមុនសិន','err');
  this.disabled=true;
  try{
    const model=$('#model').value;
    if(!asr||asrModel!==model){
      say('កំពុងទាញយក AI Model… (សូមរង់ចាំបន្តិច)');
      const {pipeline,env}=await import('https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2');
      env.allowLocalModels=false;
      asr=await pipeline('automatic-speech-recognition',model);
      asrModel=model;
    }
    say('កំពុងចម្រាញ់សំឡេងចេញពីវីដេអូ…');
    lastAudio=await getAudio16k();
    say('🧠 AI កំពុងស្តាប់ និងកំណត់ម៉ោង…');
    const opt={chunk_length_s:30,stride_length_s:5,return_timestamps:true,task:'transcribe'};
    if(S()[1]) opt.language=S()[1];
    const out=await asr(lastAudio,opt);
    const list=(out.chunks||[]).map(c=>{
      const s=c.timestamp[0]||0, e=(c.timestamp[1]==null)?s+3:c.timestamp[1];
      return {s,e:Math.max(e,s+.5),o:(c.text||'').trim()};
    }).filter(x=>x.o);
    if(!list.length) throw new Error('រកមិនឃើញសំឡេងនិយាយក្នុងវីដេអូ');
    setRows(list);
    say(`ស្តាប់បាន ${list.length} ឃ្លា — សូមចុចបកប្រែខ្មែរຕໍ່`,'ok');
  }catch(x){say(x.message||'មានបញ្តហាក្នុងការស្តាប់','err');console.error(x)}
  finally{this.disabled=false}
};

/* ---------- Translation (Google GTX Free) ---------- */
async function tr(text,tl){
  try{
    const r=await fetch('https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&dt=t&tl='+tl+'&q='+encodeURIComponent(text));
    if(!r.ok)throw 0; const j=await r.json(); return j[0].map(x=>x[0]).join('');
  }catch(e){return text}
}
$('#bTr').onclick=async function(){
  if(!rows.length) return say('មិនទាន់មានឃ្លាក្នុងតារាងទេ','err');
  this.disabled=true;
  try{
    for(let i=0;i<rows.length;i++){
      if(!rows[i].o.trim()) continue;
      say(`កំពុងបកប្រែ ${i+1}/${rows.length}…`);
      rows[i].t=await tr(rows[i].o,'km'); sync(); await sleep(100);
    }
    say('បកប្រែជាភាសាខ្មែរជោគជ័យ!','ok');
  }catch(x){say('បកប្រែមិនបាន','err')}finally{this.disabled=false}
};

/* ---------- Auto Guess Character ---------- */
$('#bGuess').onclick=()=>{
  rows.forEach(r=>{
    const txt=r.o.toLowerCase();
    if(/mom|dad|child|girl|boy/i.test(txt)) r.v='តួអង្គរង';
    else if(/old|grandfather|grandmother/i.test(txt)) r.v='តួចាស់';
    else r.v='អ្នកសម្រាយរឿង';
  });
  sync(); say('ស្មានតួអង្គរួចរាល់!','ok');
};

/* ---------- Gemini AI Analysis ---------- */
$('#bGem').onclick=async function(){
  const key=$('#gkey').value.trim();
  if(!key) return say('សូមបញ្ចូល Gemini API Key ជាមុនសិន','err');
  if(!rows.length) return say('គ្មានទិន្នន័យក្នុងតារាង','err');
  this.disabled=true;
  try{
    say('✨ Gemini កំពុងវិភាគសាច់រឿង និងបកប្រែ…');
    const prompt=`You are a professional movie recap translator. Translate these subtitle lines into natural, expressive Khmer suitable for a movie recap narrator/characters. Return ONLY a JSON array of strings containing the translated lines in order:`;
    const texts=rows.map(r=>r.o);
    const r=await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${encodeURIComponent(key)}`,{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({contents:[{parts:[{text:prompt+JSON.stringify(texts)}]}]})
    });
    const j=await r.json();
    const txt=j.candidates[0].content.parts[0].text.replace(/```json|```/g,'').trim();
    const arr=JSON.parse(txt);
    arr.forEach((t,i)=>{if(rows[i])rows[i].t=t});
    sync(); say('Gemini បកប្រែជោគជ័យ!','ok');
  }catch(e){say('Gemini មិនអាចដំណើរការបាន','err')}finally{this.disabled=false}
};

/* ---------- Speech Synthesis & Playback (Fixed Timing) ---------- */
function speak(r){
  const text=(r.t||r.o).trim(); if(!text) return;
  speechSynthesis.cancel();
  const P=PROF[r.v]||PROF['អ្នកសម្រាយរឿង'], v=pick(P.g);
  let rate=P.r;
  // Time-Stretch logic to fit exact mouth duration
  const targetDuration=Math.max(0.8, r.e - r.s);
  const estimatedDuration=text.length / 10; // ស្មា្ដនអត្រានិយាយភាសាខ្មែរ
  if(estimatedDuration > targetDuration){
    rate = Math.min(1.5, rate * (estimatedDuration / targetDuration));
  }
  
  const u=new SpeechSynthesisUtterance(text);
  if(v) u.voice=v; u.lang='km-KH'; u.rate=rate; u.pitch=P.p;
  speechSynthesis.speak(u);
}

let fired=new Set(), timer=null;
function tick(){
  const t=vid.currentTime;
  rows.forEach((r,i)=>{
    const on=t>=r.s && t<r.e;
    const el=$('#r'+i);
    if(el && el.classList.contains('on')!==on){
      el.classList.toggle('on',on);
      if(on) el.scrollIntoView({block:'nearest'});
    }
    if(!fired.has(i) && t>=r.s && t<r.s+0.4){
      fired.add(i);
      speak(r);
    }
  });
}

const applyVol=()=>{vid.muted=false;vid.volume=$('#mute').checked?0:+$('#vol').value};
vid.addEventListener('play',()=>{applyVol();clearInterval(timer);timer=setInterval(tick,50)});
vid.addEventListener('pause',()=>{clearInterval(timer);speechSynthesis.cancel()});
vid.addEventListener('seeked',()=>{fired.clear();speechSynthesis.cancel()});
$('#mute').onchange=applyVol;
$('#vol').oninput=()=>{$('#mute').checked=false;applyVol()};

$('#bPlay').onclick=()=>{
  if(!vid.src) return say('សូមបើកវីដេអូជាមុនសិន','err');
  if(!rows.length) return say('គ្មានឃ្លាសម្រាប់ចាក់ទេ','err');
  fired.clear(); vid.currentTime=Math.max(0, rows[0].s - 0.1); vid.play();
  say('កំពុងចាក់វីដេអូ និងសំឡេង AI…','ok');
};
$('#bStop').onclick=()=>{vid.pause();speechSynthesis.cancel();say('បានបញ្ឈប់','ok')};

$('#bDl').onclick=()=>{
  const s=rows.map((r,i)=>`${i+1}\n${fmt(r.s)} --> ${fmt(r.e)}\n${r.t||r.o}\n`).join('\n');
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([s],{type:'text/plain'}));a.download='voiceclone-recaps.srt';a.click();
};
</script>
</body>
</html>

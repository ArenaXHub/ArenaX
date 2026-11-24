/* AdhyX site script. One file for every page; each block runs only when its elements are on the page.
   Components marked "ported" come from the live arenax.in (deploy/index.html before v4). */
(function(){
  'use strict';
  var RM=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $=function(s,r){return (r||document).querySelector(s)}, $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
  var esc=function(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})};

  /* ---------- looks: Pearl (default) · Charcoal · Midnight; a stored "paper" falls back to Pearl ---------- */
  var LOOKS=['pearl','charcoal','midnight'];
  function setLook(v,save){
    if(LOOKS.indexOf(v)<0)v='pearl';
    document.documentElement.setAttribute('data-look',v);
    $$('.looks button').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.look===v))});
    if(save){try{localStorage.setItem('look',v)}catch(e){}}
  }
  var cur=document.documentElement.getAttribute('data-look')||'pearl';
  setLook(cur,false);
  $$('.looks button').forEach(function(b){b.addEventListener('click',function(){setLook(b.dataset.look,true)})});

  /* ---------- menu ---------- */
  var menu=$('#menu'),nav=$('#nav');
  if(menu&&nav){menu.addEventListener('click',function(){var o=nav.classList.toggle('open');menu.setAttribute('aria-expanded',String(o))});}

  /* ---------- stamps (scorecard, unit reports) ---------- */
  var stampN=0;
  function stamp(top,mid,bot,ink){
    var c=ink||'var(--mg-text)',id='sp'+(++stampN);
    return '<div class="stamp" aria-hidden="true"><svg viewBox="0 0 120 120"><defs><path id="'+id+'" d="M60,60 m-44,0 a44,44 0 1,1 88,0 a44,44 0 1,1 -88,0"/></defs>'+
      '<circle cx="60" cy="60" r="54" style="fill:none;stroke:'+c+'" stroke-width="2.5"/><circle cx="60" cy="60" r="48" style="fill:none;stroke:'+c+'" stroke-width="1" stroke-dasharray="2 3"/>'+
      '<text font-family="IBM Plex Mono,monospace" font-size="9.5" font-weight="500" style="fill:'+c+'" letter-spacing="1.5"><textPath href="#'+id+'" startOffset="2%">'+esc(top)+'</textPath></text>'+
      '<text x="60" y="56" text-anchor="middle" font-family="Manrope,sans-serif" font-size="12" font-weight="800" style="fill:'+c+'">'+esc(mid)+'</text>'+
      '<text x="60" y="72" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="8.5" style="fill:'+c+'">'+esc(bot)+'</text></svg></div>';
  }
  function fillStamps(root){$$('[data-stamp]',root).forEach(function(el){var a=el.dataset.stamp.split('|');el.innerHTML=stamp(a[0],a[1],a[2],a[3])});}

  /* ---------- hero phone: the live quick check (ported), with the class result ---------- */
  var scr=$('#screen');
  if(scr){
    var FB=['Not quite. A model carries its training hospital\'s patterns; a new hospital\'s patients differ, so accuracy usually drops.',
            'Yes. Different patients, different data: accuracy usually drops. That is why a local audit comes first.',
            'No. Nothing in the new hospital taught the model anything; accuracy cannot rise on its own.'];
    var OPTS=['Stay the same','Drop','Rise'], CLASS=[24,68,8];
    var ask=function(){
      scr.innerHTML='<div class="lvqhead"><span>Lesson 4 · Quick check</span><span>1 / 1</span></div>'+
        '<p class="lvqtext">A model trained in one hospital is used in another. Its accuracy will most likely…</p>'+
        '<div style="display:grid;gap:8px">'+OPTS.map(function(o,i){return '<button class="lvqopt" type="button" data-i="'+i+'" aria-pressed="false">'+o+'</button>'}).join('')+'</div>'+
        '<button class="lvqgo" type="button" disabled>Submit</button><p class="lvcopy">AdhyX · sample question</p>';
      var pick=-1,go=$('.lvqgo',scr);
      $$('.lvqopt',scr).forEach(function(b){b.addEventListener('click',function(){pick=+b.dataset.i;$$('.lvqopt',scr).forEach(function(x){x.setAttribute('aria-pressed',String(x===b))});go.disabled=false;})});
      go.addEventListener('click',function(){
        var right=pick===1,col=right?'#4C8C6A':'#C2604F';
        scr.innerHTML='<div class="lvres" role="status"><div class="orb" style="background:'+col+';box-shadow:0 0 30px '+col+'"></div>'+
          '<div class="kind">'+(right?'Right':'Not quite')+'</div><p class="kindline">'+FB[pick]+'</p>'+
          '<p class="clsh">YOUR CLASS SO FAR · SAMPLE</p><div class="cls">'+OPTS.map(function(o,i){return '<div class="'+(i===pick?'me':'')+'">'+o+'<b><i data-w="'+CLASS[i]+'"></i></b>'+CLASS[i]+'%</div>'}).join('')+'</div>'+
          '<p class="kindline">Topic: data shift · Lesson 4. Your teacher sees this topic in the class report.</p>'+
          '<button class="again" type="button">Try the full case</button></div>';
        setTimeout(function(){$$('.cls i',scr).forEach(function(i){i.style.width=i.dataset.w+'%'})},RM?0:120);
        $('.again',scr).addEventListener('click',function(){location.href='try.html'});
        var k=$('.kind',scr);if(k){k.setAttribute('tabindex','-1');k.focus({preventScroll:true});}
      });
    };
    ask();
  }

  /* ---------- editions (home): click a department; auto-steps until clicked ---------- */
  var CASES={"Nursing":"A ward model flags patients at risk of a fall. Last night it flagged 7 of 40. One patient it did not flag fell at 3 a.m. Keep using it?","Engineering":"A camera model checks parts on a line. Yesterday it passed 1,160 parts and flagged 23. One cracked part reached a customer. Keep using it?","Management":"A forecast model told the store to order 122 units of a product for the festival week. 61 are still on the shelf. Trust next week's number?","Pharmacy":"A label-reading model checks dispensed strengths. In a month it flagged 14 errors and missed one 5 mg vs 50 mg mix-up caught by a pharmacist. Keep using it?","Agriculture":"A crop-image model flags leaves for disease. It flagged 31 of 400 photos; a field visit found 4 of the 31 healthy and 2 unflagged plants diseased. Send the team where?","Hotel management":"A review classifier sorts guest feedback. It marked \"great, the AC worked for a full ten minutes\" as positive. Trust the weekly satisfaction score?","School (Class 9)":"The school's spam filter blocked the class teacher's email about the exam date and let a scam message through. Keep the filter on?"};
  var eds=$$('#editions .ed');
  if(eds.length){
    var edT=null,edi=0,edStopped=false,edStarted=false;
    var edShow=function(b,anim){eds.forEach(function(x){x.classList.toggle('on',x===b);x.setAttribute('aria-pressed',String(x===b))});var t=$('#ed-text');
      var f=function(){$('#ed-title').textContent=b.dataset.ed;t.textContent=CASES[b.dataset.ed];t.classList.remove('swap')};
      if(anim&&!RM){t.classList.add('swap');setTimeout(f,350)}else f();};
    eds.forEach(function(b,i){b.addEventListener('click',function(){edStopped=true;if(edT)clearInterval(edT);edi=i;edShow(b,true)})});
    edShow(eds[0],false);
    var edStart=function(){if(edStarted||RM)return;edStarted=true;edT=setInterval(function(){if(edStopped)return;edi=(edi+1)%eds.length;edShow(eds[edi],true)},3200)};
    window.__edStart=edStart;
  }

  /* ---------- AdhyX Live: slide + three phones in sync (ported) ---------- */
  if($('#slide')){
    var MX=function(hot){return '<div class="lvmx'+(hot?' hot':'')+'"><span></span><span class="lvh">Test: yes</span><span class="lvh">Test: no</span>'+
      '<span class="lvh lvrowh">Truth: yes</span><span class="lvc lvtp">True positive<small>caught</small></span><span class="lvc lvfn">False negative<small>missed</small></span>'+
      '<span class="lvh lvrowh">Truth: no</span><span class="lvc lvfp">False positive<small>false alarm</small></span><span class="lvc lvtn">True negative<small>cleared</small></span></div>'};
    var SCENE='<svg class="lvscene" viewBox="0 0 240 170" role="img" aria-label="A doctor holding a positive test tells a male patient he is pregnant">'+
'<rect x="0" y="0" width="240" height="170" rx="14" fill="#F5F5F7"/><rect x="0" y="138" width="240" height="32" rx="0" fill="#ECECEE"/>'+
'<g><rect x="34" y="78" width="54" height="70" rx="16" fill="#FFFFFF" stroke="#D2D2D7" stroke-width="2"/><path d="M50 80 L61 104 L72 80" fill="none" stroke="#D2D2D7" stroke-width="2"/>'+
'<path d="M52 84 C46 104 50 116 61 116 C72 116 76 104 70 84" fill="none" stroke="#1D1D1F" stroke-width="2.4"/><circle cx="61" cy="118" r="4" fill="#1D1D1F"/><circle cx="61" cy="58" r="17" fill="#E9C2A0"/>'+
'<path d="M44 54 C46 38 76 38 78 54 C72 46 52 46 44 54Z" fill="#3A3A3C"/><circle cx="55" cy="58" r="1.8" fill="#1D1D1F"/><circle cx="67" cy="58" r="1.8" fill="#1D1D1F"/>'+
'<path d="M56 66 Q61 70 66 66" fill="none" stroke="#1D1D1F" stroke-width="1.6" stroke-linecap="round"/><rect x="84" y="96" width="20" height="30" rx="3" fill="#FFFFFF" stroke="#1D1D1F" stroke-width="1.6"/>'+
'<rect x="88" y="102" width="12" height="5" rx="1" fill="#C2604F"/><text x="94" y="120" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="9" font-weight="700" fill="#C2604F">+</text></g>'+
'<g><rect x="152" y="80" width="56" height="68" rx="16" fill="#6E7F99"/><circle cx="180" cy="58" r="17" fill="#D9A77F"/><path d="M163 54 C163 40 197 40 197 54 L195 50 C188 44 172 44 165 50Z" fill="#2C2C2E"/>'+
'<path d="M166 62 C168 76 192 76 194 62 C190 70 170 70 166 62Z" fill="#2C2C2E"/><circle cx="174" cy="57" r="1.8" fill="#1D1D1F"/><circle cx="186" cy="57" r="1.8" fill="#1D1D1F"/>'+
'<ellipse cx="180" cy="66" rx="3" ry="3.6" fill="#1D1D1F"/><text x="212" y="44" font-family="Inter,Arial,sans-serif" font-size="20" font-weight="700" fill="#C79A45">?</text>'+
'<text x="180" y="122" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="16" fill="#FFFFFF">♂</text></g>'+
'<g><rect x="74" y="10" width="112" height="30" rx="15" fill="#1D1D1F"/><path d="M86 38 L80 50 L96 39Z" fill="#1D1D1F"/>'+
'<text x="130" y="30" text-anchor="middle" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="600" fill="#FFFFFF">“You\'re pregnant!”</text></g></svg>';
    var POLL='<div class="lvqslide"><div class="lvqart">'+SCENE+'</div><div class="lvqside2"><div class="lvqq">A doctor tells a man, “You are pregnant.” This is a…</div>'+
      '<div class="lvpoll" id="poll"><div>False positive<b><i></i></b><span>78%</span></div><div>False negative<b><i></i></b><span>15%</span></div><div>True negative<b><i></i></b><span>7%</span></div></div></div></div>';
    var SL=[
      {b:'<div class="lvbig">When a test is wrong, how is it wrong?</div><div class="lvsmall">Two kinds of mistake. One of them costs more.</div>',p:'When a test is wrong, how is it wrong?',o:null},
      {b:'<div class="lvsmall">Every yes/no test has four outcomes</div>'+MX(false),p:'Four outcomes: look at the board',o:null},
      {b:POLL,p:'A doctor tells a man, “You are pregnant.” This is a…',o:['False positive','False negative','True negative'],poll:[78,15,7]},
      {b:'<div class="lvsmall">The test said yes. The truth is no.</div>'+MX(true),p:'False positive: the test said yes, the truth is no.',o:null}];
    var slide=$('#slide'),mphs=$$('.lvmph'),si=1,picks=[0,0,1];
    var paint=function(){var S=SL[si];$('#sB').innerHTML=S.b;$('#sNo').textContent=(si+1)+' / '+SL.length;
      if(S.poll){setTimeout(function(){$$('#poll i').forEach(function(b,j){b.style.width=S.poll[j]+'%'})},RM?0:350)}
      mphs.forEach(function(m,j){$('.lvpn',m).textContent=si+1;$('.lvmt',m).innerHTML=(S.poll?'<span class="lvminiart">'+SCENE.replace('role="img"','aria-hidden="true"')+'</span>':'')+S.p.replace(/</g,'&lt;');
        $('.lvmb',m).innerHTML=S.o?S.o.map(function(o,x){return '<span class="'+(x===picks[j]?'lvon':'')+'">'+o+'</span>'}).join(''):'';});
      slide.classList.remove('lvswap');mphs.forEach(function(m){m.classList.remove('lvswap')});};
    paint();
    if(!RM)setInterval(function(){slide.classList.add('lvswap');mphs.forEach(function(m){m.classList.add('lvswap')});setTimeout(function(){si=(si+1)%SL.length;paint()},300)},4200);
  }

  /* ---------- the painted topic grid with focus and the side callout (ported) ---------- */
  var TOP=['AI basics','Predictions','Model errors','Privacy','Bias'],TOPS=['Basics','Predict','Errors','Privacy','Bias'];
  var STU=[['Riya',[92,85,70,55,78]],['Aarav',[80,62,48,30,40]],['Simran',[88,75,66,42,58]],['Rohit',[74,70,52,35,61]],['Priya',[95,90,84,72,80]],['Mohit',[60,55,40,38,45]],['Kavya',[90,82,76,68,70]],['Karan',[58,44,36,28,33]]];
  var NAMES=STU.map(function(s){return s[0]});
  var lvl=function(v){return v>=75?'lvg':v>=50?'lva':'lvr'};
  var lvlName=function(v){return v>=75?'strong':v>=50?'getting there':'needs help'};
  var DEFAULT_T=['Patient privacy: 5 of 8 below half.','One topic, most of the class. The rest of the unit landed; this lesson did not.','Re-teach Lesson 9 this week. A 20-minute version is in the kit.'];
  var TQ={c3:DEFAULT_T,
    c2:['Model errors: 3 students below half.','Most of the class can read a confusion matrix. Three cannot yet.','A short practice set of 10 questions, with feedback after each answer.'],
    c0:['AI basics: the whole class is through.','Every student is at or above half; most are strong.','Move on. Use these students as pair partners in the lab.'],
    c1:['Predictions: 2 students below half.','Most of the class reads a prediction well. Two need the ward example again.','Five minutes at the start of the next lab: the ward example, then one question.'],
    c4:['Bias: 3 students below half.','The same three as on model errors. One gap feeds the other.','Fold bias into the 30-minute session for the group: whose data trained the model?'],
    r7:['Karan needs you: weak in 4 of 5 topics.','Not one bad quiz: the same gap, unit after unit.','A one-to-one conversation this week, then the catch-up path in the kit.'],
    r4:['Priya is strong in every topic.','She has the whole unit, including the hard case on privacy.','Let her lead a peer group for the students who need privacy again.']};
  var INFO={Riya:['Riya: one topic to fix.','Privacy 55; four topics Strong or Getting there. Quiz 3: 85.','Point her to the Lesson 9 practice check. Proof Strong, Defence Strong.'],
    Aarav:['Aarav: three gaps, same as six others.','Model errors 48, privacy 30, bias 40. Quiz 3: 52.','Invite to the 30-minute "threshold by hand" session this week.'],
    Simran:['Simran: privacy only.','Privacy 42; the rest Working or better. Quiz 3: 66.','Lesson 9 practice check; pair with Priya for the defence rehearsal.'],
    Rohit:['Rohit: privacy, then errors.','Privacy 35, model errors 52. Quiz 3: 58.','Practice check first; one check-in before the Unit 3 defence.'],
    Priya:['Priya: ready for more.','Strong on four topics; privacy 72. Quiz 3: 84.','Open the Unit 4 challenge path. Her proof is one to show the class.'],
    Mohit:['Mohit: three gaps, same as six others.','Errors 40, privacy 38, bias 45. Quiz 3: 48.','Invite to the 30-minute session; check the practice check was attempted.'],
    Kavya:['Kavya: steady.','Strong on three, Getting there on two. Quiz 3: 77.','No action this week. Watch bias in Unit 4.'],
    Karan:['Karan: needs you this week.','Four topics below half. Quiz 3: 40.','Talk first, then the session. Check the phone had the practice check.']};
  function buildGrid(tg){
    tg.innerHTML='<span aria-hidden="true"></span>'+TOP.map(function(t,c){return '<button type="button" class="lvth" data-c="'+c+'" aria-label="'+t+'"><span class="lvlf">'+t+'</span><span class="lvsf" aria-hidden="true">'+TOPS[c]+'</span></button>'}).join('')+
      STU.map(function(s,r){return '<button type="button" class="lvsn" data-r="'+r+'">'+s[0]+'</button>'+s[1].map(function(x,c){return '<span class="lvtc" data-r="'+r+'" data-c="'+c+'" data-v="'+x+'" role="img" aria-label="'+s[0]+', '+TOP[c]+': '+x+', '+lvlName(x)+'">'+x+'</span>'}).join('')}).join('')+
      '<span class="lvsn cls">Class</span>'+TOP.map(function(_,c){return '<span class="lvav">'+Math.round(STU.reduce(function(a,s){return a+s[1][c]},0)/STU.length)+'%</span>'}).join('');
    var cells=$$('.lvtc',tg);
    tg.__paint=function(){if(tg.__painted)return;tg.__painted=true;cells.forEach(function(el){var r=+el.dataset.r,c=+el.dataset.c;setTimeout(function(){el.classList.add(lvl(+el.dataset.v))},RM?0:120*(r+c))})};
    return cells;
  }
  function setSide(ids,t){$('#'+ids[0]).textContent=t[0];$('#'+ids[1]).textContent=t[1];$('#'+ids[2]).textContent=t[2];}
  var grids=[];
  var hg=$('#tgrid');
  if(hg){
    var hcells=buildGrid(hg),HID=['qsT','qsP','qsA'];grids.push(hg);
    var focus=function(key,sel){var q=TQ[key];if(!q)return;setSide(HID,q);hg.classList.add('focus');hcells.forEach(function(el){el.classList.toggle('lvon',sel(el))})};
    $$('.lvth',hg).forEach(function(h){var c=h.dataset.c,f=function(){focus('c'+c,function(el){return el.dataset.c===c})};h.addEventListener('mouseenter',f);h.addEventListener('click',f);h.addEventListener('focus',f)});
    $$('.lvsn[data-r]',hg).forEach(function(h){var r=h.dataset.r,f=function(){if(TQ['r'+r])focus('r'+r,function(el){return el.dataset.r===r});else{setSide(HID,INFO[NAMES[r]]);hg.classList.add('focus');hcells.forEach(function(el){el.classList.toggle('lvon',el.dataset.r===r)})}};h.addEventListener('mouseenter',f);h.addEventListener('click',f);h.addEventListener('focus',f)});
    hg.addEventListener('mouseleave',function(){hg.classList.remove('focus');setSide(HID,DEFAULT_T)});
  }

  /* ---------- faculty: whole class view with the student filter, one student in detail; the two stay in sync ---------- */
  var DS={
   Riya:{q:85,c:59,t:[['AI basics',92,80],['Predictions',85,70],['Model errors',70,59],['Privacy',55,46],['Bias',78,58]],pl:'Strong',dl:'Strong',proof:'Fall-risk model: 40 patients, 2 thresholds',said:'It would fail on a patient who has never been admitted before.',fb:[['Privacy · 55','Point her to the Lesson 9 practice check; ask her to add a consent line to her Proof.'],['Model errors · 70','Fine. One more worked example in the lab.']],ok:['AI basics','Predictions','Bias'],act:'No session needed. Lesson 9 practice check by Friday; her Proof is one to show the class.'},
   Aarav:{q:52,c:59,t:[['AI basics',80,80],['Predictions',62,70],['Model errors',48,59],['Privacy',30,46],['Bias',40,58]],pl:'Working',dl:'Beginning',proof:'Fall-risk model: one threshold only',said:'I think it works because the accuracy was 80%.',fb:[['Model errors · 48','He equates accuracy with "good". Do the 2×2 by hand with him: 45 false alarms at 80% accuracy.'],['Privacy · 30','Lesson 9 practice check first; then ask what the ward may share with a vendor.'],['Bias · 40','Same session: whose data trained the model?']],ok:['AI basics'],act:'Invite to the 30-minute "threshold by hand" session; redo the Defence after it. Same three gaps as six others.'},
   Simran:{q:66,c:59,t:[['AI basics',88,80],['Predictions',75,70],['Model errors',66,59],['Privacy',42,46],['Bias',58,58]],pl:'Working',dl:'Working',proof:'Fall-risk model: 40 patients, 2 thresholds',said:'It would fail if the night shift stops checking the alarm.',fb:[['Privacy · 42','Lesson 9 practice check; pair with Priya for the defence rehearsal.']],ok:['AI basics','Predictions','Model errors'],act:'Practice check this week; one rehearsal with a Strong partner before the Unit 4 defence.'},
   Rohit:{q:58,c:59,t:[['AI basics',74,80],['Predictions',70,70],['Model errors',52,59],['Privacy',35,46],['Bias',61,58]],pl:'Working',dl:'Beginning',proof:'Fall-risk model: 40 patients, 1 threshold',said:'It fails when the data is wrong.',fb:[['Privacy · 35','Lesson 9 practice check; then one concrete case: the vendor asks for the ward list.'],['Model errors · 52','In the lab, make him name which number the night nurse cares about.']],ok:['Predictions','Bias'],act:'Practice check first; one check-in in the lab before the Unit 3 defence is re-recorded.'},
   Priya:{q:84,c:59,t:[['AI basics',95,80],['Predictions',90,70],['Model errors',84,59],['Privacy',72,46],['Bias',80,58]],pl:'Strong',dl:'Strong',proof:'Fall-risk model: 40 patients, 2 thresholds + a third',said:'It would fail on a ward with a different admission rule; the threshold would need to move.',fb:[['Privacy · 72','Good. Ask her to add the consent line to the class template.']],ok:['AI basics','Predictions','Model errors','Bias'],act:'Open the Unit 4 challenge path. Her Proof is one to show the class; pair her with Simran for the rehearsal.'},
   Mohit:{q:48,c:59,t:[['AI basics',60,80],['Predictions',55,70],['Model errors',40,59],['Privacy',38,46],['Bias',45,58]],pl:'Beginning',dl:'Beginning',proof:'Fall-risk model: incomplete',said:'I did not finish the audit.',fb:[['Model errors · 40','Start from the 2×2 by hand; the simulation came too fast for him.'],['Privacy · 38','Lesson 9 practice check; check it was attempted at all.'],['Bias · 45','Same session as the other six.']],ok:[],act:'Invite to the 30-minute session; check the practice check was attempted; the Proof is re-submitted after the session.'},
   Kavya:{q:77,c:59,t:[['AI basics',90,80],['Predictions',82,70],['Model errors',76,59],['Privacy',68,46],['Bias',70,58]],pl:'Strong',dl:'Working',proof:'Fall-risk model: 40 patients, 2 thresholds',said:'It would fail if the patient list is old.',fb:[['Bias · 70','Fine. Watch it in Unit 4; one question in the lab on whose data trained the model.']],ok:['AI basics','Predictions','Model errors','Privacy'],act:'No action this week. Her defence can move to Strong with one more "where would it fail" example.'},
   Karan:{q:40,c:59,t:[['AI basics',58,80],['Predictions',44,70],['Model errors',36,59],['Privacy',28,46],['Bias',33,58]],pl:'Beginning',dl:'Beginning',proof:'Not submitted',said:'(not recorded)',fb:[['Predictions · 44','Back to Lesson 7: what a prediction is, with the ward example.'],['Model errors · 36','The 2×2 by hand, with you, before the session.'],['Privacy · 28','Lesson 9 practice check; check the phone had it.']],ok:[],act:'Talk first, then the session. Four topics below half: this is the student to see this week.'}
  };
  function bars(rows){return rows.map(function(t){return '<div><span>'+t[0]+'</span><i><b class="'+(t[1]<60?'lo':'')+'" style="width:'+t[1]+'%"></b><u style="left:'+t[2]+'%"></u></i><em>'+t[1]+'</em></div>'}).join('')}
  var fg=$('#ftgrid'),sel=$('#sfilter'),dhost=$('#detail'),dtabs=$('#dtabs');
  var FID=['fqsT','fqsP','fqsA'];
  function chooseStudent(n,from){
    if(fg&&sel){
      if(from!=='select')sel.value=n||'all';
      $$('[data-r]',fg).forEach(function(el){el.classList.remove('keep')});
      if(!n||n==='all'){fg.classList.remove('one');setSide(FID,DEFAULT_T);}
      else{fg.classList.add('one');$$('[data-r="'+NAMES.indexOf(n)+'"]',fg).forEach(function(el){el.classList.add('keep')});setSide(FID,INFO[n]);}
    }
    if(dhost&&n&&n!=='all'&&DS[n]){
      var u=DS[n];
      var fb=u.fb.map(function(f){return '<div><i>'+f[0]+'</i><span>'+esc(f[1])+'</span></div>'}).join('')+(u.ok.length?'<div class="okk"><i>Strong</i><span>'+u.ok.join(', ')+'. Nothing to fix; say so.</span></div>':'');
      dhost.innerHTML='<div class="dc"><h3>'+n.toUpperCase()+' · QUIZ 3 AND TOPICS</h3><div class="big">'+u.q+'<small> / 100</small></div><p style="margin:-6px 0 0;font-size:13px;color:var(--muted)">Class average on quiz 3: '+u.c+'</p><div class="tp">'+bars(u.t)+'</div><p style="font-size:12px;color:var(--muted);margin:0">Gold tick = class average.</p></div>'+
        '<div class="dc"><h3>PROOF AND DEFENCE · UNIT 3</h3><div class="lv2"><span>Proof <b>'+u.pl+'</b></span><span>Defence <b>'+u.dl+'</b></span></div><p style="margin:0;font-weight:600">'+esc(u.proof)+'</p><h3 style="margin-top:4px">WHERE WOULD IT FAIL? — WHAT THEY SAID</h3><q>'+esc(u.said)+'</q></div>'+
        '<div class="dc"><h3>FEEDBACK, ALIGNED TO THE GAPS</h3><div class="fb">'+fb+'</div><h3 style="margin-top:4px">WHAT YOU DO</h3><div class="do">'+esc(u.act)+'</div></div>';
      if(dtabs)$$('.utab',dtabs).forEach(function(x){var on=x.dataset.s===n;x.classList.toggle('on',on);x.setAttribute('aria-selected',String(on));x.tabIndex=on?0:-1});
    }
  }
  if(fg){
    buildGrid(fg);grids.push(fg);
    $$('.lvsn[data-r]',fg).forEach(function(h){h.addEventListener('click',function(){chooseStudent(NAMES[+h.dataset.r])})});
    $$('.lvth',fg).forEach(function(h){h.addEventListener('click',function(){var c=h.dataset.c;chooseStudent('all');var q=TQ['c'+c];if(q)setSide(FID,q);fg.classList.add('focus');$$('.lvtc',fg).forEach(function(el){el.classList.toggle('lvon',el.dataset.c===c)})})});
    fg.addEventListener('mouseleave',function(){fg.classList.remove('focus')});
  }
  if(sel)sel.addEventListener('change',function(){chooseStudent(sel.value,'select')});
  if(dtabs){
    dtabs.addEventListener('click',function(e){var t=e.target.closest('.utab');if(t)chooseStudent(t.dataset.s)});
    tabKeys(dtabs,function(t){chooseStudent(t.dataset.s)});
  }
  if(dhost){chooseStudent('Aarav','init');if(fg)chooseStudent('all','init');}
  function tabKeys(list,activate){
    list.addEventListener('keydown',function(e){var tabs=$$('[role="tab"]',list),i=tabs.indexOf(document.activeElement);if(i<0)return;
      var n=e.key==='ArrowRight'?i+1:e.key==='ArrowLeft'?i-1:e.key==='Home'?0:e.key==='End'?tabs.length-1:-9;if(n===-9)return;e.preventDefault();n=(n+tabs.length)%tabs.length;tabs[n].focus();activate(tabs[n]);});
  }

  /* ---------- students: unit reports for every unit ---------- */
  var uhost=$('#ureports'),utabs=$('#utabs');
  if(uhost&&utabs){
    var U={
     1:{t:'AI around a ward',q:62,c:54,chg:'First quiz of the course',d:'12 Sep',topics:[['What AI is',70,60],['Where it sits',75,62],['Human in loop',58,50],['Night-shift gaps',48,44],['Asking the model',62,52]],fix:'One topic to fix: night-shift gaps',act:'Revisit Lesson 2 practice check · 20 min',proof:'Where AI already sits in a ward',ptype:'Checklist',pl:'WORKING',dl:'Strong',quote:'It would fail at night, when nobody checks the monitor\'s suggestion.'},
     2:{t:'Reading AI summaries',q:70,c:58,chg:'Up from 62 in Unit 1',d:'28 Sep',topics:[['Summaries',78,64],['Comparing',74,60],['Missing lines',60,52],['Allergy flags',55,47],['Length vs detail',72,58]],fix:'One topic to fix: allergy flags',act:'Revisit Lesson 5 practice check · 20 min',proof:'Two triage summaries, compared',ptype:'Comparison',pl:'STRONG',dl:'Working',quote:'The AI summary was shorter and missed the allergy line; mine was longer but had it.'},
     3:{t:'AI for Health Sciences',q:85,c:59,chg:'Up from 70 in Unit 2',d:'14 Oct',topics:[['AI basics',92,80],['Predictions',85,70],['Model errors',70,59],['Privacy',55,46],['Bias',78,58]],fix:'One topic to fix: privacy',act:'Revisit Lesson 9 practice check · 20 min',proof:'Fall-risk model: 40 patients, 2 thresholds',ptype:'Error analysis',pl:'STRONG',dl:'Strong',quote:'It would fail on a patient who has never been admitted before.'},
     4:{t:'Chatbots in care',q:80,c:63,chg:'Down from 85 in Unit 3',d:'2 Nov',topics:[['Chatbot scope',88,70],['When to refuse',82,66],['Language gaps',65,55],['Escalation',78,60],['Decision memo',84,64]],fix:'One topic to fix: language gaps',act:'Revisit Lesson 12 practice check · 20 min',proof:'Should the chatbot answer this?',ptype:'Decision memo',pl:'WORKING',dl:'Working',quote:'It would fail if the patient writes in Hindi and the chatbot only reads English.'},
     5:{t:'Data and consent',q:93,c:68,chg:'Up from 80 in Unit 4',d:'8 Nov',topics:[['Survey design',95,72],['Consent',92,70],['Reading a chart',88,66],['Hidden answers',90,62],['Data story',94,70]],fix:'Nothing to fix this unit',act:'Unit 5 challenge path is open',proof:'Our class\'s consent survey',ptype:'Data story',pl:'STRONG',dl:'Working',quote:'Twelve of forty said yes without reading; the chart hides that unless you ask.'}
    };
    var ucard=function(n){var u=U[n];var good=u.topics.filter(function(t){return t[1]>=60}).length;var above=u.topics.filter(function(t){return t[1]>t[2]}).length;
      var rows=u.topics.map(function(t){var help=t[1]<60?';background:var(--help)':'';return '<div>'+t[0]+'<b><i style="width:'+t[1]+'%'+help+'"></i><u style="left:'+t[2]+'%"></u></b>'+t[1]+'</div>'}).join('');
      return '<div class="lvframe stu'+(n===3?' on':'')+'" data-u="'+n+'" role="tabpanel" id="unit-'+n+'" aria-labelledby="utab-'+n+'">'+
       '<div class="lvftop"><b>Unit '+n+' · '+u.t+' · Riya S.</b><span>B.Sc. Nursing · Sem 2 · Section A · quiz '+n+', '+u.d+' · sample</span></div><div class="lvins">'+
       '<div class="lvcard"><p class="lvwhat">My quiz '+n+'</p><div class="lvviz"><div class="lvvbig">'+u.q+'<small> / 100</small></div></div><div><h3>'+u.chg+'</h3><p>Class average on this quiz: '+u.c+'. Counts towards continuous assessment.</p></div><span class="lvdo">'+good+' of 5 topics Strong or Getting there</span></div>'+
       '<div class="lvcard"><p class="lvwhat">My topics vs the class</p><div class="lvviz"><div class="lvpair stu-pair">'+rows+'</div></div><div><h3>'+u.fix+'</h3><p>The tick on each bar is the class average. You are above it on '+above+' topics.</p></div><span class="lvdo">'+u.act+'</span></div>'+
       '<div class="lvcard"><p class="lvwhat">My proof and defence · Unit '+n+'</p><div class="lvviz"><div class="stu-stamp" data-stamp="VERIFIED · PROOF · UNIT '+n+' ·|'+u.pl+'|teacher"></div></div><div><h3>'+esc(u.proof)+'</h3><p>'+u.ptype+' · Proof '+(u.pl==='STRONG'?'Strong':'Working')+' · Defence '+u.dl+'. “'+esc(u.quote)+'”</p></div><span class="lvdo">Stamped on your scorecard</span></div>'+
       '</div></div>';};
    uhost.innerHTML=[1,2,3,4,5].map(ucard).join('');
    $$('.utab',utabs).forEach(function(t){t.setAttribute('aria-controls','unit-'+t.dataset.u)});
    var pickUnit=function(t){$$('.utab',utabs).forEach(function(x){var on=x===t;x.classList.toggle('on',on);x.setAttribute('aria-selected',String(on));x.tabIndex=on?0:-1});$$('.lvframe',uhost).forEach(function(f){f.classList.toggle('on',f.dataset.u===t.dataset.u)});};
    utabs.addEventListener('click',function(e){var t=e.target.closest('.utab');if(t)pickUnit(t)});
    tabKeys(utabs,pickUnit);
  }
  fillStamps(document);

  /* ---------- try: the case as a self-contained simulation ---------- */
  var lesson=$('#lesson');
  if(lesson){
    var step=0,steps=$$('.l-step',lesson),ltabs=$$('.bar button',lesson),prev=$('#prev'),next=$('#next');
    var show=function(){steps.forEach(function(s,i){s.hidden=i!==step});ltabs.forEach(function(t,i){t.classList.toggle('on',i===step);t.setAttribute('aria-current',i===step?'step':'false')});prev.disabled=step===0;next.textContent=step===steps.length-1?'Done':'Next';};
    next.addEventListener('click',function(){if(step<steps.length-1){step++;show();}else{location.href='students.html';}});
    prev.addEventListener('click',function(){if(step>0){step--;show();}});
    ltabs.forEach(function(t,i){t.addEventListener('click',function(){step=i;show();})});
    show();
    var tt=$('#teacher-toggle');
    var setTeacher=function(on){lesson.classList.toggle('teacher-view',on);tt.checked=on};
    tt.addEventListener('change',function(){setTeacher(tt.checked)});
    if(/[?&]view=teacher\b/.test(location.search))setTeacher(true);
    var ch=$$('[data-choice]',lesson);ch.forEach(function(b){b.addEventListener('click',function(){ch.forEach(function(x){x.setAttribute('aria-pressed','false')});b.setAttribute('aria-pressed','true');$('#fb0').classList.add('show');})});
    var pc=$$('[data-pc]',lesson),fb4=$('#fb4');
    var pcText={a:'Not this one. Lowering the threshold flags more people, so more of the at-risk patients get caught: recall goes up.',b:'Yes. More flags means more false alarms among them, so precision goes down. That is the trade-off the night nurse manages.',c:'That number does not change with the threshold; it is a fact about the patients, not about the model.'};
    pc.forEach(function(b){b.addEventListener('click',function(){pc.forEach(function(x){x.setAttribute('aria-pressed','false')});b.setAttribute('aria-pressed','true');fb4.textContent=pcText[b.dataset.pc];fb4.classList.add('show');})});
    var snaps=[{th:'0.2',tp:8,fn:0,fp:9,tn:23},{th:'0.4',tp:7,fn:1,fp:4,tn:28},{th:'0.6',tp:6,fn:2,fp:1,tn:31},{th:'0.8',tp:4,fn:4,fp:0,tn:32},{th:'0.9',tp:2,fn:6,fp:0,tn:32}];
    var th=$('#th');
    var upd=function(){var s=snaps[+th.value];$('#thv').textContent=s.th;th.setAttribute('aria-valuetext','Threshold '+s.th);['tp','fn','fp','tn'].forEach(function(k){$('#'+k).textContent=s[k]});
      var acc=Math.round((s.tp+s.tn)/40*100),prec=s.tp+s.fp?Math.round(s.tp/(s.tp+s.fp)*100):0,rec=Math.round(s.tp/(s.tp+s.fn)*100);
      $('#acc').textContent=acc+'%';$('#prec').textContent=prec+'%';$('#rec').textContent=rec+'%';};
    th.addEventListener('input',upd);upd();
  }

  /* ---------- reveal on scroll (ported), spine auto-step, grid paint, chart draw ---------- */
  $$('.band .wrap').forEach(function(w){Array.prototype.forEach.call(w.children,function(c){
    if(c.classList.contains('nextprev'))return;
    if(/(^| )(grid-3|grid-2|grid-4|editions|seals|outs|jsteps|kap)( |$)/.test(c.className))c.classList.add('rv-k');else c.classList.add('rv');});});
  var onShow=function(t){
    var g=t.querySelector&&t.querySelector('.lvtgrid');if(g&&g.__paint)g.__paint();
    var ca=t.classList.contains('ca')?t:t.querySelector('.ca');if(ca)ca.classList.add('drawn');
    $$('.stamp',t).forEach(function(x,i){x.style.animationDelay=(.15*i)+'s';x.classList.add('pop')});
    if(t.querySelector&&t.querySelector('#editions')&&window.__edStart)window.__edStart();
  };
  if('IntersectionObserver' in window && !RM){
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;var t=e.target;t.classList.remove('pre');io.unobserve(t);onShow(t);})},{threshold:0,rootMargin:'0px 0px -10% 0px'});
    $$('.rv,.rv-k').forEach(function(t){if(t.getBoundingClientRect().top>window.innerHeight*0.9)t.classList.add('pre');io.observe(t)});
  } else {
    $$('.rv,.rv-k').forEach(onShow);
  }
  grids.forEach(function(g){if(RM&&g.__paint)g.__paint()});
  var sp=$$('.spine.auto a'),spi=0,spT;
  if(sp.length&&!RM){var spStep=function(){sp.forEach(function(a,i){a.classList.toggle('on',i===spi)});spi=(spi+1)%sp.length};spStep();spT=setInterval(spStep,2600);
    var spn=$('.spine.auto');spn.addEventListener('mouseenter',function(){clearInterval(spT)});spn.addEventListener('mouseleave',function(){spT=setInterval(spStep,2600)});}

  /* ---------- forms: post to LEADS_URL; mailto fallback when the URL is empty or the post fails ---------- */
  var CFG=window.SITE_CONFIG||{};
  var LEADS_URL=(CFG.LEADS_URL||'').trim(), CONTACT=CFG.CONTACT_EMAIL||'contactarenax@gmail.com';
  function mailtoHref(form,fields){
    var lines=Object.keys(fields).filter(function(k){return k!=='form'&&k!=='page'&&fields[k]}).map(function(k){return k.charAt(0).toUpperCase()+k.slice(1).replace(/_/g,' ')+': '+fields[k]});
    var subj='[AdhyX] '+fields.form+' · '+(fields.institution||'');
    return 'mailto:'+CONTACT+'?subject='+encodeURIComponent(subj)+'&body='+encodeURIComponent(lines.join('\n'));
  }
  function collect(f){var o={};$$('input,select,textarea',f).forEach(function(el){if(!el.name||el.type==='submit')return;o[el.name]=(el.value||'').trim()});return o;}
  $$('form.lead-form').forEach(function(f){
    f.addEventListener('submit',function(e){
      e.preventDefault();
      var ok=$('.ok',f),err=$('.form-err',f),btn=$('button[type="submit"]',f);
      if(!f.checkValidity()){if(err){err.textContent='Please fill the required fields and a valid email.';err.hidden=false}f.reportValidity&&f.reportValidity();return;}
      if(err)err.hidden=true;
      var data=collect(f);
      if(data.website)return; // honeypot: a person never fills this
      data.form=f.dataset.form; data.page=location.pathname.split('/').pop()||'index.html';
      var href=mailtoHref(f,data);
      var done=function(viaMail){
        ok.classList.add('show');
        var note=$('.mailnote',ok);
        if(viaMail){note.innerHTML='Your email app should open with these details filled in; press send. If it does not, write to <a href="'+href+'">'+CONTACT+'</a>.';note.hidden=false;location.href=href;}
        else if(note){note.hidden=true;}
        ok.setAttribute('tabindex','-1');ok.focus({preventScroll:false});
        if(btn)btn.disabled=true;
      };
      if(!LEADS_URL){done(true);return;}
      if(btn)btn.disabled=true;
      var body=new URLSearchParams();Object.keys(data).forEach(function(k){body.append(k,data[k])});
      var ctl=('AbortController' in window)?new AbortController():null,timer=ctl?setTimeout(function(){ctl.abort()},12000):null;
      fetch(LEADS_URL,{method:'POST',body:body,redirect:'follow',signal:ctl?ctl.signal:undefined})
        .then(function(r){return r.text().then(function(t){var j={};try{j=JSON.parse(t)}catch(x){};if(!r.ok||!j.ok)throw new Error('not ok');})})
        .then(function(){done(false)})
        .catch(function(){if(btn)btn.disabled=false;done(true)})
        .then(function(){if(timer)clearTimeout(timer)});
    });
  });
})();

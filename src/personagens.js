(function(){
var d=document,$=function(i){return d.getElementById(i)};
var data=JSON.parse($('pdata').textContent),li=Array.prototype.slice.call(d.querySelectorAll('#bg li'));
var fg=$('fg'),fm=$('fm'),fq=$('fq'),bc=$('bc'),dlg=$('dlg'),di=$('di');
/* filtros: grupo, marca/tema (só as do grupo escolhido) e busca por texto */
function norm(s){return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'')}
li.forEach(function(x){x._q=norm(x.dataset.q)});
function apply(){
  var g=fg.value,m=fm.value,q=norm(fq.value.trim()),n=0;
  li.forEach(function(x){var ok=(!g||x.dataset.g===g)&&(!m||x.dataset.m===m)&&(!q||q.split(/\s+/).every(function(w){return x._q.indexOf(w)>-1}));
    x.hidden=!ok;if(ok)n++});
  bc.textContent=n+(n===1?' arte':' artes');
}
fg.addEventListener('change',function(){
  Array.prototype.forEach.call(fm.options,function(o){if(o.value)o.hidden=!!fg.value&&o.dataset.g!==fg.value});
  if(fm.selectedOptions[0]&&fm.selectedOptions[0].hidden)fm.value='';apply()});
fm.addEventListener('change',apply);fq.addEventListener('input',apply);
/* clique abre a versão grande e o link do original no Drive */
$('bg').addEventListener('click',function(ev){var b=ev.target.closest('button');if(!b)return;var it=data[+b.dataset.i];
  di.src=it[0];di.width=it[1];di.height=it[2];di.alt=it[4];
  $('dt').textContent=it[4]+' · '+it[5]+' / '+it[6]+(it[7]?' / '+it[7]:'')+' · '+it[1]+'x'+it[2]+(it[8]?' · fundo transparente':'');
  $('dd').href=it[3];$('dw').href=it[0];
  if(dlg.showModal)dlg.showModal();else dlg.setAttribute('open','')});
$('dx').addEventListener('click',function(){dlg.close?dlg.close():dlg.removeAttribute('open')});
dlg.addEventListener('click',function(ev){if(ev.target===dlg)dlg.close()});
dlg.addEventListener('close',function(){di.removeAttribute('src')});
})();

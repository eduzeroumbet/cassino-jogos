(function(){
var d=document,w=window,RM=w.matchMedia&&w.matchMedia('(prefers-reduced-motion: reduce)').matches;
function $$(s,c){return Array.prototype.slice.call((c||d).querySelectorAll(s))}
function ev(n,p){try{if(w.gtag)w.gtag('event',n,p||{})}catch(e){}}
/* efeitos do hero (partículas leves, só CSS) */
$$('.fx').forEach(function(fx){
  var n=fx.classList.contains('fx-grid')?14:(w.innerWidth<720?14:22),h='';
  var cols=['#FF6FB5','#F5B942','#3DD6C4','#C9A2FF','#FF3D5A'];
  for(var i=0;i<n;i++){
    var s=(fx.classList.contains('fx-gates')?3:6+Math.random()*12)|0;
    if(fx.classList.contains('fx-grid'))s=18+(Math.random()*16|0);
    h+='<span style="--x:'+(Math.random()*100).toFixed(1)+'%;--y:'+(Math.random()*90).toFixed(1)+'%;--s:'+s+'px;--d:'+(5+Math.random()*7).toFixed(1)+'s;--w:'+(-Math.random()*10).toFixed(1)+'s;--c:'+cols[i%5]+'"></span>';
  }
  if(!RM)fx.innerHTML=h;
});
/* foco das palavras (Focus Reveal) */
setTimeout(function(){$$('.focus').forEach(function(e){e.classList.add('on')})},RM?0:900);
/* parallax do hero + barra fixa + caminho dos passos */
var hero=d.querySelector('.hero'),sticky=d.querySelector('.sticky'),steps=d.querySelector('.steps'),tick=false;
function frame(){
  tick=false;var vh=w.innerHeight,y=w.scrollY||w.pageYOffset;
  if(hero&&!RM){var p=Math.min(1,y/Math.max(1,hero.offsetHeight));hero.style.setProperty('--p',p.toFixed(3))}
  if(sticky){var fin=d.querySelector('.final'),show=y>vh*.8;if(fin){var r=fin.getBoundingClientRect();if(r.top<vh&&r.bottom>0)show=false}sticky.classList.toggle('show',show)}
  if(steps){var r2=steps.getBoundingClientRect(),sp=Math.max(0,Math.min(1,(vh*.75-r2.top)/r2.height));steps.style.setProperty('--sp',sp.toFixed(3));
    $$('.step',steps).forEach(function(s){s.classList.toggle('on',s.getBoundingClientRect().top<vh*.72)})}
}
w.addEventListener('scroll',function(){if(!tick){tick=true;requestAnimationFrame(frame)}},{passive:true});
frame();
if(steps){var pth=steps.querySelector('path.draw');if(pth){var L=pth.getTotalLength?pth.getTotalLength():600;steps.style.setProperty('--len',L)}}
/* métricas: barras, níveis e contadores (Lime Metrics) */
function count(el){var to=parseFloat(el.dataset.to),dec=(el.dataset.to.split('.')[1]||'').length,t0=null,D=1300;
  function f(t){if(!t0)t0=t;var k=Math.min(1,(t-t0)/D),e=1-Math.pow(1-k,3),v=(to*e).toFixed(dec);el.textContent=Number(v).toLocaleString('pt-BR',{minimumFractionDigits:dec,maximumFractionDigits:dec});if(k<1)requestAnimationFrame(f)}
  if(RM){el.textContent=Number(to).toLocaleString('pt-BR',{minimumFractionDigits:dec});return}requestAnimationFrame(f)}
var io=('IntersectionObserver' in w)?new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;var t=e.target;io.unobserve(t);
  if(t.matches('.bar i'))t.style.width=t.dataset.w+'%';
  else if(t.matches('[data-to]'))count(t);
  else if(t.matches('video')){t.src=t.dataset.src;t.play&&t.play().catch(function(){})}
})},{rootMargin:'0px 0px -10% 0px'}):null;
$$('.bar i,[data-to],video[data-src]').forEach(function(e){if(io)io.observe(e);else{if(e.dataset.w)e.style.width=e.dataset.w+'%';if(e.dataset.src)e.src=e.dataset.src}});
/* cartões expansíveis (Expanded Cards) */
$$('.xcard').forEach(function(b){b.addEventListener('click',function(){var on=b.getAttribute('aria-expanded')==='true';
  $$('.xcard',b.parentNode).forEach(function(o){o.setAttribute('aria-expanded','false')});b.setAttribute('aria-expanded',on&&w.innerWidth<1024?'false':'true');ev('lp_feature',{item:b.dataset.k})})});
/* cliques nos CTAs */
$$('[data-cta]').forEach(function(a){a.addEventListener('click',function(){ev('lp_cta',{cta:a.dataset.cta,page:d.body.dataset.page})})});
$$('.faq details').forEach(function(x){x.addEventListener('toggle',function(){if(x.open)ev('lp_faq',{q:x.querySelector('summary').textContent})})});
/* GA4 carregado depois da interação ou do ocioso, para não pesar no LCP */
var GA=d.body.dataset.ga;
if(GA){var loaded=false;function ga(){if(loaded)return;loaded=true;w.dataLayer=w.dataLayer||[];w.gtag=function(){w.dataLayer.push(arguments)};w.gtag('js',new Date());w.gtag('config',GA,{page_title:d.title});
  var s=d.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+GA;d.head.appendChild(s)}
  ['scroll','touchstart','pointerdown','keydown'].forEach(function(n){w.addEventListener(n,ga,{once:true,passive:true})});setTimeout(ga,3500)}
})();

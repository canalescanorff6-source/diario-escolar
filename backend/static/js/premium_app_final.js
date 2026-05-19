// Diário IA Escolar Premium — JS único final 1221-1280.


// ===== diario_1001_1080_conclusao_total.js =====

// ETAPAS 1001-1080 — pequenos reforços de UX sem dependências externas
(function(){
  function bindPrint(){
    document.querySelectorAll('[data-final-print]').forEach(function(btn){
      btn.addEventListener('click', function(ev){ ev.preventDefault(); window.print(); });
    });
  }
  function bindFilter(){
    document.querySelectorAll('[data-final-filter]').forEach(function(input){
      var target = document.querySelector(input.getAttribute('data-final-filter'));
      if(!target) return;
      input.addEventListener('input', function(){
        var q = input.value.toLowerCase().trim();
        target.querySelectorAll('[data-final-row]').forEach(function(row){
          row.style.display = row.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
        });
      });
    });
  }
  document.addEventListener('DOMContentLoaded', function(){ bindPrint(); bindFilter(); });
})();


// ===== diario_1081_1160_render_ready.js =====

(() => {
  document.documentElement.dataset.renderReady1081 = "true";
  const cards = document.querySelectorAll('.render1081-card, .render1081-panel');
  cards.forEach((card, index) => { card.style.animationDelay = `${Math.min(index * 25, 300)}ms`; });
})();


// ===== diario_861_900_operacao.js =====

(function(){
  function qs(sel, ctx){return Array.prototype.slice.call((ctx||document).querySelectorAll(sel));}

  // Seleção rápida de presença na aula oficial.
  qs('[data-set-presenca]').forEach(function(btn){
    btn.addEventListener('click', function(){
      var value = btn.getAttribute('data-set-presenca') || 'P';
      qs('select[name^="status_"]').forEach(function(select){ select.value = value; });
    });
  });

  // Filtro leve para tabelas premium sem depender de biblioteca.
  qs('[data-table-filter]').forEach(function(input){
    var target = document.querySelector(input.getAttribute('data-table-filter'));
    if(!target) return;
    input.addEventListener('input', function(){
      var term = input.value.toLowerCase().trim();
      qs('tbody tr', target).forEach(function(row){
        row.style.display = row.textContent.toLowerCase().indexOf(term) >= 0 ? '' : 'none';
      });
    });
  });

  // Scroll suave para blocos internos do fluxo.
  qs('[data-scroll-to]').forEach(function(link){
    link.addEventListener('click', function(ev){
      var el = document.querySelector(link.getAttribute('data-scroll-to'));
      if(el){ ev.preventDefault(); el.scrollIntoView({behavior:'smooth', block:'start'}); }
    });
  });
})();


// ===== diario_901_960_finalizacao.js =====

(function(){
  function filtrarLista(input){
    const alvo = input.getAttribute('data-filter-target');
    if(!alvo) return;
    const termo = (input.value || '').toLowerCase().trim();
    document.querySelectorAll(alvo).forEach(function(item){
      const txt = (item.textContent || '').toLowerCase();
      item.style.display = !termo || txt.includes(termo) ? '' : 'none';
    });
  }
  document.addEventListener('input', function(ev){
    const el = ev.target;
    if(el && el.matches('[data-filter-target]')) filtrarLista(el);
  });
  document.addEventListener('click', function(ev){
    const btn = ev.target.closest('[data-print-page]');
    if(btn){ ev.preventDefault(); window.print(); }
  });
  document.querySelectorAll('[data-pct]').forEach(function(el){
    const pct = Math.max(0, Math.min(100, Number(el.getAttribute('data-pct') || 0)));
    el.style.setProperty('--pct', pct + '%');
  });
})();


// ===== diario_961_1000_blindagem_final.js =====

(function(){
  function ready(fn){ if(document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  ready(function(){
    document.querySelectorAll('.mega961-progress').forEach(function(bar){
      var pct = parseFloat(bar.getAttribute('data-pct') || '0');
      pct = Math.max(0, Math.min(100, isNaN(pct) ? 0 : pct));
      var span = bar.querySelector('span');
      if(span) requestAnimationFrame(function(){ span.style.width = pct + '%'; });
    });
    document.querySelectorAll('[data-mega961-filter]').forEach(function(input){
      input.addEventListener('input', function(){
        var term = input.value.toLowerCase();
        document.querySelectorAll('.mega961-row').forEach(function(row){
          row.style.display = row.textContent.toLowerCase().includes(term) ? '' : 'none';
        });
      });
    });
  });
})();


// ===== diario_ia_pwa.js =====

(function(){if('serviceWorker' in navigator){window.addEventListener('load',function(){navigator.serviceWorker.register('/static/js/diario_ia_sw.js').catch(function(){})})}})();


// ===== POLIMENTO FINAL — navegação sem salto, sidebar exata, scroll-box e UI limpa =====
(function(){
  function normalizePath(value){
    try { return (new URL(value, window.location.origin).pathname || '/').replace(/\/$/, '') || '/'; }
    catch(e){ return String(value || '').split('?')[0].split('#')[0].replace(/\/$/, '') || '/'; }
  }
  function parsePaths(value){
    return String(value || '').split('|').map(function(x){ return normalizePath(x.trim()).toLowerCase(); }).filter(Boolean);
  }
  function matchPath(current, candidate){
    if(!candidate) return false;
    if(candidate === '/') return current === '/';
    return current === candidate || current.indexOf(candidate + '/') === 0;
  }
  function markSidebarActive(){
    var current = normalizePath(window.location.pathname).toLowerCase();
    var links = Array.prototype.slice.call(document.querySelectorAll('.sidebar a[href]'));
    var best = null, bestScore = -1;
    links.forEach(function(a){ a.classList.remove('active'); a.removeAttribute('aria-current'); a.removeAttribute('data-active'); });
    links.forEach(function(a){
      var paths = parsePaths(a.getAttribute('data-active-paths'));
      if(!paths.length) paths = [normalizePath(a.getAttribute('href')).toLowerCase()];
      paths.forEach(function(p){
        if(matchPath(current, p)){
          var score = p.length + (current === p ? 1000 : 0);
          if(score > bestScore){ best = a; bestScore = score; }
        }
      });
    });
    if(best){
      best.classList.add('active');
      best.setAttribute('aria-current', 'page');
      best.setAttribute('data-active', 'true');
      try { best.scrollIntoView({block:'nearest', inline:'nearest'}); } catch(e) {}
    }
  }
  function bindNoJump(){
    document.addEventListener('click', function(ev){
      var a = ev.target && ev.target.closest ? ev.target.closest('a[href]') : null;
      if(a){
        var href = (a.getAttribute('href') || '').trim();
        if(href === '' || href === '#' || href.toLowerCase().indexOf('javascript:void') === 0){ ev.preventDefault(); return false; }
        if(a.closest('.sidebar')){
          Array.prototype.slice.call(document.querySelectorAll('.sidebar a.active')).forEach(function(x){ x.classList.remove('active'); x.removeAttribute('aria-current'); x.removeAttribute('data-active'); });
          a.classList.add('active'); a.setAttribute('aria-current','page'); a.setAttribute('data-active','true');
        }
      }
    }, true);
  }
  function enhanceScrollBlocks(){
    var selectors = ['.clean-list','.table-wrap','.table-responsive','.premium-scroll','.scroll-box','.lista-scroll','.panel .clean-list','.card .clean-list','.ia-document-meta','.diario-real-actions','.recommendations','.ia-list','.long-list'];
    selectors.forEach(function(sel){
      Array.prototype.slice.call(document.querySelectorAll(sel)).forEach(function(el){
        if(!el.classList.contains('premium-scrollbox')) el.classList.add('premium-scrollbox');
      });
    });
  }
  function ready(fn){ if(document.readyState !== 'loading') fn(); else document.addEventListener('DOMContentLoaded', fn); }
  ready(function(){ markSidebarActive(); bindNoJump(); enhanceScrollBlocks(); });
  window.diarioIAMarkSidebarActive = markSidebarActive;
})();

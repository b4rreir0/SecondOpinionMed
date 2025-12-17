(function(){
  function ready(fn){
    if (document.readyState !== 'loading') { fn(); } else { document.addEventListener('DOMContentLoaded', fn); }
  }

  ready(function(){
    var overlay = document.getElementById('page-loading-overlay');
    if (!overlay) return;

    function show(){ overlay.style.display = 'flex'; overlay.setAttribute('aria-hidden','false'); }
    function hide(){ overlay.style.display = 'none'; overlay.setAttribute('aria-hidden','true'); }

    // Hide on load/pageshow
    window.addEventListener('load', hide);
    window.addEventListener('pageshow', function(e){ if (!e.persisted) hide(); else hide(); });

    // Show on internal navigation (click on same-origin links) and on form submit
    document.addEventListener('click', function(e){
      var a = e.target.closest && e.target.closest('a');
      if (!a) return;
      try {
        var href = a.getAttribute('href');
        var target = a.getAttribute('target');
        if (!href || href.indexOf('#') === 0) return; // anchors
        if (target && target !== '_self') return; // external/new tab
        var url = new URL(href, location.href);
        if (url.origin === location.origin) {
          show();
        }
      } catch(err) {
        // ignore
      }
    }, true);

    document.addEventListener('submit', function(e){ show(); }, true);

    // Also show on beforeunload for navigations triggered by browser controls
    window.addEventListener('beforeunload', function(){ show(); });
  });
})();

// Inline edit toggles for review step
(function(){
  function ready(fn){
    if (document.readyState !== 'loading') { fn(); } else { document.addEventListener('DOMContentLoaded', fn); }
  }

  ready(function(){
    function toggleFieldset(fieldset){
      var disabled = fieldset.hasAttribute('disabled');
      var inputs = fieldset.querySelectorAll('input, textarea, select');
      if (disabled) {
        // enable and store original values
        inputs.forEach(function(i){ i.dataset.original = i.value; i.removeAttribute('disabled'); });
        fieldset.removeAttribute('disabled');
        return true;
      } else {
        // revert to original and disable
        inputs.forEach(function(i){ if (i.dataset.original !== undefined) i.value = i.dataset.original; i.setAttribute('disabled','disabled'); });
        fieldset.setAttribute('disabled','disabled');
        return false;
      }
    }

    document.querySelectorAll('.btn-edit-section').forEach(function(btn){
      btn.addEventListener('click', function(e){
        var targetSelector = btn.getAttribute('data-target');
        if (!targetSelector) return;
        var fs = document.querySelector(targetSelector);
        if (!fs) return;
        var nowEditing = toggleFieldset(fs);
        btn.textContent = nowEditing ? 'Cancelar edición' : 'Editar';
      });
    });
  });
})();

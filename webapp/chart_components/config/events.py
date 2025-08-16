"""JavaScript event configuration builders."""
from __future__ import annotations

from typing import Dict


def build_resize_events() -> Dict[str, str]:
    """Build JavaScript events for chart resizing."""
    js = (
        "function(){"
        "var fire=function(){window.dispatchEvent(new Event('resize'));};"
        "setTimeout(fire,60); setTimeout(fire,300); setTimeout(fire,800);"
        "document.addEventListener('visibilitychange', function(){ if(!document.hidden){ setTimeout(fire,60); setTimeout(fire,300); } });"
        "var observer = new MutationObserver(function(mutations) {"
        "  mutations.forEach(function(mutation) {"
        "    if (mutation.type === 'attributes' && mutation.attributeName === 'aria-selected') {"
        "      var target = mutation.target;"
        "      if (target.getAttribute('aria-selected') === 'true') {"
        "        setTimeout(fire, 100); setTimeout(fire, 500);"
        "      }"
        "    }"
        "  });"
        "});"
        "var tabElements = document.querySelectorAll('[role=\"tab\"]');"
        "tabElements.forEach(function(tab) {"
        "  observer.observe(tab, { attributes: true, attributeFilter: ['aria-selected'] });"
        "});"
        "try {"
        "  var sidebar = document.querySelector('section[data-testid=\"stSidebar\"]');"
        "  if (sidebar) {"
        "    var sideObs = new MutationObserver(function(){ setTimeout(fire, 50); setTimeout(fire, 250); setTimeout(fire, 600); });"
        "    sideObs.observe(sidebar, { attributes: true, attributeFilter: ['style','class'] });"
        "  }"
        "} catch(e) { /* noop */ }"
        "}"
    )
    return {'finished': js}

import { useEffect } from 'react';

/**
 * Register global keyboard shortcuts.
 *
 * Each binding is { combo, handler } where combo is a lowercase string like
 * "mod+k" (mod = Cmd on macOS, Ctrl elsewhere) or "escape". By default a
 * binding does NOT fire while typing in an input/textarea, unless it includes
 * a modifier (mod+…) or is escape.
 *
 * @param {Array<{combo: string, handler: (e: KeyboardEvent) => void}>} bindings
 */
export default function useHotkeys(bindings) {
  useEffect(() => {
    function onKeyDown(e) {
      const tag = (e.target?.tagName || '').toLowerCase();
      const typing = tag === 'input' || tag === 'textarea' || e.target?.isContentEditable;
      const mod = e.metaKey || e.ctrlKey;

      for (const { combo, handler } of bindings) {
        const parts = combo.toLowerCase().split('+');
        const key = parts[parts.length - 1];
        const needsMod = parts.includes('mod');

        if (e.key.toLowerCase() !== key) continue;
        if (needsMod !== mod) continue;
        // Plain (modifier-less) shortcuts are suppressed while typing,
        // except Escape which should always work.
        if (typing && !needsMod && key !== 'escape') continue;

        e.preventDefault();
        handler(e);
        break;
      }
    }

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [bindings]);
}

## kebab_graphics Runtime

`kebab_graphics` is the graphics/input runtime facade used by kebab-gui.

It currently defaults to a pygame backend for compatibility, but it is now designed to support backend switching.

### Goals

- Keep app/kernel code independent from direct backend imports.
- Allow multiple rendering/input backends over time.
- Preserve the existing pygame-like API surface for current modules.

### Current Behavior

- Active backend is selected by environment variable: `KEBAB_GRAPHICS_BACKEND`
- Default backend: `pygame`
- Code imports `kebab_graphics as pygame` to remain source-compatible.

### Programmatic API

- `register_backend(name, module_path)`
- `set_backend(name)`
- `get_backend_name()`
- `get_backend_module()`

All unknown attributes are forwarded to the active backend module via `__getattr__`.

### Example

```python
import os
import kebab_graphics as kg

os.environ["KEBAB_GRAPHICS_BACKEND"] = "pygame"
kg.set_backend("pygame")
kg.init()
```

### Next Steps

- Define a backend capability contract (display, events, draw, font, image, transform, input, clipboard).
- Split rendering and input layers so custom backends can map platform APIs cleanly.
- Add a minimal software-only backend for headless testing.

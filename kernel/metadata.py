import json
from html import escape


def _style_to_str(style):
    if isinstance(style, str):
        return style
    if not isinstance(style, dict):
        return ""
    parts = []
    for key, value in style.items():
        if value is None:
            continue
        parts.append(f"{key}: {value}")
    return "; ".join(parts)


def _attrs_to_str(attrs):
    if not isinstance(attrs, dict):
        return ""

    rendered = []
    for key, value in attrs.items():
        if value is None:
            continue
        if key == "style":
            value = _style_to_str(value)
        rendered.append(f'{key}="{escape(str(value), quote=True)}"')
    return (" " + " ".join(rendered)) if rendered else ""


def _node_to_markup(tag, spec):
    if isinstance(spec, list):
        return "".join(_node_to_markup(tag, item) for item in spec)

    if spec is None:
        return f"<{tag} />"

    if not isinstance(spec, dict):
        return f"<{tag}>{escape(str(spec))}</{tag}>"

    attrs = _attrs_to_str(spec.get("attributes", {}))
    children = spec.get("children")
    text = spec.get("text")

    # Support shorthand where additional keys are child tags.
    child_parts = []
    for key, value in spec.items():
        if key in ("attributes", "children", "text"):
            continue
        child_parts.append(_node_to_markup(key, value))

    if isinstance(children, dict):
        if "text" in children and len(children) == 1:
            child_parts.append(escape(str(children["text"])))
        else:
            for child_tag, child_spec in children.items():
                child_parts.append(_node_to_markup(child_tag, child_spec))
    elif isinstance(children, list):
        for child in children:
            if isinstance(child, dict) and "tag" in child:
                child_tag = str(child.get("tag", "div"))
                child_spec = {k: v for k, v in child.items() if k != "tag"}
                child_parts.append(_node_to_markup(child_tag, child_spec))
            else:
                child_parts.append(escape(str(child)))
    elif children is not None:
        child_parts.append(escape(str(children)))

    if text is not None:
        child_parts.insert(0, escape(str(text)))

    if not child_parts:
        return f"<{tag}{attrs} />"
    return f"<{tag}{attrs}>{''.join(child_parts)}</{tag}>"


def _content_to_markup(content_spec):
    if isinstance(content_spec, str):
        return content_spec
    if content_spec is None:
        return None

    child_markup = []
    if isinstance(content_spec, dict):
        for tag, spec in content_spec.items():
            child_markup.append(_node_to_markup(tag, spec))
    elif isinstance(content_spec, list):
        for item in content_spec:
            if isinstance(item, dict) and "tag" in item:
                tag = str(item.get("tag", "div"))
                spec = {k: v for k, v in item.items() if k != "tag"}
                child_markup.append(_node_to_markup(tag, spec))

    if not child_markup:
        return None

    return f"<content>{''.join(child_markup)}</content>"


def parse_kbml_metadata(manifest_str):
    """Extract config, initial data, and optional static markup from app.kbml JSON."""
    try:
        manifest = json.loads(manifest_str)
    except Exception:
        return {}, {}, None

    if not isinstance(manifest, dict):
        return {}, {}, None

    config = {}
    init_data = {}
    static_markup = None

    meta = manifest.get("meta", {})
    if not isinstance(meta, dict):
        meta = {}

    config_obj = meta.get("config", manifest.get("config", {}))
    if isinstance(config_obj, dict):
        config = {
            "width": int(config_obj.get("width", 400)),
            "height": int(config_obj.get("height", 300)),
        }

    data_obj = meta.get("data", manifest.get("data", {}))
    if isinstance(data_obj, dict):
        init_data = dict(data_obj)

    content_value = manifest.get("content")
    static_markup = _content_to_markup(content_value)

    # Backward compatibility for earlier app.kbapp schema.
    if not static_markup:
        markup_value = manifest.get("content_markup")
        if isinstance(markup_value, str) and markup_value.strip():
            static_markup = markup_value

    return config, init_data, static_markup


def parse_kbapp_metadata(manifest_str):
    """Backward-compatible alias for older imports."""
    return parse_kbml_metadata(manifest_str)

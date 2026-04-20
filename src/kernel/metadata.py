import xml.etree.ElementTree as ET


def parse_kebabapp_metadata(markup_str):
    """Extract config and initial data from .kebabapp metadata only."""
    try:
        root = ET.fromstring(markup_str)
    except Exception:
        return {}, {}

    config = {}
    init_data = {}

    meta = root.find("meta")
    if meta is not None:
        config_elem = meta.find("config")
        if config_elem is not None:
            config = {
                "width": int(config_elem.get("width", 400)),
                "height": int(config_elem.get("height", 300)),
            }

        data_elem = meta.find("data")
        if data_elem is not None:
            init_data = dict(data_elem.attrib)

    return config, init_data

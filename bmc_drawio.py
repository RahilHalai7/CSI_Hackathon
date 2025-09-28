#!/usr/bin/env python3
import argparse
import datetime
import json
import os
from pathlib import Path


def _escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_bmc_cells(data: dict, title: str = "Business Model Canvas") -> str:
    """
    Returns XML for BMC cells arranged in a typical layout.

    Layout (page 1200x520):
    - Key Partners: x=0,y=0,w=200,h=320 (spans top+middle)
    - Key Activities: x=200,y=0,w=200,h=160 (top)
    - Key Resources: x=200,y=160,w=200,h=160 (middle)
    - Value Propositions: x=400,y=0,w=300,h=320 (spans top+middle)
    - Customer Relationships: x=700,y=0,w=250,h=160 (top)
    - Channels: x=700,y=160,w=250,h=160 (middle)
    - Customer Segments: x=950,y=0,w=250,h=320 (spans top+middle)
    - Cost Structure: x=0,y=320,w=700,h=200 (bottom left)
    - Revenue Streams: x=700,y=320,w=500,h=200 (bottom right)
    """

    # Helper to make HTML value content
    def html_block(title_key: str) -> str:
        items = data.get(title_key, [])
        if isinstance(items, str):
            items = [items]
        if not isinstance(items, list):
            items = []
        bullets = "<br>".join([_escape_xml(f"• {str(x)}") for x in items])
        content = f"<b>{_escape_xml(title_key)}</b>"
        if bullets:
            content += f"<br>{bullets}"
        return content

    # Common style
    base_style = "rounded=1;whiteSpace=wrap;html=1;strokeColor=#000000;fontSize=12;"

    # Color accents per block
    styles = {
        "Key Partners": base_style + "fillColor=#dae8fc;",
        "Key Activities": base_style + "fillColor=#fff2cc;",
        "Key Resources": base_style + "fillColor=#f8cecc;",
        "Value Propositions": base_style + "fillColor=#d5e8d4;",
        "Customer Relationships": base_style + "fillColor=#e1d5e7;",
        "Channels": base_style + "fillColor=#f5f5f5;",
        "Customer Segments": base_style + "fillColor=#ffe6cc;",
        "Cost Structure": base_style + "fillColor=#e2f2ff;",
        "Revenue Streams": base_style + "fillColor=#ffdada;",
    }

    # Positions
    positions = {
        "Key Partners": (0, 0, 200, 320),
        "Key Activities": (200, 0, 200, 160),
        "Key Resources": (200, 160, 200, 160),
        "Value Propositions": (400, 0, 300, 320),
        "Customer Relationships": (700, 0, 250, 160),
        "Channels": (700, 160, 250, 160),
        "Customer Segments": (950, 0, 250, 320),
        "Cost Structure": (0, 320, 700, 200),
        "Revenue Streams": (700, 320, 500, 200),
    }

    # Build cells
    cell_id = 2  # 0 and 1 are reserved for root and layer
    cells_xml = []

    # Optional title banner
    title_value = _escape_xml(title)
    cells_xml.append(
        f'<mxCell id="{cell_id}" value="{title_value}" style="whiteSpace=wrap;html=1;fontSize=16;fontStyle=1;strokeColor=none;" vertex="1" parent="1">'
        f'<mxGeometry x="480" y="-30" width="240" height="24" as="geometry"/></mxCell>'
    )
    cell_id += 1

    for key in [
        "Key Partners",
        "Key Activities",
        "Key Resources",
        "Value Propositions",
        "Customer Relationships",
        "Channels",
        "Customer Segments",
        "Cost Structure",
        "Revenue Streams",
    ]:
        x, y, w, h = positions[key]
        val = html_block(key)
        style = styles[key]
        cells_xml.append(
            f'<mxCell id="{cell_id}" value="{val}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'
        )
        cell_id += 1

    return "\n".join(cells_xml)


def build_drawio_xml(data: dict, title: str = "Business Model Canvas") -> str:
    cells = build_bmc_cells(data, title)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mxgraph = (
        "<mxGraphModel dx=\"1280\" dy=\"720\" grid=\"1\" gridSize=\"10\" guides=\"1\" tooltips=\"1\" connect=\"1\" arrows=\"1\" fold=\"1\" page=\"1\" pageScale=\"1\" pageWidth=\"1200\" pageHeight=\"520\" math=\"0\" shadow=\"0\">"
        "<root>"
        "<mxCell id=\"0\"/>"
        "<mxCell id=\"1\" parent=\"0\"/>"
        f"{cells}"
        "</root>"
        "</mxGraphModel>"
    )
    xml = (
        f"<mxfile host=\"app.diagrams.net\" modified=\"{now}\" agent=\"Python\" version=\"20.8.3\" etag=\"bmc\">"
        f"<diagram id=\"bmc\" name=\"BMC\"><![CDATA[{mxgraph}]]></diagram>"
        "</mxfile>"
    )
    return xml


def load_data(data_file: str | None) -> dict:
    default = {
        "Key Partners": [],
        "Key Activities": [],
        "Key Resources": [],
        "Value Propositions": [],
        "Customer Relationships": [],
        "Channels": [],
        "Customer Segments": [],
        "Cost Structure": [],
        "Revenue Streams": [],
    }
    if not data_file:
        return default
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        for k in default.keys():
            v = loaded.get(k, [])
            if isinstance(v, str):
                default[k] = [v]
            elif isinstance(v, list):
                default[k] = v
    except Exception:
        pass
    return default


def main():
    parser = argparse.ArgumentParser(description="Generate a Business Model Canvas as a .drawio diagram")
    parser.add_argument("--output", help="Output .drawio file path", default=str(Path("diagrams") / "bmc.drawio"))
    parser.add_argument("--title", help="Title for the canvas", default="Business Model Canvas")
    parser.add_argument("--data-file", help="JSON file containing BMC blocks content", default=None)
    args = parser.parse_args()

    # Ensure folder exists
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Build XML
    data = load_data(args.data_file)
    xml = build_drawio_xml(data, args.title)

    # Write file
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"✅ BMC diagram generated: {out_path}")
    print("Open https://app.diagrams.net/ then File > Open From Device and select this file.")
    print("Tip: You can edit block contents later directly in diagrams.net.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
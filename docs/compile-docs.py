"""
Convert all .md files in pages-raw/ to .html files in pages/
"""

from pathlib import Path
import markdown



def convert_markdown_to_html(md_text: str, title: str) -> str:
    md = markdown.Markdown(
        extensions=[
            "fenced_code",    
            "codehilite",     
            "tables"
        ],
        extension_configs={
            "codehilite": {
                "linenums": False,
                "guess_lang": True,
                "noclasses": False,  # use CSS classes; works with Pygments CSS
            }
        }
    )

    body_html = md.convert(md_text)

    html_doc = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <link rel="stylesheet" href="../lib/pages.css">
    <link rel="stylesheet" href="../lib/code.css">
</head>
<body>
{body_html}
</body>
</html>
    """
    return html_doc


def process_folder(src_dir, dst_dir):
    for md_path in src_dir.glob("*.md"):
        rel_path = md_path.relative_to(src_dir)
        dst_path = (dst_dir / rel_path).with_suffix(".html")
        md_text = md_path.read_text()
        html_doc = convert_markdown_to_html(md_text, md_path.stem)
        dst_path.write_text(html_doc)
        print(f"Converted: {md_path} -> {dst_path}")

if __name__ == "__main__":
    base_dir = Path(__file__).parent
    process_folder(base_dir / "pages-raw", base_dir / "pages")

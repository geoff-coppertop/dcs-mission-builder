"""Briefings from Markdown: one source for the PDF and the in-game (Mission Editor) briefing text.

A briefing is a Markdown file with Jinja2 placeholders ({{ tot }}, {% if hard %}...{% endif %}) filled from a
context dict computed from the built mission. Three HTML comments mark what goes into the .miz:

    <!-- ingame -->      ...   <!-- /ingame -->     the mission description (Situation, mission, the story)
    <!-- task -->        ...   <!-- /task -->       the "Blue task" text (times, frequencies, menus)
    <!-- pdf-only -->    ...   <!-- /pdf-only -->   left out of the in-game text even inside the blocks above

Everything is in the PDF. Images use paths relative to the work directory, where the maps are drawn.
"""
import html
import re
import zipfile
from pathlib import Path

import jinja2
import markdown as md_lib

STYLE = Path(__file__).with_name("briefing.css")


# ------------------------------------------------------------------ templates
def render(template_path, ctx):
    """Fill a Markdown template's placeholders. Undefined names are errors, so a typo cannot ship."""
    template_path = Path(template_path)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(template_path.parent)),
                             undefined=jinja2.StrictUndefined, trim_blocks=True, lstrip_blocks=True,
                             keep_trailing_newline=True)
    return env.get_template(template_path.name).render(**ctx)


def _blocks(md, tag):
    return re.findall(rf"<!--\s*{tag}\s*-->(.*?)<!--\s*/{tag}\s*-->", md, flags=re.S)


# ------------------------------------------------------------------ plain text for DCS
def _inline(t):
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)                 # images
    t = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", t)             # links -> text
    t = re.sub(r"\*\*(.+?)\*\*|__(.+?)__", lambda m: m.group(1) or m.group(2), t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = re.sub(r"<br\s*/?>", " ", t)
    t = re.sub(r"<[^>]+>", "", t)
    return html.unescape(t).replace("&nbsp;", " ").strip()


def to_text(md):
    """Markdown to the plain text DCS shows in its briefing window: headings in capitals, paragraphs
    reflowed, lists kept, tables as one line per row ("A: B, C")."""
    md = re.sub(r"<!--\s*pdf-only\s*-->.*?<!--\s*/pdf-only\s*-->", "", md, flags=re.S)
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    out, para, rows = [], [], []

    def flush():
        if para:
            out.append(_inline(" ".join(para)))
            out.append("")
            para.clear()
        if rows:
            head = rows[0]
            for r in rows[2:]:                                  # skip header and |---| rule
                cells = [_inline(c) for c in r]
                if len(cells) >= 2 and head and _inline(head[0]).lower() in ("", "item", "callsign", "event", "time"):
                    out.append(f"{cells[0]}: " + ", ".join(c for c in cells[1:] if c))
                else:
                    out.append(" - ".join(c for c in cells if c))
            out.append("")
            rows.clear()

    for line in md.splitlines():
        s = line.strip()
        if not s:
            flush()
            continue
        if s.startswith("|"):
            if para:
                flush()
            rows.append([c.strip() for c in s.strip("|").split("|")])
            continue
        if rows:
            flush()
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush()
            out.append(_inline(m.group(2)).upper())
            continue
        m = re.match(r"^([-*]|\d+\.)\s+(.*)$", s)
        if m:
            flush()
            bullet = "-" if m.group(1) in "-*" else m.group(1)
            out.append(f"{bullet} {_inline(m.group(2))}")
            continue
        if s.startswith(">"):
            s = s.lstrip("> ")
        if not para and out and re.match(r"^(-|\d+\.) ", out[-1]):
            out.append("")                                      # a paragraph after a list gets its own line
        para.append(s)
    flush()
    text = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def ingame(md):
    """(description, task) for the .miz from the marked blocks."""
    desc = "\n\n".join(_blocks(md, "ingame"))
    task = "\n\n".join(_blocks(md, "task"))
    return to_text(desc), to_text(task)


# ------------------------------------------------------------------ write into the .miz
def _lua_str(s):
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
    return f'"{s}"'


def inject(miz_path, description, task):
    """Replace the mission description and Blue task texts in an existing .miz (in place)."""
    import lupa
    miz_path = Path(miz_path)
    with zipfile.ZipFile(miz_path) as z:
        items = {n: z.read(n) for n in z.namelist()}
    L = lupa.LuaRuntime(unpack_returned_tuples=True)
    L.execute(items["mission"].decode("utf-8"))
    L.execute(items["l10n/DEFAULT/dictionary"].decode("utf-8"))
    mis, dic = L.globals().mission, L.globals().dictionary
    entries = {k: dic[k] for k in dic.keys()}
    entries[mis.descriptionText] = description
    entries[mis.descriptionBlueTask] = task
    body = "dictionary = \n{\n" + "".join(f"    [{_lua_str(k)}] = {_lua_str(v)},\n" for k, v in sorted(entries.items())) + "} -- end of dictionary\n"
    items["l10n/DEFAULT/dictionary"] = body.encode("utf-8")
    tmp = miz_path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in items.items():
            z.writestr(n, data)
    tmp.replace(miz_path)


# ------------------------------------------------------------------ PDF
def to_html(md, title):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    body = md_lib.markdown(md, extensions=["tables", "attr_list", "md_in_html", "sane_lists", "smarty"],
                           output_format="html5")
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
            f"<style>{STYLE.read_text(encoding='utf-8')}</style></head><body>{body}</body></html>")


def to_pdf(md, out_pdf, base_dir, title, footer):
    """Render Markdown to a Letter PDF with Chromium (Playwright). Image paths resolve against base_dir."""
    from playwright.sync_api import sync_playwright
    base_dir = Path(base_dir).resolve()
    page_html = base_dir / (Path(out_pdf).stem + ".html")
    page_html.write_text(to_html(md, title), encoding="utf-8")
    foot = ("<div style='font-family:Inter,Helvetica,Arial,sans-serif;font-size:7px;letter-spacing:.06em;color:#8a8984;"
            "width:100%;margin:0 0.6in;display:flex;justify-content:space-between;border-top:0.6px solid #d9d7d0;"
            f"padding-top:4px'><span>{html.escape(footer.upper())}</span><span class='pageNumber'></span></div>")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(page_html.as_uri())
        pg.wait_for_load_state("networkidle")
        pg.pdf(path=str(out_pdf), format="Letter", print_background=True, display_header_footer=True,
               header_template="<div></div>", footer_template=foot,
               margin={"top": "0.55in", "bottom": "0.7in", "left": "0.6in", "right": "0.6in"})
        b.close()
    return out_pdf

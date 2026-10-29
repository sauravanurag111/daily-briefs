#!/usr/bin/env python3
"""Publish Tokenwise issues to Telegraph and keep a date-sorted index page.

Usage: python3 tw_publish.py ISSUES_DIR STATE_JSON
  ISSUES_DIR  folder of <YYYY-MM-DD>.json issue files (the ArtifactData export)
  STATE_JSON  {"access_token","index_path","index_url","pages":{date:{path,url}}}
              (created if missing; rewritten in place)
Publishes every issue that has no page yet (oldest first), then rebuilds the index.
Prints a JSON summary. Exit code 2 if Telegraph could not be reached.
"""
import json, os, re, sys, glob, urllib.request, urllib.parse, urllib.error

API = "https://api.telegra.ph/"
MON = ["January","February","March","April","May","June","July","August","September","October","November","December"]
DOW = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]


def call(method, **params):
    data = urllib.parse.urlencode({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
                                   for k, v in params.items()}).encode()
    req = urllib.request.Request(API + method, data=data, headers={"User-Agent": "tokenwise/1"})
    with urllib.request.urlopen(req, timeout=40) as r:
        res = json.load(r)
    if not res.get("ok"):
        raise RuntimeError(f"{method}: {res.get('error')}")
    return res["result"]


def inline(text):
    """**bold** and *italic* -> Telegraph nodes."""
    out = []
    for part in re.split(r"(\*\*.+?\*\*|(?<!\*)\*(?!\s)[^*]+?\*(?!\*))", str(text or "")):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            out.append({"tag": "strong", "children": [part[2:-2]]})
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append({"tag": "em", "children": [part[1:-1]]})
        else:
            out.append(part)
    return out


def p(text, tag="p"):
    return {"tag": tag, "children": inline(text)}


def link(name, url):
    return {"tag": "a", "attrs": {"href": url}, "children": [name or url]}


def long_date(d):
    import datetime
    dt = datetime.date.fromisoformat(d)
    return f"{DOW[dt.weekday()]}, {dt.day} {MON[dt.month-1]} {dt.year}"


def issue_nodes(it, d, index_url):
    n = []
    n.append(p(f"Issue {it.get('issue','')} · {long_date(d)}", "aside"))
    n.append({"tag": "h3", "children": ["The 60-second brief"]})
    n.append({"tag": "ol", "children": [{"tag": "li", "children": inline(t)} for t in it.get("tldr", [])]})

    n.append({"tag": "hr"})
    n.append({"tag": "h3", "children": ["What happened"]})
    for s in it.get("news", []):
        head = (f"[{s['tag']}] " if s.get("tag") else "") + s.get("headline", "")
        n.append({"tag": "h4", "children": inline(head)})
        n.append(p(s.get("what", "")))
        if s.get("why"):
            n.append({"tag": "blockquote", "children": [{"tag": "strong", "children": ["Why it matters: "]}] + inline(s["why"])})
        src = s.get("source") or {}
        if src.get("url"):
            n.append({"tag": "p", "children": [{"tag": "em", "children": ["Source: "]}, link(src.get("name"), src["url"])]})

    m = it.get("models") or {}
    if m.get("rows"):
        n.append({"tag": "hr"})
        n.append({"tag": "h3", "children": ["Who's winning, by use case"]})
        if m.get("intro"):
            n.append(p(m["intro"]))
        items = []
        for r in m["rows"]:
            kids = [{"tag": "strong", "children": [r.get("useCase", "") + ": "]}] + inline(r.get("pick", ""))
            if r.get("runnerUp"):
                kids += [" (also: "] + inline(r["runnerUp"]) + [")"]
            if r.get("why"):
                kids += [{"tag": "br"}] + inline(r["why"])
            items.append({"tag": "li", "children": kids})
        n.append({"tag": "ul", "children": items})
        if m.get("note"):
            n.append({"tag": "p", "children": [{"tag": "em", "children": inline(m["note"])}]})

    c = it.get("concept") or {}
    if c.get("title"):
        n.append({"tag": "hr"})
        label = f"Learn one thing · {c.get('track','Concept')}" + (f" · Lesson {c['lesson']}" if c.get("lesson") else "")
        n.append(p(label, "aside"))
        n.append({"tag": "h3", "children": inline(c["title"])})
        if c.get("oneLiner"):
            n.append({"tag": "p", "children": [{"tag": "em", "children": inline(c["oneLiner"])}]})
        for para in c.get("body", []):
            n.append(p(para))
        if c.get("analogy"):
            n.append({"tag": "blockquote", "children": [{"tag": "strong", "children": ["Think of it like this: "]}] + inline(c["analogy"])})
        if c.get("pmTakeaways"):
            n.append({"tag": "h4", "children": ["For you as a PM"]})
            n.append({"tag": "ul", "children": [{"tag": "li", "children": inline(t)} for t in c["pmTakeaways"]]})
        if c.get("terms"):
            n.append({"tag": "h4", "children": ["Key terms"]})
            n.append({"tag": "ul", "children": [{"tag": "li", "children": [{"tag": "strong", "children": [t.get("term", "") + ": "]}] + inline(t.get("def", ""))} for t in c["terms"]]})

    q = it.get("quiz")
    if q and q.get("options"):
        n.append({"tag": "hr"})
        n.append({"tag": "h3", "children": ["Check yourself"]})
        n.append(p(q.get("question", "")))
        letters = "ABCDEFGH"
        n.append({"tag": "ul", "children": [{"tag": "li", "children": [f"{letters[i]}. "] + inline(o)} for i, o in enumerate(q["options"])]})
        ans = q.get("answer", 0)
        n.append({"tag": "blockquote", "children": [{"tag": "strong", "children": [f"Answer (scroll past if you're still thinking): {letters[ans]}. "]}] + inline(q.get("explain", ""))})

    if it.get("sources"):
        n.append({"tag": "hr"})
        n.append({"tag": "h4", "children": ["Sources"]})
        n.append({"tag": "ol", "children": [{"tag": "li", "children": [link(s.get("name"), s.get("url"))]} for s in it["sources"] if s.get("url")]})

    if index_url:
        n.append({"tag": "hr"})
        n.append({"tag": "p", "children": [link("← All Tokenwise issues, by date", index_url)]})
    return n


def index_nodes(issues, pages):
    n = [p("Your daily AI brief: news, which models are winning, one concept a day. Newest first. Every issue stays here.")]
    last = None
    for d in sorted(pages, reverse=True):
        y, mth = d[:4], int(d[5:7])
        key = (y, mth)
        if key != last:
            n.append({"tag": "h3", "children": [f"{MON[mth-1]} {y}"]})
            n.append({"tag": "ul", "children": []})
            last = key
        it = issues.get(d, {})
        lesson = (it.get("concept") or {}).get("title", "")
        kids = [{"tag": "strong", "children": [f"{long_date(d)[:-5]}: "]}, link(it.get("title") or f"Issue {it.get('issue','')}", pages[d]["url"])]
        if lesson:
            kids += [{"tag": "br"}, {"tag": "em", "children": ["Learn: " + re.sub(r"\*", "", lesson)]}]
        n[-1]["children"].append({"tag": "li", "children": kids})
    return n


def main():
    issues_dir, state_path = sys.argv[1], sys.argv[2]
    state = json.load(open(state_path)) if os.path.exists(state_path) else {}
    state.setdefault("pages", {})
    issues = {}
    for f in glob.glob(os.path.join(issues_dir, "*.json")):
        d = os.path.basename(f)[:-5]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
            issues[d] = json.load(open(f))
    published = []
    try:
        if not state.get("access_token"):
            acc = call("createAccount", short_name="Tokenwise", author_name="Tokenwise")
            state["access_token"] = acc["access_token"]
        tok = state["access_token"]
        if not state.get("index_path"):
            idx = call("createPage", access_token=tok, title="Tokenwise: all issues", author_name="Tokenwise",
                       content=[p("Setting up…")])
            state["index_path"], state["index_url"] = idx["path"], idx["url"]
        for d in sorted(issues):
            if d in state["pages"]:
                continue
            it = issues[d]
            title = f"Tokenwise #{it.get('issue','')}: {re.sub(r'[*`]', '', it.get('title','Today in AI'))}"[:256]
            pg = call("createPage", access_token=tok, title=title, author_name="Tokenwise",
                      author_url=state["index_url"], content=issue_nodes(it, d, state["index_url"]))
            state["pages"][d] = {"path": pg["path"], "url": pg["url"]}
            published.append({"date": d, "url": pg["url"]})
            json.dump(state, open(state_path, "w"), indent=1)
        call("editPage/" + state["index_path"], access_token=tok, title="Tokenwise: all issues",
             author_name="Tokenwise", content=index_nodes(issues, state["pages"]))
    except (urllib.error.URLError, OSError, RuntimeError) as e:
        json.dump(state, open(state_path, "w"), indent=1)
        print(json.dumps({"ok": False, "error": str(e), "published": published, "index_url": state.get("index_url")}))
        sys.exit(2)
    json.dump(state, open(state_path, "w"), indent=1)
    print(json.dumps({"ok": True, "published": published, "index_url": state["index_url"]}))


if __name__ == "__main__":
    main()

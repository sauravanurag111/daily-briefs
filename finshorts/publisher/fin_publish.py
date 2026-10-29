#!/usr/bin/env python3
"""Publish FinShorts issues to Telegraph and keep a date-sorted index page.

Usage: python3 fin_publish.py ISSUES_DIR STATE_JSON
  ISSUES_DIR  folder of <YYYY-MM-DD>.json issue files (the ArtifactData export)
  STATE_JSON  {"access_token","index_path","index_url","pages":{date:{path,url}}}
              (created if missing; rewritten in place)
Publishes every issue that has no page yet (oldest first), then rebuilds the index.
Prints a JSON summary. Exit code 2 if Telegraph could not be reached.
"""
import datetime, glob, json, os, re, sys, urllib.error, urllib.parse, urllib.request

API = "https://api.telegra.ph/"
MON = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def call(method, **params):
    data = urllib.parse.urlencode({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
                                   for k, v in params.items()}).encode()
    req = urllib.request.Request(API + method, data=data, headers={"User-Agent": "finshorts/1"})
    with urllib.request.urlopen(req, timeout=40) as r:
        res = json.load(r)
    if not res.get("ok"):
        raise RuntimeError(f"{method}: {res.get('error')}")
    return res["result"]


def inline(text):
    """**bold** -> Telegraph nodes."""
    out = []
    for part in re.split(r"(\*\*.+?\*\*)", str(text or "")):
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            out.append({"tag": "strong", "children": [part[2:-2]]})
        elif part:
            out.append(part)
    return out


def el(tag, *children, **attrs):
    node = {"tag": tag, "children": [c for c in children if c not in (None, "")]}
    if attrs:
        node["attrs"] = attrs
    return node


def p(text, tag="p"):
    return el(tag, *inline(text))


def link(name, url):
    return el("a", name or url, href=url)


def labelled(label, text):
    return el("p", el("strong", label + " "), *inline(text))


def long_date(d):
    dt = datetime.date.fromisoformat(d)
    return f"{DOW[dt.weekday()]}, {dt.day} {MON[dt.month - 1]} {dt.year}"


def source_line(s):
    s = s or {}
    return el("p", el("em", "Source: "), link(s.get("name"), s["url"])) if s.get("url") else None


def issue_nodes(it, d, index_url):
    n = [p(f"Issue {it.get('issue', '')} · {long_date(d)}", "aside"),
         el("h3", "In 60 seconds"),
         el("ol", *[el("li", *inline(t)) for t in it.get("tldr", [])])]

    if it.get("news"):
        n += [el("hr"), el("h3", "What happened")]
        for s in it["news"]:
            n.append(el("h4", *inline((f"[{s['tag']}] " if s.get("tag") else "") + s.get("headline", ""))))
            n.append(p(s.get("what", "")))
            if s.get("why"):
                n.append(el("blockquote", el("strong", "Why it matters: "), *inline(s["why"])))
            n.append(source_line(s.get("source")))

    if it.get("rules"):
        n += [el("hr"), el("h3", "Rules & regulators")]
        for r in it["rules"]:
            n.append(el("h4", *inline((f"[{r['regulator']}] " if r.get("regulator") else "") + r.get("headline", ""))))
            n.append(p(r.get("what", "")))
            if r.get("whoIsAffected"):
                n.append(labelled("Who is affected:", r["whoIsAffected"]))
            if r.get("when"):
                n.append(labelled("When:", r["when"]))
            n.append(source_line(r.get("source")))

    if it.get("deals"):
        n += [el("hr"), el("h3", "Money raised")]
        items = []
        for dl in it["deals"]:
            kids = [el("strong", f"{dl.get('company', '')}: {dl.get('amount', '')}")]
            if dl.get("round"):
                kids.append(f" ({dl['round']})")
            if dl.get("what"):
                kids += [el("br"), *inline(dl["what"])]
            if dl.get("investors"):
                kids += [el("br"), el("em", "Investors: " + dl["investors"])]
            items.append(el("li", *kids))
        n.append(el("ul", *items))

    if it.get("numbers"):
        n += [el("hr"), el("h3", "Numbers to know"),
              el("ul", *[el("li", el("strong", f"{x.get('label', '')}: {x.get('value', '')}"),
                             *([" · "] + inline(x["note"]) if x.get("note") else [])) for x in it["numbers"]])]

    c = it.get("concept") or {}
    if c.get("title"):
        n.append(el("hr"))
        n.append(p(f"Concept of the day · {c.get('track', 'Finance')}" + (f" · Lesson {c['lesson']}" if c.get("lesson") else ""), "aside"))
        n.append(el("h3", *inline(c["title"])))
        if c.get("oneLiner"):
            n.append(el("p", el("em", *inline(c["oneLiner"]))))
        n += [p(para) for para in c.get("body", [])]
        if c.get("example"):
            n.append(el("blockquote", el("strong", "Example in rupees: "), *inline(c["example"])))
        if c.get("whyItMatters"):
            n += [el("h4", "Why it matters to you"), p(c["whyItMatters"])]
        if c.get("terms"):
            n += [el("h4", "Key terms"),
                  el("ul", *[el("li", el("strong", t.get("term", "") + ": "), *inline(t.get("def", ""))) for t in c["terms"]])]

    q = it.get("quiz")
    if q and q.get("options"):
        letters = "ABCDEFGH"
        ans = q.get("answer", 0)
        n += [el("hr"), el("h3", "Check yourself"), p(q.get("question", "")),
              el("ul", *[el("li", f"{letters[i]}. ", *inline(o)) for i, o in enumerate(q["options"])]),
              el("blockquote", el("strong", f"Answer (scroll past if you're still thinking): {letters[ans]}. "), *inline(q.get("explain", "")))]

    if it.get("sources"):
        n += [el("hr"), el("h4", "Sources"),
              el("ol", *[el("li", link(s.get("name"), s["url"])) for s in it["sources"] if s.get("url")])]

    if index_url:
        n += [el("hr"), el("p", link("← All FinShorts issues, by date", index_url))]
    return [x for x in n if x]


def index_nodes(issues, pages):
    n = [p("Your daily fintech and finance brief: news, funding, regulator moves and one concept a day. Newest first. Every issue stays here.")]
    last = None
    for d in sorted(pages, reverse=True):
        key = d[:7]
        if key != last:
            n += [el("h3", f"{MON[int(d[5:7]) - 1]} {d[:4]}"), el("ul")]
            last = key
        it = issues.get(d, {})
        kids = [el("strong", f"{long_date(d)[:-5]}: "), link(re.sub(r"\*", "", it.get("title") or f"Issue {it.get('issue', '')}"), pages[d]["url"])]
        lesson = (it.get("concept") or {}).get("title")
        if lesson:
            kids += [el("br"), el("em", "Concept: " + re.sub(r"\*", "", lesson))]
        n[-1]["children"].append(el("li", *kids))
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
            state["access_token"] = call("createAccount", short_name="FinShorts", author_name="FinShorts")["access_token"]
        tok = state["access_token"]
        if not state.get("index_path"):
            idx = call("createPage", access_token=tok, title="FinShorts: all issues", author_name="FinShorts", content=[p("Setting up…")])
            state["index_path"], state["index_url"] = idx["path"], idx["url"]
        for d in sorted(issues):
            if d in state["pages"]:
                continue
            it = issues[d]
            title = f"FinShorts #{it.get('issue', '')}: {re.sub(r'[*`]', '', it.get('title', 'Today in fintech'))}"[:256]
            pg = call("createPage", access_token=tok, title=title, author_name="FinShorts",
                      author_url=state["index_url"], content=issue_nodes(it, d, state["index_url"]))
            state["pages"][d] = {"path": pg["path"], "url": pg["url"]}
            published.append({"date": d, "url": pg["url"]})
            json.dump(state, open(state_path, "w"), indent=1)
        call("editPage/" + state["index_path"], access_token=tok, title="FinShorts: all issues",
             author_name="FinShorts", content=index_nodes(issues, state["pages"]))
    except (urllib.error.URLError, OSError, RuntimeError) as e:
        json.dump(state, open(state_path, "w"), indent=1)
        print(json.dumps({"ok": False, "error": str(e), "published": published, "index_url": state.get("index_url")}))
        sys.exit(2)
    json.dump(state, open(state_path, "w"), indent=1)
    print(json.dumps({"ok": True, "published": published, "index_url": state["index_url"]}))


if __name__ == "__main__":
    main()

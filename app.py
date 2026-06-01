"""
PFM Business Explorer
Interactive app to understand PFM's machines, segments, and pack styles.
"""

import json
import streamlit as st

# ── Page config ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PFM Business Explorer",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Load data ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    with open("data/pfm_data.json", encoding="utf-8") as f:
        raw = json.load(f)
    with open("data/enrichment.json", encoding="utf-8") as f:
        enrichment = json.load(f)

    apps = raw["applications"]
    machines_detail = raw["machines"]

    # Clean segment names
    name_fixes = {"BreadCutting &": "Cut Bread", "Bread": "Cut Bread", "Meat": "Meat & Sausages"}
    for app in apps:
        app["name"] = name_fixes.get(app["name"], app["name"])

    # Inject enrichment into segments
    for app in apps:
        seg_data = enrichment["segments"].get(app["name"], {})
        app.update(seg_data)

    # Fix machine families using slug patterns
    family_rules = {
        "azimuth": "VFFS", "comet": "VFFS", "solaris": "VFFS", "zenith": "VFFS",
        "r-700": "VFFS", "rc-700": "VFFS", "rq-700": "VFFS", "rx800": "VFFS",
        "polar": "VFFS", "vetta": "VFFS", "pv320": "VFFS", "compact": "VFFS",
        "mbp": "Multihead Weigher",
        "bora": "Flow Wrap", "falcon": "Flow Wrap", "ghibli": "Flow Wrap",
        "levante": "Flow Wrap", "mistral": "Flow Wrap", "pearl": "Flow Wrap",
        "pulsar": "Flow Wrap", "scirocco": "Flow Wrap", "shamal": "Flow Wrap",
        "tornado": "Flow Wrap", "zephyr": "Flow Wrap", "bg-2800": "Flow Wrap",
        "blizzard": "Flow Wrap",
        "d-series": "Stand-up Pouch", "f-series": "Stand-up Pouch",
    }
    for slug, detail in machines_detail.items():
        for key, family in family_rules.items():
            if key in slug.lower():
                detail["family"] = family
                break
        # Inject machine enrichment
        m_data = enrichment["machines"].get(slug, {})
        detail.update(m_data)

    # Build reverse index: machine slug → segments
    machine_to_segments = {}
    for app in apps:
        for m in app["machines"]:
            slug = m["slug"]
            machine_to_segments.setdefault(slug, [])
            if app["name"] not in machine_to_segments[slug]:
                machine_to_segments[slug].append(app["name"])

    return apps, machines_detail, machine_to_segments, enrichment


apps, machines_detail, machine_to_segments, enrichment = load_data()

# ── Constants ────────────────────────────────────────────────────────────────────
DATA_NOTE = (
    "📊 **Data disclaimer:** Market size and growth figures are estimates based on "
    "public industry knowledge (Statista, Euromonitor). Est. target counts are approximations. "
    "PFM Priority is inferred from internal documents. "
    "**Do not use in client meetings without verifying against official sources** "
    "(Euromonitor, Statista, Matchplat, ZoomInfo)."
)

FAMILY_COLORS = {
    "VFFS":              "#1f77b4",
    "Flow Wrap":         "#ff7f0e",
    "Multihead Weigher": "#2ca02c",
    "Stand-up Pouch":    "#9467bd",
    "Other":             "#7f7f7f",
    "Unknown":           "#7f7f7f",
}
PRIORITY_COLORS = {"High": "#d62728", "Medium": "#ff7f0e", "Low": "#2ca02c"}


# ── Helper renderers ─────────────────────────────────────────────────────────────
def badge(text, color):
    return f'<span style="background:{color};color:white;padding:2px 10px;border-radius:12px;font-size:0.8em;font-weight:600;">{text}</span>'

def chip(text, bg="#e8f4fd", fg="#1a6fa8"):
    return f'<span style="background:{bg};color:{fg};padding:2px 10px;border-radius:12px;font-size:0.85em;margin:2px;display:inline-block;">{text}</span>'

def render_chips(items, bg="#e8f4fd", fg="#1a6fa8"):
    st.markdown(" ".join(chip(i, bg, fg) for i in items), unsafe_allow_html=True)

def priority_badge(priority):
    color = PRIORITY_COLORS.get(priority, "#7f7f7f")
    return badge(f"PFM Priority: {priority}", color)

def family_badge(family):
    return badge(family, FAMILY_COLORS.get(family, "#7f7f7f"))


# ── Sidebar ──────────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 📦 PFM Business Explorer")
st.sidebar.markdown("---")
view = st.sidebar.radio(
    "Explore by",
    ["🏠 Home", "🏭 Segment", "⚙️ Machine", "📦 Pack Style"],
    label_visibility="collapsed"
)


# ════════════════════════════════════════════════════════════════════════════════
# HOME
# ════════════════════════════════════════════════════════════════════════════════
if view == "🏠 Home":
    st.title("📦 PFM Business Explorer")
    st.markdown(
        "**PFM Group** is an Italian packaging machinery manufacturer. "
        "This app maps their machines to industries and pack formats — "
        "use it to understand the business quickly."
    )
    st.markdown("---")

    # Top metrics
    total_market = sum(a.get("market_size_bn_eur", 0) for a in apps)
    all_ps = set(ps["name"] for a in apps for ps in a["pack_styles"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Industry Segments", len(apps))
    c2.metric("Machine Models", len(machines_detail))
    c3.metric("Pack Styles", len(all_ps))
    c4.metric("Total Addressable Market", f"€{total_market:,.0f}B")

    st.markdown("---")

    # Machine families
    st.subheader("Machine Families")
    families = {}
    for slug, m in machines_detail.items():
        fam = m.get("family", "Unknown")
        families.setdefault(fam, []).append(slug)

    cols = st.columns(len(families))
    for col, (fam, slugs) in zip(cols, sorted(families.items())):
        color = FAMILY_COLORS.get(fam, "#7f7f7f")
        col.markdown(
            f'<div style="border-left:4px solid {color};padding-left:10px;">'
            f'<b>{fam}</b><br>'
            f'<span style="font-size:2em;font-weight:bold;">{len(slugs)}</span>'
            f'<span style="color:gray;font-size:0.85em;"> models</span></div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    st.caption("📊 Market size & growth: estimated from public sources (Statista, Euromonitor). Est. Targets & Priority: approximations for learning — verify before use.")

    # Segment table ranked by market size
    st.subheader("Segments — Ranked by Market Size")
    sorted_apps = sorted(apps, key=lambda a: a.get("market_size_bn_eur", 0), reverse=True)

    col_headers = st.columns([3, 2, 2, 2, 2])
    col_headers[0].markdown("**Segment**")
    col_headers[1].markdown("**Market Size**")
    col_headers[2].markdown("**Growth/yr**")
    col_headers[3].markdown("**Est. Targets**")
    col_headers[4].markdown("**PFM Priority**")
    st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

    for app in sorted_apps:
        cols = st.columns([3, 2, 2, 2, 2])
        cols[0].markdown(f"**{app['name']}**")
        size = app.get("market_size_bn_eur")
        cols[1].markdown(f"€{size}B" if size else "—")
        growth = app.get("growth_pct")
        cols[2].markdown(f"📈 {growth}%" if growth else "—")
        targets = app.get("target_count_estimate")
        cols[3].markdown(f"~{targets:,}" if targets else "—")
        priority = app.get("pfm_priority", "—")
        color = PRIORITY_COLORS.get(priority, "#7f7f7f")
        cols[4].markdown(badge(priority, color), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# SEGMENT
# ════════════════════════════════════════════════════════════════════════════════
elif view == "🏭 Segment":
    segment_names = sorted(a["name"] for a in apps)
    selected = st.sidebar.selectbox("Choose a segment", segment_names)
    app = next(a for a in apps if a["name"] == selected)

    # Header
    priority = app.get("pfm_priority", "—")
    st.title(f"🏭 {app['name']}")
    st.markdown(priority_badge(priority), unsafe_allow_html=True)
    st.markdown("")

    # Key numbers row
    size = app.get("market_size_bn_eur")
    growth = app.get("growth_pct")
    targets = app.get("target_count_estimate")
    invest = app.get("avg_investment_keur")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Market Size", f"€{size}B" if size else "—", help="Estimated — source: Statista / Euromonitor. Not verified.")
    c2.metric("Yearly Growth", f"{growth}%" if growth else "—", help="Estimated — source: public industry reports. Not verified.")
    c3.metric("Est. Target Companies", f"~{targets:,}" if targets else "—", help="Approximation only. Verify with Matchplat, Apollo.io or ZoomInfo.")
    c4.metric("Avg. Machine Investment", f"~€{invest}K" if invest else "—", help="Rough estimate for learning purposes only.")

    # Why PFM
    why = app.get("why_pfm")
    if why:
        st.info(f"**Why PFM wins here:** {why}")

    st.markdown(f"[View on pfm.it]({app['url']})")

    if app.get("intro"):
        with st.expander("Show page description"):
            st.markdown(app["intro"])

    st.markdown("---")

    col_l, col_r = st.columns([3, 2])

    with col_l:
        # Example clients
        clients = app.get("example_clients", [])
        if clients:
            st.subheader(f"🏢 Example Clients ({len(clients)})")
            render_chips(clients, bg="#fff3e0", fg="#b45309")
            st.markdown("")

        # Machines grouped by family
        st.subheader(f"⚙️ Recommended Machines ({len(app['machines'])})")
        by_family = {}
        for m in app["machines"]:
            slug = m["slug"]
            detail = machines_detail.get(slug, {})
            fam = detail.get("family", "Other")
            by_family.setdefault(fam, []).append((m, detail))

        for fam, items in sorted(by_family.items()):
            color = FAMILY_COLORS.get(fam, "#7f7f7f")
            st.markdown(
                f'<div style="border-left:3px solid {color};padding-left:8px;margin:10px 0 4px 0;">'
                f'<b>{fam}</b> — {len(items)} model(s)</div>',
                unsafe_allow_html=True
            )
            for m, detail in items:
                speed = detail.get("speed_bags_min")
                heads = detail.get("weighing_heads")
                feat = detail.get("key_feature", "")
                label = m["name"]
                if speed:
                    label += f" · **{speed} bags/min**"
                elif heads:
                    label += f" · **{heads} weighing heads**"
                with st.expander(label):
                    if feat:
                        st.markdown(f"✅ {feat}")
                    desc = detail.get("description", "")
                    if desc:
                        st.markdown(desc[:400])
                    fmt = detail.get("format_range_mm")
                    if fmt:
                        st.markdown(f"**Format range:** {fmt} mm")
                    segs = machine_to_segments.get(m["slug"], [])
                    other_segs = [s for s in segs if s != app["name"]]
                    if other_segs:
                        st.markdown("**Also used in:**")
                        render_chips(other_segs)
                    if m.get("url"):
                        st.markdown(f"[Machine page →]({m['url']})")

    with col_r:
        st.subheader(f"📦 Pack Styles ({len(app['pack_styles'])})")
        for ps in app["pack_styles"]:
            st.markdown(f"- [{ps['name']}]({ps['url']})")


# ════════════════════════════════════════════════════════════════════════════════
# MACHINE
# ════════════════════════════════════════════════════════════════════════════════
elif view == "⚙️ Machine":
    machine_options = {}
    for slug, detail in machines_detail.items():
        display = detail.get("name") or slug.replace("-", " ").title()
        machine_options[display] = slug

    selected_name = st.sidebar.selectbox("Choose a machine", sorted(machine_options.keys()))
    slug = machine_options[selected_name]
    detail = machines_detail[slug]
    segs = machine_to_segments.get(slug, [])
    family = detail.get("family", "Unknown")

    st.title(f"⚙️ {selected_name}")
    st.markdown(family_badge(family), unsafe_allow_html=True)
    st.markdown("")

    # Key numbers
    speed = detail.get("speed_bags_min")
    heads = detail.get("weighing_heads")
    fmt = detail.get("format_range_mm")
    feat = detail.get("key_feature", "")

    c1, c2, c3 = st.columns(3)
    if speed:
        c1.metric("Max Speed", f"{speed} bags/min")
    elif heads:
        c1.metric("Weighing Heads", str(heads))
    c2.metric("Format Range", f"{fmt} mm" if fmt else "—")
    c3.metric("Segments Served", len(segs))

    if feat:
        st.success(f"**Key feature:** {feat}")

    if detail.get("description"):
        st.markdown(f"*{detail['description'][:500]}*")
    if detail.get("url"):
        st.markdown(f"[View on pfm.it →]({detail['url']})")

    st.markdown("---")
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader(f"🏭 Serves {len(segs)} Segment(s)")
        for seg_name in sorted(segs):
            seg = next((a for a in apps if a["name"] == seg_name), {})
            size = seg.get("market_size_bn_eur", "")
            growth = seg.get("growth_pct", "")
            suffix = f" · €{size}B · 📈{growth}%" if size else ""
            st.markdown(f"- **{seg_name}**{suffix}")

    with col_r:
        st.subheader("📦 Relevant Pack Styles")
        all_ps = {}
        for a in apps:
            if a["name"] in segs:
                for ps in a["pack_styles"]:
                    all_ps[ps["name"]] = ps["url"]
        for name, url in sorted(all_ps.items()):
            st.markdown(f"- [{name}]({url})")


# ════════════════════════════════════════════════════════════════════════════════
# PACK STYLE
# ════════════════════════════════════════════════════════════════════════════════
elif view == "📦 Pack Style":
    all_ps = {}
    for app in apps:
        for ps in app["pack_styles"]:
            all_ps[ps["name"]] = ps["url"]

    selected_ps = st.sidebar.selectbox("Choose a pack style", sorted(all_ps.keys()))

    st.title(f"📦 {selected_ps}")
    if all_ps[selected_ps]:
        st.markdown(f"[View on pfm.it →]({all_ps[selected_ps]})")
    st.markdown("---")

    segments_with_ps = [
        a for a in apps if any(ps["name"] == selected_ps for ps in a["pack_styles"])
    ]

    # Aggregate numbers for this pack style
    total_market = sum(a.get("market_size_bn_eur", 0) for a in segments_with_ps)
    total_targets = sum(a.get("target_count_estimate", 0) for a in segments_with_ps)

    c1, c2, c3 = st.columns(3)
    c1.metric("Segments using this format", len(segments_with_ps))
    c2.metric("Combined Market Size", f"€{total_market:,.0f}B", help="Sum of estimated market sizes. Source: Statista / Euromonitor. Not verified.")
    c3.metric("Est. Total Target Companies", f"~{total_targets:,}", help="Approximation only. Verify with Matchplat or ZoomInfo.")

    st.markdown("---")
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.subheader(f"🏭 Segments ({len(segments_with_ps)})")
        sorted_segs = sorted(segments_with_ps, key=lambda a: a.get("market_size_bn_eur", 0), reverse=True)
        for a in sorted_segs:
            size = a.get("market_size_bn_eur", "—")
            growth = a.get("growth_pct", "—")
            priority = a.get("pfm_priority", "—")
            color = PRIORITY_COLORS.get(priority, "#7f7f7f")
            st.markdown(
                f'**{a["name"]}** &nbsp; €{size}B &nbsp; 📈{growth}% &nbsp; '
                + badge(priority, color),
                unsafe_allow_html=True
            )

    with col_r:
        machine_slugs = set(m["slug"] for a in segments_with_ps for m in a["machines"])
        st.subheader(f"⚙️ Compatible Machines ({len(machine_slugs)})")
        by_family = {}
        for slug in machine_slugs:
            d = machines_detail.get(slug, {})
            fam = d.get("family", "Other")
            by_family.setdefault(fam, []).append((slug, d))

        for fam, items in sorted(by_family.items()):
            color = FAMILY_COLORS.get(fam, "#7f7f7f")
            st.markdown(
                f'<div style="border-left:3px solid {color};padding-left:8px;margin:8px 0 2px 0;">'
                f'<b>{fam}</b></div>', unsafe_allow_html=True
            )
            for slug, d in sorted(items, key=lambda x: x[0]):
                name = d.get("name") or slug.replace("-", " ").title()
                speed = d.get("speed_bags_min")
                suffix = f" · {speed} bags/min" if speed else ""
                url = d.get("url", "")
                if url:
                    st.markdown(f"  - [{name}]({url}){suffix}")
                else:
                    st.markdown(f"  - {name}{suffix}")

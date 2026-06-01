"""
PFM Business Explorer
Mobile-first interactive app to understand PFM's machines, segments, and pack styles.
"""

import json
import streamlit as st

# ── Page config ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PFM Business Explorer",
    page_icon="📦",
    layout="centered",          # centered = better on mobile than "wide"
    initial_sidebar_state="collapsed"   # sidebar hidden by default on mobile
)

# ── Mobile-friendly CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Larger touch targets for expanders */
  details summary { font-size: 1.05rem; padding: 10px 0; }

  /* Metric cards: bigger value on small screens */
  [data-testid="metric-container"] { padding: 12px 10px; border-radius: 10px;
    background: rgba(255,255,255,0.05); margin-bottom: 8px; }
  [data-testid="stMetricValue"] { font-size: 1.5rem !important; }

  /* Row cards for segment table */
  .seg-card { background: rgba(255,255,255,0.05); border-radius: 10px;
    padding: 12px 14px; margin-bottom: 8px; }
  .seg-card .seg-name { font-size: 1.05rem; font-weight: 700; }
  .seg-card .seg-stats { font-size: 0.85rem; opacity: 0.8; margin-top: 4px; }

  /* Family section header */
  .fam-header { border-left: 4px solid; padding: 6px 10px;
    border-radius: 0 8px 8px 0; margin: 14px 0 6px 0;
    background: rgba(255,255,255,0.05); font-weight: 700; }

  /* Hide "Made with Streamlit" footer */
  footer { visibility: hidden; }

  /* Reduce padding on mobile */
  .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ── Load data ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    with open("data/pfm_data.json", encoding="utf-8") as f:
        raw = json.load(f)
    with open("data/enrichment.json", encoding="utf-8") as f:
        enrichment = json.load(f)

    apps = raw["applications"]
    machines_detail = raw["machines"]

    name_fixes = {"BreadCutting &": "Cut Bread", "Bread": "Cut Bread", "Meat": "Meat & Sausages"}
    for app in apps:
        app["name"] = name_fixes.get(app["name"], app["name"])
        app.update(enrichment["segments"].get(app["name"], {}))

    family_rules = {
        "azimuth": "VFFS", "comet": "VFFS", "solaris": "VFFS", "zenith": "VFFS",
        "r-700": "VFFS", "rc-700": "VFFS", "rq-700": "VFFS", "rx800": "VFFS",
        "polar": "VFFS", "vetta": "VFFS", "pv320": "VFFS", "compact": "VFFS",
        "mbp": "Multihead Weigher",
        "bora": "Flow Wrap", "falcon": "Flow Wrap", "ghibli": "Flow Wrap",
        "levante": "Flow Wrap", "mistral": "Flow Wrap", "pearl": "Flow Wrap",
        "pulsar": "Flow Wrap", "scirocco": "Flow Wrap", "shamal": "Flow Wrap",
        "tornado": "Flow Wrap", "zephyr": "Flow Wrap", "bg-2800": "Flow Wrap",
        "blizzard": "Flow Wrap", "d-series": "Stand-up Pouch", "f-series": "Stand-up Pouch",
    }
    for slug, detail in machines_detail.items():
        for key, family in family_rules.items():
            if key in slug.lower():
                detail["family"] = family
                break
        detail.update(enrichment["machines"].get(slug, {}))

    machine_to_segments = {}
    for app in apps:
        for m in app["machines"]:
            machine_to_segments.setdefault(m["slug"], [])
            if app["name"] not in machine_to_segments[m["slug"]]:
                machine_to_segments[m["slug"]].append(app["name"])

    return apps, machines_detail, machine_to_segments


apps, machines_detail, machine_to_segments = load_data()

# ── Constants ────────────────────────────────────────────────────────────────────
FAMILY_COLORS = {
    "VFFS":              "#4F8EF7",
    "Flow Wrap":         "#F7944F",
    "Multihead Weigher": "#4FCF87",
    "Stand-up Pouch":    "#B47FFF",
    "Other":             "#8899AA",
    "Unknown":           "#8899AA",
}
PRIORITY_COLORS = {"High": "#EF4444", "Medium": "#F59E0B", "Low": "#22C55E"}


# ── Helpers ──────────────────────────────────────────────────────────────────────
def badge(text, color):
    return (f'<span style="background:{color};color:white;padding:3px 12px;'
            f'border-radius:20px;font-size:0.78em;font-weight:700;'
            f'letter-spacing:0.03em;">{text}</span>')

def chip(text, bg="rgba(79,142,247,0.15)", fg="#4F8EF7"):
    return (f'<span style="background:{bg};color:{fg};padding:4px 12px;'
            f'border-radius:20px;font-size:0.85em;margin:3px;display:inline-block;">{text}</span>')

def render_chips(items, bg="rgba(79,142,247,0.15)", fg="#4F8EF7"):
    st.markdown(" ".join(chip(i, bg, fg) for i in items), unsafe_allow_html=True)

def divider():
    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.1);margin:16px 0'>",
                unsafe_allow_html=True)

def seg_card(name, size, growth, targets, priority):
    color = PRIORITY_COLORS.get(priority, "#8899AA")
    st.markdown(
        f'<div class="seg-card">'
        f'<div class="seg-name">{name} &nbsp;{badge(priority, color)}</div>'
        f'<div class="seg-stats">💰 €{size}B &nbsp;·&nbsp; 📈 {growth}%/yr &nbsp;·&nbsp; 🏢 ~{targets:,} targets</div>'
        f'</div>',
        unsafe_allow_html=True
    )

def fam_header(fam, count):
    color = FAMILY_COLORS.get(fam, "#8899AA")
    st.markdown(
        f'<div class="fam-header" style="border-color:{color}">'
        f'{fam} &nbsp;<span style="font-weight:400;font-size:0.85em;opacity:0.7">— {count} model(s)</span>'
        f'</div>',
        unsafe_allow_html=True
    )


# ── Bottom nav (mobile-style) ────────────────────────────────────────────────────
st.markdown("---")
view = st.radio(
    "Navigate",
    ["🏠 Home", "🏭 Segment", "⚙️ Machine", "📦 Pack Style"],
    horizontal=True,
    label_visibility="collapsed"
)
st.markdown("---")


# ════════════════════════════════════════════════════════════════════════════════
# HOME
# ════════════════════════════════════════════════════════════════════════════════
if view == "🏠 Home":
    st.markdown("## 📦 PFM Business Explorer")
    st.markdown(
        "**PFM Group** — Italian packaging machinery. "
        "Maps machines → industries → pack formats."
    )

    total_market = sum(a.get("market_size_bn_eur", 0) for a in apps)
    all_ps = set(ps["name"] for a in apps for ps in a["pack_styles"])

    # 2×2 grid works better on mobile than 1×4
    c1, c2 = st.columns(2)
    c1.metric("Segments", len(apps))
    c2.metric("Machine Models", len(machines_detail))
    c3, c4 = st.columns(2)
    c3.metric("Pack Styles", len(all_ps))
    c4.metric("Total Market", f"€{total_market:,.0f}B", help="Estimated. Source: Statista/Euromonitor.")

    divider()
    st.markdown("#### Machine Families")
    families = {}
    for slug, m in machines_detail.items():
        fam = m.get("family", "Unknown")
        families.setdefault(fam, []).append(slug)

    for fam, slugs in sorted(families.items()):
        color = FAMILY_COLORS.get(fam, "#8899AA")
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;'
            f'background:rgba(255,255,255,0.05);border-radius:10px;'
            f'padding:10px 14px;margin-bottom:8px;">'
            f'<div style="width:6px;height:36px;background:{color};border-radius:3px;flex-shrink:0;"></div>'
            f'<div><div style="font-weight:700">{fam}</div>'
            f'<div style="font-size:0.85em;opacity:0.7">{len(slugs)} models</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

    divider()
    st.markdown("#### Segments by Market Size")
    st.caption("📊 Estimated — Statista/Euromonitor. Verify before use.")
    sorted_apps = sorted(apps, key=lambda a: a.get("market_size_bn_eur", 0), reverse=True)
    for a in sorted_apps:
        seg_card(
            a["name"],
            a.get("market_size_bn_eur", "?"),
            a.get("growth_pct", "?"),
            a.get("target_count_estimate", 0),
            a.get("pfm_priority", "—")
        )


# ════════════════════════════════════════════════════════════════════════════════
# SEGMENT
# ════════════════════════════════════════════════════════════════════════════════
elif view == "🏭 Segment":
    segment_names = sorted(a["name"] for a in apps)
    selected = st.selectbox("Choose a segment", segment_names, label_visibility="collapsed")
    app = next(a for a in apps if a["name"] == selected)

    priority = app.get("pfm_priority", "—")
    pcolor = PRIORITY_COLORS.get(priority, "#8899AA")
    st.markdown(
        f'## 🏭 {app["name"]} &nbsp; {badge(priority, pcolor)}',
        unsafe_allow_html=True
    )

    # 2×2 metrics
    size   = app.get("market_size_bn_eur")
    growth = app.get("growth_pct")
    targets = app.get("target_count_estimate")
    invest  = app.get("avg_investment_keur")

    c1, c2 = st.columns(2)
    c1.metric("Market Size", f"€{size}B" if size else "—",
              help="Estimated — Statista/Euromonitor. Not verified.")
    c2.metric("Growth/yr", f"{growth}%" if growth else "—",
              help="Estimated — public industry reports. Not verified.")
    c3, c4 = st.columns(2)
    c3.metric("Est. Targets", f"~{targets:,}" if targets else "—",
              help="Approximation. Verify with Matchplat/Apollo/ZoomInfo.")
    c4.metric("Avg. Investment", f"~€{invest}K" if invest else "—",
              help="Rough estimate for learning only.")

    why = app.get("why_pfm")
    if why:
        st.info(f"**Why PFM wins here:** {why}")

    st.markdown(f"[🔗 View on pfm.it]({app['url']})")
    if app.get("intro"):
        with st.expander("Page description"):
            st.markdown(app["intro"])

    divider()

    # Example clients
    clients = app.get("example_clients", [])
    if clients:
        st.markdown(f"#### 🏢 Example Clients")
        render_chips(clients, bg="rgba(247,148,79,0.15)", fg="#F7944F")

    divider()

    # Machines grouped by family — full width, stacked
    st.markdown(f"#### ⚙️ Machines ({len(app['machines'])})")
    by_family = {}
    for m in app["machines"]:
        detail = machines_detail.get(m["slug"], {})
        fam = detail.get("family", "Other")
        by_family.setdefault(fam, []).append((m, detail))

    for fam, items in sorted(by_family.items()):
        fam_header(fam, len(items))
        for m, detail in items:
            speed = detail.get("speed_bags_min")
            heads = detail.get("weighing_heads")
            feat  = detail.get("key_feature", "")
            label = m["name"]
            if speed:
                label += f" · {speed} bags/min"
            elif heads:
                label += f" · {heads} heads"
            with st.expander(label):
                if feat:
                    st.markdown(f"✅ {feat}")
                fmt = detail.get("format_range_mm")
                if fmt:
                    st.markdown(f"**Format range:** {fmt} mm")
                desc = detail.get("description", "")
                if desc:
                    st.markdown(desc[:350])
                other_segs = [s for s in machine_to_segments.get(m["slug"], []) if s != app["name"]]
                if other_segs:
                    st.markdown("**Also used in:**")
                    render_chips(other_segs)
                if m.get("url"):
                    st.markdown(f"[Machine page →]({m['url']})")

    divider()

    # Pack styles — compact list
    st.markdown(f"#### 📦 Pack Styles ({len(app['pack_styles'])})")
    ps_text = " &nbsp;·&nbsp; ".join(
        f'<a href="{ps["url"]}" target="_blank" style="color:#4F8EF7">{ps["name"]}</a>'
        for ps in app["pack_styles"]
    )
    st.markdown(ps_text, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# MACHINE
# ════════════════════════════════════════════════════════════════════════════════
elif view == "⚙️ Machine":
    machine_options = {
        (detail.get("name") or slug.replace("-", " ").title()): slug
        for slug, detail in machines_detail.items()
    }
    selected_name = st.selectbox("Choose a machine", sorted(machine_options.keys()),
                                 label_visibility="collapsed")
    slug   = machine_options[selected_name]
    detail = machines_detail[slug]
    segs   = machine_to_segments.get(slug, [])
    family = detail.get("family", "Unknown")
    fcolor = FAMILY_COLORS.get(family, "#8899AA")

    st.markdown(
        f'## ⚙️ {selected_name} &nbsp; {badge(family, fcolor)}',
        unsafe_allow_html=True
    )

    speed = detail.get("speed_bags_min")
    heads = detail.get("weighing_heads")
    fmt   = detail.get("format_range_mm")
    feat  = detail.get("key_feature", "")

    c1, c2 = st.columns(2)
    if speed:
        c1.metric("Max Speed", f"{speed} bags/min")
    elif heads:
        c1.metric("Weighing Heads", str(heads))
    c2.metric("Format Range", f"{fmt} mm" if fmt else "—")

    c3, c4 = st.columns(2)
    c3.metric("Segments Served", len(segs))
    c4.metric("Family", family)

    if feat:
        st.success(f"✅ {feat}")
    if detail.get("description"):
        st.markdown(f"*{detail['description'][:400]}*")
    if detail.get("url"):
        st.markdown(f"[🔗 View on pfm.it]({detail['url']})")

    divider()
    st.markdown(f"#### 🏭 Segments Served ({len(segs)})")
    for seg_name in sorted(segs):
        seg = next((a for a in apps if a["name"] == seg_name), {})
        size   = seg.get("market_size_bn_eur", "?")
        growth = seg.get("growth_pct", "?")
        p      = seg.get("pfm_priority", "—")
        st.markdown(
            f'<div class="seg-card">'
            f'<div class="seg-name">{seg_name} &nbsp;{badge(p, PRIORITY_COLORS.get(p,"#8899AA"))}</div>'
            f'<div class="seg-stats">💰 €{size}B &nbsp;·&nbsp; 📈 {growth}%/yr</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    divider()
    st.markdown("#### 📦 Pack Styles (across its segments)")
    all_ps = {ps["name"]: ps["url"] for a in apps if a["name"] in segs for ps in a["pack_styles"]}
    ps_text = " &nbsp;·&nbsp; ".join(
        f'<a href="{url}" target="_blank" style="color:#4F8EF7">{name}</a>'
        for name, url in sorted(all_ps.items())
    )
    st.markdown(ps_text, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# PACK STYLE
# ════════════════════════════════════════════════════════════════════════════════
elif view == "📦 Pack Style":
    all_ps = {ps["name"]: ps["url"] for a in apps for ps in a["pack_styles"]}
    selected_ps = st.selectbox("Choose a pack style", sorted(all_ps.keys()),
                               label_visibility="collapsed")

    st.markdown(f"## 📦 {selected_ps}")
    if all_ps[selected_ps]:
        st.markdown(f"[🔗 View on pfm.it]({all_ps[selected_ps]})")

    segments_with_ps = [a for a in apps if any(ps["name"] == selected_ps for ps in a["pack_styles"])]
    total_market  = sum(a.get("market_size_bn_eur", 0) for a in segments_with_ps)
    total_targets = sum(a.get("target_count_estimate", 0) for a in segments_with_ps)

    c1, c2 = st.columns(2)
    c1.metric("Segments", len(segments_with_ps))
    c2.metric("Combined Market", f"€{total_market:,.0f}B",
              help="Estimated — Statista/Euromonitor. Not verified.")
    c3, c4 = st.columns(2)
    c3.metric("Est. Targets", f"~{total_targets:,}",
              help="Approximation only. Verify with Matchplat/ZoomInfo.")
    c4.markdown("")

    divider()
    st.markdown(f"#### 🏭 Segments using this format")
    sorted_segs = sorted(segments_with_ps, key=lambda a: a.get("market_size_bn_eur", 0), reverse=True)
    for a in sorted_segs:
        seg_card(
            a["name"],
            a.get("market_size_bn_eur", "?"),
            a.get("growth_pct", "?"),
            a.get("target_count_estimate", 0),
            a.get("pfm_priority", "—")
        )

    divider()
    machine_slugs = set(m["slug"] for a in segments_with_ps for m in a["machines"])
    st.markdown(f"#### ⚙️ Compatible Machines ({len(machine_slugs)})")
    by_family = {}
    for s in machine_slugs:
        d = machines_detail.get(s, {})
        by_family.setdefault(d.get("family", "Other"), []).append((s, d))

    for fam, items in sorted(by_family.items()):
        fam_header(fam, len(items))
        for s, d in sorted(items, key=lambda x: x[0]):
            name  = d.get("name") or s.replace("-", " ").title()
            speed = d.get("speed_bags_min")
            url   = d.get("url", "")
            suffix = f" · {speed} bags/min" if speed else ""
            line = f"[{name}]({url}){suffix}" if url else f"{name}{suffix}"
            st.markdown(f"- {line}")

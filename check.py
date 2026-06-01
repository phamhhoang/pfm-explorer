import json

with open("data/pfm_data.json", encoding="utf-8") as f:
    data = json.load(f)

apps = data["applications"]
machines = data["machines"]

print(f"Applications scraped: {len(apps)}")
print(f"Unique machines: {len(machines)}")
print()

for app in apps:
    names = [m["name"] for m in app["machines"]]
    ps = [p["name"] for p in app["pack_styles"]]
    print(f"[{app['name']}]")
    print(f"  Machines ({len(names)}): {', '.join(names[:5])}{'...' if len(names) > 5 else ''}")
    print(f"  Pack styles ({len(ps)}): {', '.join(ps[:4])}{'...' if len(ps) > 4 else ''}")
    print()

print("--- Machine families ---")
families = {}
for slug, m in machines.items():
    fam = m.get("family", "Unknown")
    families.setdefault(fam, []).append(slug)

for fam, slugs in sorted(families.items()):
    print(f"  {fam}: {len(slugs)} machines")

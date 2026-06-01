"""
PFM Business Explorer - Scraper
Fetches machine names and pack styles per application segment from pfm.it
Output: data/pfm_data.json
"""

import requests
from bs4 import BeautifulSoup
import json
import time

BASE_URL = "https://www.pfm.it"

APPLICATIONS = [
    "bakery", "beverages", "chocolate-confectionery", "coffee",
    "cut-bread", "dairy", "detergents", "fine-granulates", "fish",
    "frozen-foods", "fruit", "meat-sausages", "pasta",
    "pet-food", "pharma", "powders", "snacks", "sweets", "wet-wipes"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def scrape_machine(slug):
    url = f"{BASE_URL}/en/machine/{slug}/"
    soup = fetch_page(url)
    if not soup:
        return {"slug": slug, "description": "", "family": "Unknown"}

    description = ""
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if len(text) > 80:
            description = text
            break

    # Detect machine family from page content
    full_text = soup.get_text(" ", strip=True).lower()
    if "vertical form fill" in full_text or "vffs" in full_text:
        family = "VFFS"
    elif "flow wrap" in full_text or "horizontal flow" in full_text:
        family = "Flow Wrap"
    elif "stand-up" in full_text or "pouch" in full_text:
        family = "Stand-up / Pouch"
    elif "weigh" in full_text or "multihead" in full_text:
        family = "Multihead Weigher"
    else:
        family = "Other"

    return {
        "slug": slug,
        "name": slug.replace("-", " ").title(),
        "url": url,
        "description": description,
        "family": family
    }


def scrape_application(slug):
    url = f"{BASE_URL}/en/application/{slug}/"
    print(f"Scraping: {url}")
    soup = fetch_page(url)
    if not soup:
        return None

    # Segment name from h1
    h1 = soup.find("h1")
    name = h1.get_text(strip=True) if h1 else slug.replace("-", " ").title()
    # Clean "Packaging" suffix for display
    name = name.replace(" Packaging", "").replace("Packaging", "").strip()

    # Intro paragraph
    intro = ""
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if len(text) > 60:
            intro = text
            break

    # Machines: links matching /en/machine/<slug>/
    machines = []
    seen_slugs = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/en/machine/" in href:
            machine_slug = href.rstrip("/").split("/")[-1]
            if machine_slug and machine_slug not in seen_slugs:
                seen_slugs.add(machine_slug)
                label = a.get_text(strip=True)
                machines.append({
                    "slug": machine_slug,
                    "name": label if label else machine_slug.replace("-", " ").title(),
                    "url": href
                })

    # Pack styles: links matching /en/packstyle/<slug>/
    pack_styles = []
    seen_ps = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/en/packstyle/" in href:
            ps_slug = href.rstrip("/").split("/")[-1]
            if ps_slug and ps_slug not in seen_ps:
                seen_ps.add(ps_slug)
                label = a.get_text(strip=True)
                pack_styles.append({
                    "slug": ps_slug,
                    "name": label if label else ps_slug.replace("-", " ").title(),
                    "url": href
                })

    return {
        "slug": slug,
        "name": name,
        "url": url,
        "intro": intro,
        "machines": machines,
        "pack_styles": pack_styles
    }


def main():
    # Step 1: Scrape all application pages
    applications = []
    for slug in APPLICATIONS:
        data = scrape_application(slug)
        if data:
            applications.append(data)
        time.sleep(0.6)

    # Step 2: Collect unique machine slugs and scrape each machine page
    all_machine_slugs = set()
    for app in applications:
        for m in app["machines"]:
            all_machine_slugs.add(m["slug"])

    print(f"\nScraping {len(all_machine_slugs)} machine detail pages...")
    machines_detail = {}
    for slug in sorted(all_machine_slugs):
        detail = scrape_machine(slug)
        machines_detail[slug] = detail
        time.sleep(0.5)

    # Step 3: Save combined output
    output = {
        "applications": applications,
        "machines": machines_detail
    }

    output_path = "data/pfm_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone.")
    print(f"  Applications scraped: {len(applications)}")
    print(f"  Unique machines found: {len(machines_detail)}")
    print(f"  Saved to: {output_path}")

    print("\n--- Applications Summary ---")
    for app in applications:
        machine_names = [m["name"] for m in app["machines"]]
        print(f"  {app['name']}: {len(app['machines'])} machines → {', '.join(machine_names[:4])}{'...' if len(machine_names) > 4 else ''}")


if __name__ == "__main__":
    main()

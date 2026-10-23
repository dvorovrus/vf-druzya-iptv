#!/usr/bin/env python3
"""Publish a compact XMLTV guide for the selected VF IPTV channels."""
import copy
import datetime as dt
import gzip
import io
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

URL = "https://iptvx.one/EPG_LITE"
CHANNELS = {
    "vf-friends": ("VF Друзья", "https://iptvx.one/picons/vf-friends.png"),
    "vf-series": ("VF Series", "https://iptvx.one/picons/vf-series.png"),
    "vf-klinika": ("VF Клиника", "https://iptvx.one/picons/vf-klinika.png"),
}
now = dt.datetime.now(dt.timezone.utc)
earliest = (now - dt.timedelta(days=2)).strftime("%Y%m%d")
latest = (now + dt.timedelta(days=9)).strftime("%Y%m%d")

tv = ET.Element("tv", {"generator-info-name": "vf-druzya-iptv | iptvx.one"})
for channel_id, (name, logo) in CHANNELS.items():
    ch = ET.SubElement(tv, "channel", {"id": channel_id})
    ET.SubElement(ch, "display-name", {"lang": "ru"}).text = name
    ET.SubElement(ch, "icon", {"src": logo})

request = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(request, timeout=60) as response:
    compressed = response.read()
found = {key: 0 for key in CHANNELS}
for _, el in ET.iterparse(gzip.GzipFile(fileobj=io.BytesIO(compressed)), events=("end",)):
    if el.tag != "programme":
        continue
    channel_id = el.get("channel")
    start = el.get("start", "")[:8]
    if channel_id in CHANNELS and earliest <= start <= latest:
        tv.append(copy.deepcopy(el))
        found[channel_id] += 1
    el.clear()

if not found["vf-series"]:
    raise RuntimeError("VF Series EPG is empty; refusing to replace the last guide")
ET.indent(tv, space="  ")
Path("epg.xml").write_bytes(ET.tostring(tv, encoding="utf-8", xml_declaration=True))
print("Programmes:", found, "|", Path("epg.xml").stat().st_size, "bytes")

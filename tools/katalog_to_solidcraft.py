"""Turn the material entries of the knowledge catalog into a SolidCraft material library.

    python3 tools/katalog_to_solidcraft.py [out.solidcraft-library.json]
    (default katalog/werkstoffe.solidcraft-library.json)

Each entry in katalog/eintraege/werkstoffe/ becomes a SolidCraft material with its density, a default
look (PBR) and a physical card (schema 1, SI units) whose properties name the source they come from.
SolidCraft itself validates the cards (material.create) and writes the library (library.export), so
the format and the entry revisions are SolidCraft's own.

Values the catalog gives as a range go into the card conservatively: strengths take the lower bound,
density, stiffness and thermal values the middle. For 3D-printed plastics the weaker of the XY and Z
values is taken. Each property's source is the catalog source whose quotation contains the number.
"""
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from mechvane.documents import PART, Workspace  # noqa: E402

KATALOG = REPO / "katalog" / "eintraege" / "werkstoffe"

# Display name in SolidCraft, family, colour and PBR look per catalog id
LOOKS = {
    "s235jr": ("S235JR", "metal", "#8a9097", 1.0, 0.45),
    "s355j2": ("S355J2", "metal", "#868c93", 1.0, 0.45),
    "c45_verguetet": ("C45 +QT", "metal", "#80868d", 1.0, 0.4),
    "42crmo4_verguetet": ("42CrMo4 +QT", "metal", "#7a8087", 1.0, 0.4),
    "1_4301": ("1.4301 (X5CrNi18-10)", "metal", "#b8bcc0", 1.0, 0.25),
    "1_4404": ("1.4404 (X2CrNiMo17-12-2)", "metal", "#b4b9be", 1.0, 0.25),
    "en_aw_6060_t6": ("EN AW-6060 T6", "metal", "#c6cacf", 1.0, 0.3),
    "en_aw_6082_t6": ("EN AW-6082 T6", "metal", "#c2c6cb", 1.0, 0.3),
    "en_aw_7075_t6": ("EN AW-7075 T6", "metal", "#bcc0c5", 1.0, 0.3),
    "en_aw_5083_h111": ("EN AW-5083 H111", "metal", "#c0c4c8", 1.0, 0.35),
    "en_gjl_250": ("EN-GJL-250", "metal", "#5c6064", 1.0, 0.65),
    "cuzn39pb3": ("CuZn39Pb3 (CW614N)", "metal", "#c9a74e", 1.0, 0.3),
    "pom_c": ("POM-C", "polymer", "#efeeea", 0.0, 0.45),
    "pa6_trocken": ("PA6 (dry)", "polymer", "#e9e3d2", 0.0, 0.5),
    "pla": ("PLA (3D print)", "polymer", "#d9d9d6", 0.0, 0.5),
    "petg": ("PETG (3D print)", "polymer", "#c9d8de", 0.0, 0.3),
    "11smnpb30": ("11SMnPb30", "metal", "#868b91", 1.0, 0.4),
    "1_4305": ("1.4305 (X8CrNiS18-9)", "metal", "#b6babe", 1.0, 0.25),
    "1_4571": ("1.4571 (X6CrNiMoTi17-12-2)", "metal", "#b2b7bc", 1.0, 0.25),
    "cu_etp": ("Cu-ETP (CW004A)", "metal", "#d27a4a", 1.0, 0.2),
    "en_ac_42100": ("EN AC-42100 T6", "metal", "#b9bdc2", 1.0, 0.5),
    "en_aw_2007": ("EN AW-2007", "metal", "#c0c4c9", 1.0, 0.3),
    "pa12_sls": ("PA12 (SLS)", "polymer", "#ecebe6", 0.0, 0.7),
    "pa6_gf30": ("PA6-GF30", "polymer", "#2b2b2c", 0.0, 0.55),
    "pa_cf": ("PA-CF (3D print)", "polymer", "#2a2b2d", 0.0, 0.6),
    "pc": ("PC", "polymer", "#dfe7ec", 0.0, 0.15),
    "asa": ("ASA (3D print)", "polymer", "#d8d9d6", 0.0, 0.5),
    "tpu_95a": ("TPU 95A (3D print)", "polymer", "#3a3b3d", 0.0, 0.7),
}

TO_SI = {"mpa": 1e6, "n/mm²": 1e6, "kn/mm²": 1e9, "gpa": 1e9, "kg/dm³": 1000.0, "g/cm³": 1000.0,
         "kg/m³": 1.0, "w/(m*k)": 1.0, "10^-6/k": 1e-6, "": 1.0}


def numbers(w: dict) -> list[float]:
    return list(w["bereich"]) if "bereich" in w else [w["wert"]] if w.get("wert") is not None else []


def pick(werte, pattern, how, skip=r"$^"):
    """Value in SI of the entries whose name matches: 'low' = smallest lower bound, 'mid' = mean of
    the first matching entry. Returns (value, raw numbers) or None."""
    rows = [w for w in werte if re.search(pattern, w["name"]) and not re.search(skip, w["name"]) and numbers(w)]
    if not rows:
        return None
    unit = lambda w: TO_SI[w.get("einheit", "").strip().lower()]  # noqa: E731
    if how == "low":
        w = min(rows, key=lambda w: min(numbers(w)) * unit(w))
        return float(f"{min(numbers(w)) * unit(w):.6g}"), numbers(w)
    w = rows[0]
    n = numbers(w)
    return float(f"{sum(n) / len(n) * unit(w):.6g}"), n


def source_for(raw, quellen) -> str:
    """Id of the first source whose quotation holds one of the numbers (German or English decimals)."""
    for i, q in enumerate(quellen):
        text = q.get("zitat", "")
        for x in raw:
            s = f"{x:g}"
            if re.search(rf"(?<![\d.,]){re.escape(s)}(?![\d])", text) or \
                    re.search(rf"(?<![\d.,]){re.escape(s.replace('.', ','))}(?![\d])", text):
                return f"s{i + 1}"
    return "s1"


def card(entry: dict, family: str) -> tuple[dict, float]:
    werte, quellen = entry["werte"], entry["quellen"]
    state = ", ".join(entry["geltungsbereich"].get("werkstoff", [])[:2])
    props = []

    def add(kind, data, found, note=""):
        props.append({"data": dict(kind=kind, **data), "source_id": source_for(found[1], quellen),
                      "conditions": {"temperature_k": 293.15, "state": (state + note)[:200]}})

    dens = pick(werte, r"^Dichte", "mid")
    if dens:
        add("density", {"kg_m3": dens[0]}, dens)
    e = pick(werte, r"^Elastizitaetsmodul", "mid", skip=r"Z-Druck")
    nu = pick(werte, r"^Querkontraktionszahl", "mid")
    if e and nu:
        add("elasticity", {"model": {"symmetry": "isotropic", "young_modulus_pa": e[0], "poisson_ratio": nu[0]}}, e,
            ", XY print direction" if family == "polymer" and "XY" in str(werte) else "")
    for kind, pattern, skip in (("tensile_strength", r"^Zugfestigkeit", r"$^"),
                                ("yield_strength", r"Dehngrenze Rp0,2|Streckgrenze|Streckspannung|ReH", r"Rp0,1"),
                                ("compressive_strength", r"^Druckfestigkeit", r"$^"),
                                ("shear_strength", r"^Scherfestigkeit", r"$^")):
        v = pick(werte, pattern, "low", skip)
        if v:
            add(kind, {"pa": v[0]}, v, ", minimum" + (" of XY and Z" if "Z-Druck" in str(werte) else ""))
    k = pick(werte, r"^Waermeleitfaehigkeit", "mid")
    if k:
        add("thermal_conductivity", {"w_m_k": [k[0]] * 3, "axes": "material123"}, k)
    a = pick(werte, r"^Waermeausdehnungskoeffizient", "mid")
    if a:
        add("thermal_expansion", {"per_k": [a[0]] * 3, "axes": "material123"}, a)
    sources = [{"id": f"s{i + 1}", "title": (q.get("stelle") or q["url"])[:200], "kind": "public_reference",
                "reference": q["url"]} for i, q in enumerate(quellen)]
    return ({"schema_version": 1, "designation": LOOKS[entry["id"]][0], "family": family,
             "sources": sources, "properties": props}, dens[0] / 1000.0 if dens else None)


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "katalog" / "werkstoffe.solidcraft-library.json"
    entries = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(KATALOG.glob("*.json"))]
    tmp = Path(tempfile.mkdtemp(prefix="mv-library-"))
    ws = Workspace(tmp)
    try:
        s = ws.new(PART, "library").session
        for entry in entries:
            name, family, color, metallic, rough = LOOKS[entry["id"]]
            c, density = card(entry, family)
            s.cmd("material.properties.validate", {"card": c})
            # SolidCraft wants all three; the IOR only shapes the dielectric (plastic) look
            pbr = {"metallic": metallic, "roughness": rough, "dielectric_ior": 1.5}
            s.cmd("material.create", {"name": name, "density_g_cm3": density, "color": color, "pbr": pbr,
                                      "physical_card": c})
            print(f"{name:26} {len(c['properties'])} properties, {density} g/cm³")
        out.parent.mkdir(parents=True, exist_ok=True)
        # SolidCraft writes only into folders it may use: export next to the session, then copy
        written = tmp / out.name
        s.cmd("library.export", {"path": str(written), "id": "mechvane.werkstoffe",
                                 "name": "Mechvane materials (knowledge catalog)", "overwrite": True,
                                 # the compilation is Mechvane's; each value names its own source in the card
                                 "provenance": {"license": "MIT OR Apache-2.0", "author": "Mechvane contributors",
                                                "source_url": "https://github.com/mechvane/mechvane/tree/main/katalog/eintraege/werkstoffe"}})
        shutil.copyfile(written, out)
        print("wrote", out)
    finally:
        ws.close_all()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()

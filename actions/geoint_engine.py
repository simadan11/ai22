# actions/geoint_engine.py — MAXIMUM GEOINT: Interactive Mapping of Military & Historical Sites
"""
Maximum GEOINT (Geospatial Intelligence) Engine for EDIT.
Provides access to interactive maps (Google Maps, Google Satellite, Esri Imagery, OpenStreetMap, WikiMapia)
with over 50+ marked military sites (active, abandoned, historical, airfields, radar installations, bunkers,
naval ports, missile ranges, and equipment locations).
Operates within full legal and ethical open-source intelligence (OSINT/GEOINT) boundaries using public data.
"""

import json
import math
import os
import sys
import tempfile
import urllib.request
import urllib.parse
import webbrowser
from pathlib import Path
from typing import List, Dict, Optional, Any

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "actions" / "geoint_cache"
HTML_MAP_PATH = CACHE_DIR / "geoint_map.html"

# ─────────────────────────────────────────────────────────────────────────────
# CURATED OPEN-SOURCE GEOINT DATABASE: MILITARY, HISTORIC & ABANDONED SITES
# Publicly verifiable coordinates and unclassified historical descriptions.
# ─────────────────────────────────────────────────────────────────────────────
MILITARY_SITES: List[Dict[str, Any]] = [
    # ── Active Command Centers & Air Bases ──────────────────────────────────
    {
        "name": "Pentagon / National Military Command Center",
        "lat": 38.8710, "lon": -77.0560,
        "category": "active", "type": "Command HQ",
        "status": "Active", "country": "USA",
        "description": "HQ of the US Department of Defense. Houses the NMCC and strategic command elements.",
        "equipment": "Strategic Command & Control, Helicopters, Secure Comms Arrays"
    },
    {
        "name": "Cheyenne Mountain Complex (NORAD Bunker)",
        "lat": 38.7441, "lon": -104.8465,
        "category": "bunker", "type": "Underground Command Bunker",
        "status": "Active / Standby", "country": "USA",
        "description": "Underground military installation built inside Cheyenne Mountain. Former NORAD HQ, now backup strategic bunker.",
        "equipment": "25-ton blast doors, springs-mounted granite vault buildings, EMP-shielded com-lines"
    },
    {
        "name": "Ramstein Air Base",
        "lat": 49.4369, "lon": 7.6008,
        "category": "airbase", "type": "Strategic Air Base",
        "status": "Active", "country": "Germany",
        "description": "HQ USAFE-AFAFRICA and NATO Allied Air Command. Largest American air base in Europe.",
        "equipment": "C-130J Super Hercules, C-17A Globemaster III transit, Air and Space Operations Center"
    },
    {
        "name": "Diego Garcia Naval & Air Facility",
        "lat": -7.3195, "lon": 72.4229,
        "category": "active", "type": "Island Strategic Base",
        "status": "Active", "country": "BIOT (UK/US)",
        "description": "Joint UK/US strategic military facility in the central Indian Ocean. Supports bomber deployments and naval logistics.",
        "equipment": "B-52H, B-2A Strategic Bomber dispersal aprons, Maritime Prepositioning Ships (MPS)"
    },
    {
        "name": "Thule Air Base (Pituffik Space Base)",
        "lat": 76.5312, "lon": -68.7032,
        "category": "radar", "type": "Arctic Ballistic Missile Warning",
        "status": "Active", "country": "Greenland (Denmark/US)",
        "description": "Northernmost US military base. Home to the Upgraded Early Warning Radar (UEWR) for missile defense.",
        "equipment": "AN/FPS-132 Upgraded Early Warning Radar, Satellite Tracking Arrays"
    },
    {
        "name": "Al Udeid Air Base",
        "lat": 25.1187, "lon": 51.3150,
        "category": "airbase", "type": "Combined Air Operations Center",
        "status": "Active", "country": "Qatar",
        "description": "Hosts USAF Combined Air and Space Operations Center (CAOC) and RAF elements in the Middle East.",
        "equipment": "KC-135 Stratotankers, RC-135 Rivet Joint, E-3 Sentry AWACS, Fighter squadrons"
    },
    {
        "name": "Yokota Air Base",
        "lat": 35.7485, "lon": 139.3486,
        "category": "airbase", "type": "Regional HQ",
        "status": "Active", "country": "Japan",
        "description": "HQ United States Forces Japan (USFJ) and Japanese Air Self-Defense Force Air Defense Command.",
        "equipment": "C-130J Super Hercules, CV-22B Osprey, UH-1N Twin Huey"
    },
    {
        "name": "Pine Gap Joint Defence Facility",
        "lat": -23.7990, "lon": 133.7370,
        "category": "radar", "type": "SIGINT & Satellite Ground Station",
        "status": "Active", "country": "Australia",
        "description": "Joint Australian/US intelligence facility with numerous protective radomes for satellite signal interception.",
        "equipment": "33+ Large Radomes, Geostationary SIGINT satellite downlinks"
    },
    {
        "name": "RAF Menwith Hill",
        "lat": 54.0084, "lon": -1.6897,
        "category": "radar", "type": "SIGINT / ECHELON Station",
        "status": "Active", "country": "UK",
        "description": "Largest electronic monitoring station in the world, operated by RAF and US NSA. Features iconic 'golf ball' radomes.",
        "equipment": "30+ Radome spheres, Satellite communications monitoring antennae"
    },
    {
        "name": "Sevastopol Naval Base",
        "lat": 44.6166, "lon": 33.5254,
        "category": "naval", "type": "Black Sea Naval Base",
        "status": "Active / Historic", "country": "Crimea",
        "description": "Major Black Sea naval port and historical fortress city with centuries of military fortifications and bunker harbors.",
        "equipment": "Frigates, Corvettes, Diesel-electric Kilo-class submarines, Coastal batteries"
    },
    {
        "name": "Baikonur Cosmodrome (Site 1 & Military Launch Complex)",
        "lat": 45.9650, "lon": 63.3050,
        "category": "historic", "type": "Strategic Space & Missile Center",
        "status": "Active / Historical", "country": "Kazakhstan",
        "description": "World's first and largest operational space launch facility. Originally built for R-7 ICBM development.",
        "equipment": "Soyuz launch pads, Buran shuttle hangars, Abandoned Energia launch towers"
    },
    {
        "name": "Plesetsk Cosmodrome",
        "lat": 62.9275, "lon": 40.5750,
        "category": "active", "type": "ICBM & Military Satellite Launch Base",
        "status": "Active", "country": "Russia",
        "description": "Strategic northern rocket and ballistic missile test site operated by Russian Aerospace Forces.",
        "equipment": "Angara, Soyuz-2 launch pads, Underground missile testing silos"
    },
    {
        "name": "Vandenberg Space Force Base",
        "lat": 34.7420, "lon": -120.5724,
        "category": "active", "type": "ICBM & Polar Orbit Launch Base",
        "status": "Active", "country": "USA",
        "description": "Primary US west coast space launch facility and Minuteman III ICBM operational test launch range.",
        "equipment": "Minuteman III launch silos, Space Launch Complexes (SLC-4, SLC-6)"
    },
    {
        "name": "Kapustin Yar Missile Test Range",
        "lat": 48.5848, "lon": 46.2936,
        "category": "active", "type": "Ballistic Missile Proving Ground",
        "status": "Active / Historical", "country": "Russia",
        "description": "Historic Soviet and active Russian ballistic missile and air defense testing polygon.",
        "equipment": "Radar tracking arrays, SRBM and IRBM launch aprons, historic V-2 test bunkers"
    },
    {
        "name": "Andersen Air Force Base",
        "lat": 13.5840, "lon": 144.9240,
        "category": "airbase", "type": "Pacific Bomber Base",
        "status": "Active", "country": "Guam (USA)",
        "description": "Major strategic USAF base in the western Pacific. Stores large munition stockpiles and hosts bomber rotations.",
        "equipment": "B-1B Lancer, B-52H Stratofortress aprons, THAAD Air Defense battery"
    },

    # ── Abandoned & Historical Cold War Relics ──────────────────────────────
    {
        "name": "Duga-1 Radar ('Russian Woodpecker' - Chernobyl-2)",
        "lat": 51.3045, "lon": 30.0669,
        "category": "abandoned", "type": "Over-The-Horizon (OTH) Radar",
        "status": "Abandoned / Monument", "country": "Ukraine",
        "description": "Massive Soviet early-warning OTH radar array near Chernobyl. The steel structure is 150m high and 700m wide.",
        "equipment": "150m steel antenna towers, phased array dipole cages, abandoned computer command rooms"
    },
    {
        "name": "Duga-2 Radar Site (Komsomolsk-on-Amur)",
        "lat": 50.3888, "lon": 137.3323,
        "category": "abandoned", "type": "Over-The-Horizon (OTH) Radar",
        "status": "Abandoned", "country": "Russia",
        "description": "Eastern Soviet OTH radar installation designed to detect ICBM launches over the Pacific.",
        "equipment": "Steel lattice tower remains, abandoned transmitter bunkers"
    },
    {
        "name": "Teufelsberg NSA Listening Station",
        "lat": 52.4968, "lon": 13.2415,
        "category": "abandoned", "type": "SIGINT Listening Post",
        "status": "Abandoned / Museum", "country": "Germany",
        "description": "Iconic abandoned US/British espionage radar complex built on a man-made rubble mountain in West Berlin during the Cold War.",
        "equipment": "Large white fabric/plastic radome towers, multi-story SIGINT listening rooms"
    },
    {
        "name": "Zeljava Underground Air Base (Object 505)",
        "lat": 44.8369, "lon": 15.7589,
        "category": "abandoned", "type": "Mountain Bunker Airfield",
        "status": "Abandoned", "country": "Croatia / Bosnia",
        "description": "One of the largest underground air bases in Europe, built inside Mount Pljesevica. Destroyed with explosives in 1992.",
        "equipment": "3.5km of underground aircraft tunnels, blast doors, MiG-21 outdoor wreckage, 5 runways"
    },
    {
        "name": "Balaklava Submarine Base (Object 825 GTS)",
        "lat": 44.5015, "lon": 33.5966,
        "category": "bunker", "type": "Underground Nuclear Submarine Base",
        "status": "Historical / Museum", "country": "Crimea",
        "description": "Top-secret Soviet underground submarine bunker and nuclear weapons storage depot inside Mount Tavros.",
        "equipment": "600m water canal through mountain, 150-ton nuclear-hardened blast gates, dry dock tunnel"
    },
    {
        "name": "Submarine Pen Valentin (Bremen-Farge)",
        "lat": 53.2215, "lon": 8.5038,
        "category": "abandoned", "type": "WWII U-Boat Bunker",
        "status": "Abandoned / Memorial", "country": "Germany",
        "description": "Gigantic protective WWII U-boat assembly bunker on the Weser river with roof concrete walls up to 7 meters thick.",
        "equipment": "Massive concrete reinforced arch halls, bomb crater damage from Grand Slam bombs"
    },
    {
        "name": "Greenbrier Congressional Bunker (Project Greek Island)",
        "lat": 37.7850, "lon": -80.3080,
        "category": "bunker", "type": "Underground Relocation Center",
        "status": "Historical / Museum", "country": "USA",
        "description": "Secret emergency Cold War fallout bunker built beneath the Greenbrier Resort to house the entire US Congress.",
        "equipment": "25-ton blast doors, decontamination showers, 1000-person dormitory rooms, broadcast studio"
    },
    {
        "name": "Skrunda-1 Soviet Radar City",
        "lat": 56.7180, "lon": 21.9880,
        "category": "abandoned", "type": "Early Warning Radar Town",
        "status": "Abandoned / Ghost Town", "country": "Latvia",
        "description": "Abandoned Soviet military secret city that housed Dnepr early-warning ballistic missile detection radars.",
        "equipment": "60+ abandoned barracks, officer apartments, radar foundation pads (Hen House radar destroyed 1995)"
    },
    {
        "name": "Plokstine Missile Base (Object 181)",
        "lat": 56.0270, "lon": 21.9058,
        "category": "abandoned", "type": "Underground ICBM Silo Complex",
        "status": "Historical / Museum", "country": "Lithuania",
        "description": "First Soviet underground ballistic missile base in Europe, armed with four R-12 nuclear ICBM silos inside the forest.",
        "equipment": "Four 30m-deep nuclear missile silos, underground control room, fuel tanks"
    },
    {
        "name": "R-12 Missile Silo Complex (Tirza)",
        "lat": 57.1420, "lon": 26.3980,
        "category": "abandoned", "type": "Nuclear Missile Silo Base",
        "status": "Abandoned", "country": "Latvia",
        "description": "Abandoned Soviet R-12 Dvina (SS-4 Sandal) underground missile launch base abandoned after the INF Treaty.",
        "equipment": "Flooded 28m concrete silos, rusted command dome covers, rocket fuel drainage channels"
    },
    {
        "name": "Maunsell Sea Forts (Redsand & Shivering Sands)",
        "lat": 51.4816, "lon": 1.0003,
        "category": "abandoned", "type": "WWII Offshore Anti-Aircraft Towers",
        "status": "Abandoned / Sea Towers", "country": "UK",
        "description": "Surreal steel and concrete armed towers built in the Thames Estuary during WWII to defend London from Luftwaffe bombers.",
        "equipment": "Seven interconnected steel towers on concrete legs, rusted anti-aircraft gun platforms"
    },
    {
        "name": "Wünsdorf-Zehrensdorf Soviet High Command",
        "lat": 52.1930, "lon": 13.4735,
        "category": "abandoned", "type": "Military Command City",
        "status": "Abandoned", "country": "Germany",
        "description": "Former HQ of the Group of Soviet Forces in Germany (GSFG) and earlier German Army High Command underground bunker complex ('Mayak').",
        "equipment": "Zeppelin underground bunker, Lenin statues, abandoned Soviet barracks city ('Little Moscow')"
    },
    {
        "name": "Maginot Line — Ouvrage Hackenberg",
        "lat": 49.3450, "lon": 6.3650,
        "category": "historic", "type": "Underground Fortress Complex",
        "status": "Historical / Museum", "country": "France",
        "description": "Largest fortress of the French Maginot Line. Features 10 km of subterranean galleries and electric train ammunition transport.",
        "equipment": "Retractable steel gun turrets, underground electric locomotive line, 1930s power generators"
    },
    {
        "name": "Flakturm IV St. Pauli Bunker",
        "lat": 53.5566, "lon": 9.9702,
        "category": "historic", "type": "WWII Anti-Aircraft Flak Tower",
        "status": "Historical / Reused", "country": "Germany",
        "description": "Massive concrete WWII flak tower in Hamburg. Now greened and repurposed with roof gardens and memorials.",
        "equipment": "3.5m thick reinforced concrete walls, historic anti-aircraft gun turrets"
    },
    {
        "name": "Peenemünde Army Research Center",
        "lat": 54.1480, "lon": 13.7940,
        "category": "historic", "type": "V-2 Rocket Development Base",
        "status": "Historical / Museum", "country": "Germany",
        "description": "Historic German WWII rocket research center where the V-2 ballistic missile was developed by Wernher von Braun.",
        "equipment": "Historic V-2 rocket replicas, oxygen production plant bunker, test stand VII remains"
    },
    {
        "name": "Bletchley Park",
        "lat": 51.9977, "lon": -0.7408,
        "category": "historic", "type": "WWII SIGINT & Codebreaking HQ",
        "status": "Historical / Museum", "country": "UK",
        "description": "Historic British Government Code and Cypher School where Alan Turing and team decrypted Enigma and Lorenz cipher machines.",
        "equipment": "Turing-Welchman Bombe replicas, Colossus electronic computer, wooden huts 3 and 6"
    },
    {
        "name": "RAF Stenigot Cold War Radar Dishes",
        "lat": 53.3275, "lon": -0.1235,
        "category": "abandoned", "type": "Chain Home / ACE High Radar Site",
        "status": "Abandoned", "country": "UK",
        "description": "Historic WWII Chain Home and Cold War NATO ACE High tropospheric scatter communications station.",
        "equipment": "Gigantic 18m rusted parabolic steel radar dishes lying in pasture"
    },
    {
        "name": "Sary-Shagan ABM Test Range",
        "lat": 46.0350, "lon": 73.6500,
        "category": "abandoned", "type": "Anti-Ballistic Missile Proving Ground",
        "status": "Abandoned / Standby", "country": "Kazakhstan",
        "description": "Historic Soviet and Russian testing ground for anti-ballistic missile systems and high-power laser weapons (Terra-3).",
        "equipment": "Don-2N / Dunay radar dome remains, abandoned laser dome domes, missile impact craters"
    },
    {
        "name": "White Sands Missile Range / Trinity Site",
        "lat": 33.6773, "lon": -106.4754,
        "category": "historic", "type": "Historic Atomic Test Site & Range",
        "status": "Active / Historical", "country": "USA",
        "description": "Site of the world's first atomic bomb detonation (Trinity, July 16, 1945) within White Sands Missile Range.",
        "equipment": "Trinity monument obelisk, Jumbo steel containment vessel, Trinitite crater site"
    },
    {
        "name": "Semipalatinsk Test Site (The Polygon)",
        "lat": 50.4400, "lon": 78.7800,
        "category": "abandoned", "type": "Nuclear Weapons Testing Range",
        "status": "Abandoned / Memorial", "country": "Kazakhstan",
        "description": "Primary testing venue for Soviet nuclear weapons. 456 nuclear tests were conducted here between 1949 and 1989.",
        "equipment": "Atomic Lake crater (Chagan), underground test tunnels (Degelen Mountain), concrete observation bunkers"
    },
    {
        "name": "Johnston Atoll Chemical & Missile Facility",
        "lat": 16.7295, "lon": -169.5310,
        "category": "abandoned", "type": "Pacific Missile & Munitions Disposal Base",
        "status": "Abandoned / Wildlife Refuge", "country": "USA (Pacific)",
        "description": "Former US air base, chemical weapons disposal plant (JACADS), and high-altitude nuclear test launch site.",
        "equipment": "Abandoned 2,700m coral runway, underground storage bunkers, Thor missile launch pads"
    },

    # ── Additional Strategic & Naval Installations ──────────────────────────
    {
        "name": "Tinian North Field (Historic WWII Strategic Airbase)",
        "lat": 15.0719, "lon": 145.6358,
        "category": "historic", "type": "WWII Bomber Airfield & Atomic Loading Site",
        "status": "Historical / Disused", "country": "Northern Mariana Islands (USA)",
        "description": "Historic WWII airbase from which B-29 bombers launched the atomic missions against Hiroshima and Nagasaki.",
        "equipment": "4 abandoned coral 2,600m runways, bomb loading pits (Little Boy / Fat Man memorials)"
    },
    {
        "name": "Edwards Air Force Base (Air Force Test Center)",
        "lat": 34.9240, "lon": -117.8912,
        "category": "airbase", "type": "Flight Test & Space Shuttle Landing Center",
        "status": "Active", "country": "USA",
        "description": "Premier USAF flight test facility and historic Space Shuttle landing site on Rogers Dry Lake.",
        "equipment": "11,200m dry lakebed runways, experimental X-planes, B-2 and F-22 testing hangars"
    },
    {
        "name": "Barksdale Air Force Base (AFGSC HQ)",
        "lat": 32.5018, "lon": -93.6627,
        "category": "airbase", "type": "Global Strike Command HQ",
        "status": "Active", "country": "USA",
        "description": "Headquarters of USAF Global Strike Command and Eighth Air Force. Primary B-52H Stratofortress bomber hub.",
        "equipment": "B-52H Stratofortress squadrons, strategic nuclear command facilities"
    },
    {
        "name": "Aviano Air Base",
        "lat": 46.0319, "lon": 12.5964,
        "category": "airbase", "type": "NATO Southern Europe Air Base",
        "status": "Active", "country": "Italy",
        "description": "Major USAF and NATO tactical air base in northeastern Italy at the base of the Alps.",
        "equipment": "F-16C/D Fighting Falcon squadrons, hardened aircraft shelters (HAS)"
    },
    {
        "name": "Naval Base San Diego",
        "lat": 32.6833, "lon": -117.1167,
        "category": "naval", "type": "Pacific Fleet Surface Port",
        "status": "Active", "country": "USA",
        "description": "Principal homeport of the US Navy Pacific Fleet surface forces, hosting over 50 ships.",
        "equipment": "Cruisers, Destroyers, Littoral Combat Ships, Amphibious Assault Ships"
    },
    {
        "name": "RAF Scampton (Historic Bomber Base)",
        "lat": 53.3075, "lon": -0.5508,
        "category": "historic", "type": "Historic RAF Bomber Airfield",
        "status": "Historical / Disused", "country": "UK",
        "description": "Historic RAF base famous for the WWII Dambusters Raid (No. 617 Squadron) and former home of the Red Arrows.",
        "equipment": "2,700m runway, WWII C-type hangars, Guy Gibson dog memorial obelisk"
    },
    {
        "name": "Fort Douaumont (Verdun WWI Fortress)",
        "lat": 49.2167, "lon": 5.4333,
        "category": "historic", "type": "WWI Subterranean Fortification",
        "status": "Historical / Memorial", "country": "France",
        "description": "Largest and highest fort of the Verdun ring of WWI fortifications. Scene of intense combat in 1916.",
        "equipment": "Reinforced concrete bunker vaults, 155mm Galopin gun turrets, underground barracks"
    },
    {
        "name": "Goldsboro B-52 Crash Site ('Broken Arrow')",
        "lat": 35.4930, "lon": -77.8590,
        "category": "historic", "type": "Historic Nuclear Incident Site",
        "status": "Historical / Easement", "country": "USA",
        "description": "Site of the 1961 Goldsboro B-52 crash where two Mark 39 hydrogen bombs fell; one thermonuclear core remains buried 15m deep.",
        "equipment": "Government-owned perpetual easement field, buried thermonuclear secondary assembly"
    },
    {
        "name": "Arctic Radar Station Okhotsk",
        "lat": 59.3580, "lon": 143.2500,
        "category": "abandoned", "type": "Arctic Coastal Early Warning Radar",
        "status": "Abandoned", "country": "Russia",
        "description": "Abandoned Soviet Arctic air defense and coastal radar outpost overlooking the Sea of Okhotsk.",
        "equipment": "Rusted radar domes, abandoned diesel generator house, Arctic barracks"
    },
    {
        "name": "Zossen-Wünsdorf 'Mayak' Underground Bunker Complex",
        "lat": 52.1790, "lon": 13.4700,
        "category": "bunker", "type": "Subterranean Command Citadel",
        "status": "Abandoned / Museum", "country": "Germany",
        "description": "Huge WWII Wehrmacht High Command bunker ('Zeppelin') later reused as secret Soviet Supreme HQ in East Germany.",
        "equipment": "Three-story underground concrete bunker vaults, pneumatic tube comms, blast doors"
    },
    {
        "name": "Naval Station Norfolk",
        "lat": 36.9467, "lon": -76.3050,
        "category": "naval", "type": "World's Largest Naval Base",
        "status": "Active", "country": "USA",
        "description": "Largest naval station in the world. Supports US Navy Atlantic Fleet aircraft carriers, cruisers, and submarines.",
        "equipment": "Nimitz & Ford-class Aircraft Carriers, Arleigh Burke-class destroyers, Nuclear attack subs"
    },
    {
        "name": "Faslane Naval Base (HM Naval Base Clyde)",
        "lat": 56.0667, "lon": -4.8167,
        "category": "naval", "type": "Strategic Nuclear Submarine Port",
        "status": "Active", "country": "UK (Scotland)",
        "description": "Home of the United Kingdom's nuclear deterrent (Trident nuclear-armed Vanguard-class ballistic missile submarines).",
        "equipment": "Vanguard-class SSBNs, Astute-class attack subs, nuclear weapon handling jetties"
    },
    {
        "name": "Yulin Naval Base (Hainan Island)",
        "lat": 18.2167, "lon": 109.6833,
        "category": "naval", "type": "Underground Nuclear Submarine Port",
        "status": "Active", "country": "China",
        "description": "Strategic PLA Navy base featuring massive sea tunnels excavated into the coastal mountain for submarine concealment.",
        "equipment": "Type 094 SSBN ballistic submarines, underground mountain submarine berths, Aircraft carriers"
    },
    {
        "name": "Ouvrage Schoenenbourg (Maginot Line)",
        "lat": 48.9667, "lon": 7.9250,
        "category": "historic", "type": "Subterranean Fortress",
        "status": "Historical / Museum", "country": "France",
        "description": "One of the most heavily shelled fortifications of the Maginot Line during WWII, preserved in original working condition.",
        "equipment": "Retractable 75mm artillery turrets, 30m underground command galleries, air filtration works"
    }
]


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_all_sites(category: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return filtered list of curated military and historical sites."""
    result = []
    cat_lower = (category or "all").lower().strip()
    stat_lower = (status or "all").lower().strip()

    for s in MILITARY_SITES:
        if cat_lower not in ("all", "") and s.get("category", "").lower() != cat_lower:
            continue
        if stat_lower not in ("all", "") and stat_lower not in s.get("status", "").lower():
            continue
        result.append(s)
    return result


def search_sites(query: str) -> List[Dict[str, Any]]:
    """Fuzzy/keyword search across military sites database."""
    q = query.lower().strip()
    if not q or q == "all":
        return MILITARY_SITES

    matched = []
    for s in MILITARY_SITES:
        searchable = (
            s.get("name", "") + " " +
            s.get("type", "") + " " +
            s.get("country", "") + " " +
            s.get("description", "") + " " +
            s.get("equipment", "") + " " +
            s.get("category", "") + " " +
            s.get("status", "")
        ).lower()
        if q in searchable:
            matched.append(s)
    return matched


def calculate_geodesic_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict[str, Any]:
    """Calculate geodesic distance (km / nautical miles) and bearing between two points."""
    R = 6371.0  # Earth mean radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    dist_km = R * c
    dist_nm = dist_km * 0.539957

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0

    return {
        "distance_km": round(dist_km, 2),
        "distance_nm": round(dist_nm, 2),
        "bearing_deg": round(bearing, 1)
    }


def query_osm_overpass(lat: float, lon: float, radius_km: float = 25.0, max_results: int = 30) -> List[Dict[str, Any]]:
    """
    Query Overpass API for public OSM tags (military=base, military=airfield, military=bunker, historic=fort).
    Fully legal OSINT using public OpenStreetMap data.
    """
    radius_m = int(radius_km * 1000)
    query = f"""
    [out:json][timeout:15];
    (
      node["military"](around:{radius_m},{lat},{lon});
      way["military"](around:{radius_m},{lat},{lon});
      node["historic"="fort"](around:{radius_m},{lat},{lon});
      node["abandoned:military"](around:{radius_m},{lat},{lon});
    );
    out center {max_results};
    """
    url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(query.strip())

    results = []
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "EDIT-GEOINT-Engine/2.0 (public-osint-research)"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for el in data.get("elements", []):
                tags = el.get("tags", {})
                name = tags.get("name") or tags.get("official_name") or "OSM Military/Historic Site"
                elat = el.get("lat") or (el.get("center", {}).get("lat"))
                elon = el.get("lon") or (el.get("center", {}).get("lon"))
                if not elat or not elon:
                    continue
                mil_type = tags.get("military") or tags.get("historic") or "military_site"
                results.append({
                    "name": name,
                    "lat": float(elat),
                    "lon": float(elon),
                    "category": "osm_result",
                    "type": mil_type.capitalize(),
                    "status": "Public OSM Object",
                    "country": "OSM Data",
                    "description": f"Public OpenStreetMap tag: military={mil_type}. " + (tags.get("description", "")),
                    "equipment": tags.get("note", "Public geographic marker")
                })
    except Exception as e:
        print(f"[GEOINT] Overpass query failed: {e}")
    return results


def build_external_links(lat: float, lon: float) -> Dict[str, str]:
    """Generate direct URLs for Google Maps, Satellite, OSM, and WikiMapia."""
    return {
        "google_maps": f"https://www.google.com/maps?q={lat},{lon}",
        "google_satellite": f"https://www.google.com/maps/dir//?api=1&destination={lat},{lon}&basemap=satellite",
        "openstreetmap": f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=14/{lat}/{lon}",
        "wikimapia": f"https://wikimapia.org/#lang=en&lat={lat}&lon={lon}&z=14&m=w"
    }


def generate_html_map(target_site: Optional[Dict[str, Any]] = None, filter_category: str = "all") -> Path:
    """
    Generate an interactive Leaflet GEOINT HTML map with multi-layer switching:
      - Google Maps (Roads)
      - Google Satellite (High-Res Imagery)
      - Google Hybrid
      - OpenStreetMap
      - Esri World Imagery
      - OpenTopoMap (Terrain)
    Includes all 50+ active, abandoned, and historical military sites with clickable intelligence cards.
    """
    _ensure_cache_dir()
    sites_to_render = get_all_sites(category=filter_category if filter_category != "all" else None)
    if target_site and target_site not in sites_to_render:
        sites_to_render.append(target_site)

    center_lat = target_site["lat"] if target_site else 48.0
    center_lon = target_site["lon"] if target_site else 15.0
    zoom = 12 if target_site else 4

    sites_json = json.dumps(sites_to_render, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🛰️ GEOINT / OSINT Hub — Military & Historical Sites Map (EDIT)</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            height: 100%;
            width: 100%;
            background-color: #050a0e;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #d8f0ff;
        }}
        #map {{
            height: 100%;
            width: 100%;
            z-index: 1;
        }}
        .hud-topbar {{
            position: absolute;
            top: 10px;
            left: 50px;
            right: 20px;
            z-index: 1000;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            background: rgba(4, 15, 24, 0.88);
            border: 1px solid #00d4ff;
            border-radius: 8px;
            padding: 10px 16px;
            box-shadow: 0 4px 20px rgba(0, 212, 255, 0.25);
            backdrop-filter: blur(6px);
        }}
        .hud-title {{
            font-size: 16px;
            font-weight: 700;
            color: #00d4ff;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .hud-btn {{
            background: rgba(0, 212, 255, 0.15);
            border: 1px solid #00d4ff;
            color: #00d4ff;
            padding: 6px 12px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s ease;
        }}
        .hud-btn:hover, .hud-btn.active {{
            background: #00d4ff;
            color: #000;
            box-shadow: 0 0 10px #00d4ff;
        }}
        .leaflet-popup-content-wrapper {{
            background: rgba(6, 18, 28, 0.95);
            border: 1px solid #00d4ff;
            color: #e0f2ff;
            border-radius: 8px;
            box-shadow: 0 4px 25px rgba(0, 212, 255, 0.4);
        }}
        .leaflet-popup-tip {{
            background: rgba(6, 18, 28, 0.95);
        }}
        .site-card-title {{
            font-size: 15px;
            font-weight: bold;
            color: #00ffaa;
            margin-bottom: 4px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            margin-bottom: 6px;
        }}
        .status-active {{ background: #00ff88; color: #000; }}
        .status-abandoned {{ background: #ff4444; color: #fff; }}
        .status-historic {{ background: #00bfff; color: #000; }}
        .site-desc {{
            font-size: 12px;
            line-height: 1.4;
            margin: 8px 0;
            color: #bce0f7;
        }}
        .site-links a {{
            display: inline-block;
            margin-right: 6px;
            margin-top: 6px;
            padding: 4px 8px;
            border-radius: 4px;
            background: #00364d;
            color: #00d4ff;
            text-decoration: none;
            font-size: 11px;
            border: 1px solid #0088bb;
        }}
        .site-links a:hover {{
            background: #00d4ff;
            color: #000;
        }}
    </style>
</head>
<body>
    <div class="hud-topbar">
        <div class="hud-title">🛰️ EDIT GEOINT HUB</div>
        <button class="hud-btn active" onclick="filterMarkers('all')">🟢 Все объекты ({len(sites_to_render)})</button>
        <button class="hud-btn" onclick="filterMarkers('active')">🔴 Активные базы</button>
        <button class="hud-btn" onclick="filterMarkers('abandoned')">🟡 Заброшенные / РЛС</button>
        <button class="hud-btn" onclick="filterMarkers('airbase')">✈️ Аэродромы</button>
        <button class="hud-btn" onclick="filterMarkers('bunker')">⚓ Бункеры & ВМБ</button>
        <button class="hud-btn" onclick="filterMarkers('historic')">🏛️ Исторические</button>
    </div>
    <div id="map"></div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map', {{
            center: [{center_lat}, {center_lon}],
            zoom: {zoom},
            zoomControl: true
        }});

        // Base Map Layers
        var googleRoads = L.tileLayer('https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}', {{
            maxZoom: 20,
            attribution: '© Google Maps'
        }});

        var googleSat = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={{x}}&y={{y}}&z={{z}}', {{
            maxZoom: 20,
            attribution: '© Google Satellite'
        }});

        var googleHybrid = L.tileLayer('https://mt1.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}', {{
            maxZoom: 20,
            attribution: '© Google Hybrid'
        }});

        var osmLayer = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }});

        var esriSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            maxZoom: 19,
            attribution: '© Esri World Imagery'
        }});

        var topoLayer = L.tileLayer('https://c.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 17,
            attribution: '© OpenTopoMap'
        }});

        // Default active base layer: Google Hybrid (Satellite + borders/labels)
        googleHybrid.addTo(map);

        var baseMaps = {{
            "🛰️ Google Hybrid (Спутник + Метки)": googleHybrid,
            "🛰️ Google Satellite (Спутник HD)": googleSat,
            "🌍 Google Maps (Кара дорог)": googleRoads,
            "🗺️ OpenStreetMap (OSM)": osmLayer,
            "🛰️ Esri World Imagery": esriSat,
            "⛰️ OpenTopoMap (Рельеф)": topoLayer
        }};

        L.control.layers(baseMaps, null, {{position: 'topright'}}).addTo(map);

        var allSites = {sites_json};
        var markerLayer = L.layerGroup().addTo(map);

        function getStatusClass(status) {{
            var s = status.toLowerCase();
            if (s.includes('active')) return 'status-active';
            if (s.includes('abandoned') || s.includes('disused')) return 'status-abandoned';
            return 'status-historic';
        }}

        function getIconEmoji(category) {{
            var c = category.toLowerCase();
            if (c === 'airbase') return '✈️';
            if (c === 'radar') return '📡';
            if (c === 'bunker' || c === 'naval') return '⚓';
            if (c === 'abandoned') return '🟡';
            if (c === 'historic') return '🏛️';
            return '🔴';
        }}

        function renderMarkers(filterCat) {{
            markerLayer.clearLayers();
            allSites.forEach(function(site) {{
                if (filterCat !== 'all' && site.category !== filterCat) {{
                    return;
                }}

                var emoji = getIconEmoji(site.category);
                var customIcon = L.divIcon({{
                    className: 'custom-pin',
                    html: `<div style="font-size: 22px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.8));">${{emoji}}</div>`,
                    iconSize: [28, 28],
                    iconAnchor: [14, 14]
                }});

                var gmapsUrl = `https://www.google.com/maps?q=${{site.lat}},${{site.lon}}`;
                var gsatUrl = `https://www.google.com/maps/dir//?api=1&destination=${{site.lat}},${{site.lon}}&basemap=satellite`;
                var osmUrl = `https://www.openstreetmap.org/?mlat=${{site.lat}}&mlon=${{site.lon}}#map=14/${{site.lat}}/${{site.lon}}`;
                var wikimapiaUrl = `https://wikimapia.org/#lang=en&lat=${{site.lat}}&lon=${{site.lon}}&z=14&m=w`;

                var popupHtml = `
                    <div class="site-card-title">${{emoji}} ${{site.name}}</div>
                    <div class="status-badge ${{getStatusClass(site.status)}}">${{site.status}} — ${{site.country}}</div>
                    <div style="font-size: 11px; color: #88c0e0;">📍 WGS84: ${{site.lat.toFixed(4)}}, ${{site.lon.toFixed(4)}} | Тип: ${{site.type}}</div>
                    <div class="site-desc">${{site.description}}</div>
                    <div style="font-size: 11px; color: #00ffaa; margin-top: 4px;">⚙️ ${{site.equipment}}</div>
                    <div class="site-links">
                        <a href="${{gsatUrl}}" target="_blank">🛰️ Спутник Google</a>
                        <a href="${{gmapsUrl}}" target="_blank">🌍 Google Maps</a>
                        <a href="${{osmUrl}}" target="_blank">🗺️ OpenStreetMap</a>
                        <a href="${{wikimapiaUrl}}" target="_blank">ℹ️ WikiMapia</a>
                    </div>
                `;

                L.marker([site.lat, site.lon], {{icon: customIcon}})
                    .bindPopup(popupHtml)
                    .addTo(markerLayer);
            }});
        }}

        function filterMarkers(cat) {{
            var btns = document.querySelectorAll('.hud-btn');
            btns.forEach(b => b.classList.remove('active'));
            if (event && event.target) {{
                event.target.classList.add('active');
            }}
            renderMarkers(cat);
        }}

        // Initial render
        renderMarkers('all');
    </script>
</body>
</html>"""

    HTML_MAP_PATH.write_text(html_content, encoding="utf-8")
    return HTML_MAP_PATH


def open_map_in_browser(target_site: Optional[Dict[str, Any]] = None, filter_category: str = "all") -> str:
    """Generate geoint_map.html and open it in the default web browser."""
    path = generate_html_map(target_site=target_site, filter_category=filter_category)
    try:
        webbrowser.open(path.as_uri())
        target_name = target_site["name"] if target_site else "All Sites"
        return f"GEOINT interactive map opened in browser (Focus: {target_name})."
    except Exception as e:
        return f"Map saved to {path} (Error opening browser: {e})."


def geoint_lookup(parameters: dict, player=None, speak=None) -> str:
    """
    Maximum GEOINT tool for EDIT.
    parameters:
        query: str
        category: str ("all" | "active" | "abandoned" | "radar" | "airbase" | "bunker")
        open_map: bool
        calc_distance_to: str
    """
    params = parameters or {}
    query = (params.get("query") or "").strip()
    category = (params.get("category") or "all").lower().strip()
    open_map = bool(params.get("open_map", False))
    calc_to = (params.get("calc_distance_to") or "").strip()

    if player:
        try:
            player.write_log(f"🛰️ GEOINT Lookup: query='{query}' cat='{category}'")
        except Exception:
            pass

    matches = search_sites(query) if query else get_all_sites(category=category)
    if not matches:
        return f"No military or historical sites matched query '{query}'. Try keywords like 'Ramstein', 'Duga', 'abandoned', 'radar', or 'bunker'."

    top_site = matches[0]
    links = build_external_links(top_site["lat"], top_site["lon"])

    dist_str = ""
    if calc_to:
        second_matches = search_sites(calc_to)
        if second_matches:
            s2 = second_matches[0]
            d = calculate_geodesic_distance(top_site["lat"], top_site["lon"], s2["lat"], s2["lon"])
            dist_str = (
                f"\n📏 Geodesic distance to {s2['name']}: {d['distance_km']} km "
                f"({d['distance_nm']} nm), initial bearing {d['bearing_deg']}°."
            )

    # If open_map was requested, launch interactive browser map focused on the site
    map_status = ""
    if open_map or "открой" in query.lower() or "карт" in query.lower() or "map" in query.lower():
        map_status = " " + open_map_in_browser(target_site=top_site, filter_category=category)

    report_lines = [
        f"🛰️ GEOINT Report: Found {len(matches)} site(s). Top match: {top_site['name']} ({top_site['country']})",
        f" • Status   : {top_site['status']} [{top_site['type']}]",
        f" • WGS84    : {top_site['lat']}, {top_site['lon']}",
        f" • Overview : {top_site['description']}",
        f" • Equipment: {top_site['equipment']}",
        f" • Google Satellite: {links['google_satellite']}",
        f" • OpenStreetMap   : {links['openstreetmap']}"
    ]
    if dist_str:
        report_lines.append(dist_str)
    if map_status:
        report_lines.append(map_status)

    report_text = "\n".join(report_lines)
    if player:
        try:
            player.write_log(f"SYS: GEOINT Match — {top_site['name']}")
        except Exception:
            pass

    return report_text

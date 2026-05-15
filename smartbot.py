"""
SmartPlayer - Advanced Pokemon Showdown Battle Bot
- Format: Gen 9 Anything Goes
- Has a built-in competitive AG team
- Plays ladder AND accepts challenges from anyone (AG only)
- Uses pkmn.github.io Smogon sets API (like Showdex) for opponent stat estimation
- Uses proper Gen 9 damage formula instead of raw base power scoring
"""

import asyncio
import math
import aiohttp
from poke_env.player import Player
from poke_env import (
    AccountConfiguration,
    ShowdownServerConfiguration,
)

# ---------------------------------------------------------------------------
# YOUR SETTINGS
# ---------------------------------------------------------------------------
BOT_USERNAME  = "verycoolbot"
BOT_PASSWORD  = "verycoolbotpass"
BATTLE_FORMAT = "gen9anythinggoes"
LADDER_GAMES  = 100

# pkmn / Showdex data endpoints
PKMN_SETS_URL  = "https://pkmn.github.io/smogon/data/sets/gen9anythinggoes.json"
PKMN_STATS_URL = "https://pkmn.github.io/smogon/data/stats/gen9anythinggoes.json"

# ---------------------------------------------------------------------------
# TEAM (Showdown paste format)
# ---------------------------------------------------------------------------
AG_TEAM = """
Zacian-Crowned @ Rusted Sword
Ability: Intrepid Sword
Tera Type: Normal
EVs: 252 Atk / 4 SpD / 252 Spe
Jolly Nature
- Behemoth Blade
- Play Rough
- Close Combat
- Protect

Calyrex-Shadow @ Choice Scarf
Ability: As One (Spectrier)
Tera Type: Ghost
EVs: 252 SpA / 4 SpD / 252 Spe
Timid Nature
- Astral Barrage
- Psyshock
- Energy Ball
- Nasty Plot

Eternatus @ Heavy-Duty Boots
Ability: Pressure
Tera Type: Poison
EVs: 252 SpA / 4 SpD / 252 Spe
Timid Nature
- Dynamax Cannon
- Sludge Bomb
- Flamethrower
- Recover

Miraidon @ Choice Specs
Ability: Hadron Engine
Tera Type: Electric
EVs: 252 SpA / 4 SpD / 252 Spe
Timid Nature
- Electro Drift
- Draco Meteor
- Dazzling Gleam
- Volt Switch

Groudon @ Leftovers
Ability: Drought
Tera Type: Ground
EVs: 248 HP / 8 Atk / 252 SpD
Careful Nature
- Precipice Blades
- Stone Edge
- Stealth Rock
- Thunder Wave

Necrozma-Dusk-Mane @ Leftovers
Ability: Prism Armor
Tera Type: Steel
EVs: 252 Atk / 4 SpD / 252 Spe
Jolly Nature
- Sunsteel Strike
- Earthquake
- Dragon Dance
- Morning Sun
"""
# ---------------------------------------------------------------------------

TYPE_CHART = {
    "normal":   {"rock": 0.5, "ghost": 0, "steel": 0.5},
    "fire":     {"fire": 0.5, "water": 0.5, "rock": 0.5, "dragon": 0.5,
                 "grass": 2, "ice": 2, "bug": 2, "steel": 2},
    "water":    {"water": 0.5, "grass": 0.5, "dragon": 0.5,
                 "fire": 2, "ground": 2, "rock": 2},
    "grass":    {"fire": 0.5, "grass": 0.5, "poison": 0.5, "flying": 0.5,
                 "bug": 0.5, "dragon": 0.5, "steel": 0.5,
                 "water": 2, "ground": 2, "rock": 2},
    "electric": {"grass": 0.5, "electric": 0.5, "dragon": 0.5, "ground": 0,
                 "water": 2, "flying": 2},
    "ice":      {"water": 0.5, "ice": 0.5, "steel": 0.5, "fire": 0.5,
                 "grass": 2, "ground": 2, "flying": 2, "dragon": 2},
    "fighting": {"poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5,
                 "fairy": 0.5, "ghost": 0,
                 "normal": 2, "rock": 2, "steel": 2, "ice": 2, "dark": 2},
    "poison":   {"poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5,
                 "steel": 0, "grass": 2, "fairy": 2},
    "ground":   {"grass": 0.5, "bug": 0.5, "flying": 0,
                 "fire": 2, "electric": 2, "poison": 2, "rock": 2, "steel": 2},
    "flying":   {"electric": 0.5, "rock": 0.5, "steel": 0.5,
                 "grass": 2, "fighting": 2, "bug": 2},
    "psychic":  {"psychic": 0.5, "steel": 0.5, "dark": 0,
                 "fighting": 2, "poison": 2},
    "bug":      {"fire": 0.5, "fighting": 0.5, "flying": 0.5, "ghost": 0.5,
                 "steel": 0.5, "fairy": 0.5,
                 "grass": 2, "psychic": 2, "dark": 2},
    "rock":     {"fighting": 0.5, "ground": 0.5, "steel": 0.5,
                 "fire": 2, "ice": 2, "flying": 2, "bug": 2},
    "ghost":    {"normal": 0, "dark": 0.5, "ghost": 2, "psychic": 2},
    "dragon":   {"steel": 0.5, "fairy": 0, "dragon": 2},
    "dark":     {"fighting": 0.5, "dark": 0.5, "fairy": 0.5,
                 "ghost": 2, "psychic": 2},
    "steel":    {"steel": 0.5, "fire": 0.5, "water": 0.5, "electric": 0.5,
                 "ice": 2, "rock": 2, "fairy": 2},
    "fairy":    {"fire": 0.5, "poison": 0.5, "steel": 0.5,
                 "dragon": 2, "dark": 2, "fighting": 2},
}

# Nature modifiers: (boosted_stat, reduced_stat)
NATURE_MODIFIERS = {
    "Hardy": {}, "Docile": {}, "Serious": {}, "Bashful": {}, "Quirky": {},
    "Lonely": {"atk": 1.1, "def": 0.9},
    "Brave":  {"atk": 1.1, "spe": 0.9},
    "Adamant":{"atk": 1.1, "spa": 0.9},
    "Naughty":{"atk": 1.1, "spd": 0.9},
    "Bold":   {"def": 1.1, "atk": 0.9},
    "Relaxed":{"def": 1.1, "spe": 0.9},
    "Impish": {"def": 1.1, "spa": 0.9},
    "Lax":    {"def": 1.1, "spd": 0.9},
    "Timid":  {"spe": 1.1, "atk": 0.9},
    "Hasty":  {"spe": 1.1, "def": 0.9},
    "Jolly":  {"spe": 1.1, "spa": 0.9},
    "Naive":  {"spe": 1.1, "spd": 0.9},
    "Modest": {"spa": 1.1, "atk": 0.9},
    "Mild":   {"spa": 1.1, "def": 0.9},
    "Quiet":  {"spa": 1.1, "spe": 0.9},
    "Rash":   {"spa": 1.1, "spd": 0.9},
    "Calm":   {"spd": 1.1, "atk": 0.9},
    "Gentle": {"spd": 1.1, "def": 0.9},
    "Sassy":  {"spd": 1.1, "spe": 0.9},
    "Careful":{"spd": 1.1, "spa": 0.9},
}

# ---------------------------------------------------------------------------
# Showdex-style: global caches populated at startup from pkmn.github.io
# ---------------------------------------------------------------------------
SMOGON_SETS: dict  = {}   # {species_name: {set_name: set_data}}
SMOGON_STATS: dict = {}   # {species_name: usage stats blob}


async def fetch_pkmn_data():
    """Fetch Smogon set + usage data from pkmn.github.io (like Showdex does)."""
    global SMOGON_SETS, SMOGON_STATS
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(PKMN_SETS_URL, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    SMOGON_SETS = await r.json(content_type=None)
                    print(f"[Showdex] Loaded sets for {len(SMOGON_SETS)} species")
                else:
                    print(f"[Showdex] Sets fetch failed: HTTP {r.status}")
        except Exception as e:
            print(f"[Showdex] Sets fetch error: {e}")

        try:
            async with session.get(PKMN_STATS_URL, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json(content_type=None)
                    # pkmn stats structure: data["pokemon"] = {name: {...}}
                    SMOGON_STATS = data.get("pokemon", {})
                    print(f"[Showdex] Loaded usage stats for {len(SMOGON_STATS)} species")
                else:
                    print(f"[Showdex] Stats fetch failed: HTTP {r.status}")
        except Exception as e:
            print(f"[Showdex] Stats fetch error: {e}")


# ---------------------------------------------------------------------------
# Stat calculation helpers (Gen 9 formula, Showdex-style)
# ---------------------------------------------------------------------------

def calc_stat(base: int, ev: int, iv: int, level: int, nature_mod: float,
              is_hp: bool = False) -> int:
    """Gen 9 stat formula (same as Showdex / @smogon/calc uses)."""
    if is_hp:
        return math.floor(((2 * base + iv + math.floor(ev / 4)) * level) / 100) + level + 10
    else:
        return math.floor(
            (math.floor(((2 * base + iv + math.floor(ev / 4)) * level) / 100) + 5) * nature_mod
        )


def parse_evs(ev_string: str) -> dict:
    """Parse EV string like '252 Atk / 4 SpD / 252 Spe' into dict."""
    evs = {"hp": 0, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0}
    stat_map = {
        "HP": "hp", "Atk": "atk", "Def": "def",
        "SpA": "spa", "SpD": "spd", "Spe": "spe"
    }
    if not ev_string:
        return evs
    for part in ev_string.split("/"):
        part = part.strip()
        tokens = part.split()
        if len(tokens) >= 2:
            try:
                val = int(tokens[0])
                key = stat_map.get(tokens[1], None)
                if key:
                    evs[key] = val
            except ValueError:
                pass
    return evs


def get_best_set(species_name: str) -> dict | None:
    """
    Return the first (most notable) Smogon set for a species.
    Normalise the key the same way Showdex does (strip hyphens/spaces, lower).
    """
    if not SMOGON_SETS:
        return None
    # Try a few key formats
    for key in [species_name,
                species_name.replace("-", " "),
                species_name.replace(" ", "-")]:
        entry = SMOGON_SETS.get(key)
        if entry:
            sets = list(entry.values())
            return sets[0] if sets else None
    return None


def estimate_opponent_stat(pokemon, stat_name: str, fallback: int = 100) -> int:
    """
    Estimate an opponent's stat using Smogon set data (Showdex approach).
    Falls back to actual stats if known, then base stats, then Smogon sets.
    """
    # Try actual known stats first (poke-env populates these)
    try:
        val = pokemon.stats.get(stat_name) if pokemon.stats else None
        if val:
            return val
    except Exception:
        pass

    # Try Smogon set data
    species = pokemon.species if hasattr(pokemon, "species") else ""
    best_set = get_best_set(species)
    if best_set:
        evs_raw    = best_set.get("evs", "")
        nature_str = best_set.get("nature", "Hardy")
        if isinstance(evs_raw, dict):
            ev_map = {k.lower()[:3].replace("spa", "spa").replace("spd", "spd"): v
                      for k, v in evs_raw.items()}
        else:
            ev_map = parse_evs(str(evs_raw))

        base = getattr(pokemon, "base_stats", {}).get(stat_name, fallback)
        ev   = ev_map.get(stat_name, 0)
        iv   = 31
        nature_mod = NATURE_MODIFIERS.get(nature_str, {}).get(stat_name, 1.0)
        level = getattr(pokemon, "level", 100)
        is_hp = stat_name == "hp"
        return calc_stat(base, ev, iv, level, nature_mod, is_hp)

    # Final fallback: base stats
    try:
        return pokemon.base_stats.get(stat_name, fallback)
    except Exception:
        return fallback


# ---------------------------------------------------------------------------
# Type / move helpers
# ---------------------------------------------------------------------------

def type_multiplier(move_type: str, defending_types: list) -> float:
    m = 1.0
    chart = TYPE_CHART.get(move_type.lower(), {})
    for t in defending_types:
        m *= chart.get(t.lower(), 1.0)
    return m


def get_types(pokemon) -> list:
    return [t.name for t in pokemon.types if t is not None]


def get_stat(pokemon, stat_name: str, fallback: int = 100) -> int:
    try:
        val = pokemon.stats.get(stat_name) if pokemon.stats else None
        if val:
            return val
    except Exception:
        pass
    try:
        return pokemon.base_stats.get(stat_name, fallback)
    except Exception:
        return fallback


# ---------------------------------------------------------------------------
# Showdex-style damage formula (Gen 9)
# ---------------------------------------------------------------------------

def showdex_damage(move, attacker, defender, use_tera: bool = False) -> float:
    """
    Approximate Gen 9 damage using proper Atk/Def stats and STAB/type mods,
    mirroring what Showdex's @smogon/calc does internally.
    Returns expected damage as fraction of defender's max HP.
    """
    if move.base_power == 0:
        return 0.0

    level = getattr(attacker, "level", 100)

    # Determine attacker stat (physical vs special)
    is_special = move.category.name == "SPECIAL" if hasattr(move, "category") else False
    atk_stat   = "spa" if is_special else "atk"
    def_stat   = "spd" if is_special else "def"

    atk = get_stat(attacker, atk_stat, 100)
    # Use Showdex-style estimation for defender's defensive stat
    dfn = estimate_opponent_stat(defender, def_stat, 100)
    hp  = estimate_opponent_stat(defender, "hp", 250)

    # Attacker types (tera override)
    if use_tera and hasattr(attacker, "tera_type") and attacker.tera_type:
        attacker_types = [attacker.tera_type.name]
    else:
        attacker_types = get_types(attacker)

    defender_types  = get_types(defender)
    effectiveness   = type_multiplier(move.type.name, defender_types)

    # STAB (Tera Stellar STAB = 2.25 if original type, 1.5 otherwise)
    stab = 1.0
    if move.type.name in attacker_types:
        stab = 2.25 if (use_tera and move.type.name in get_types(attacker)) else 1.5

    # Accuracy factor
    accuracy = move.accuracy
    if isinstance(accuracy, bool) or accuracy is None:
        accuracy = 100
    acc_factor = accuracy / 100.0

    # PP scarcity penalty
    pp_factor = 1.0
    if hasattr(move, "current_pp") and move.current_pp is not None:
        if move.current_pp <= 1:
            pp_factor = 0.5

    # Gen 9 base damage formula (ignoring random roll -> use 0.925 average)
    base_damage = (
        math.floor(
            math.floor(
                math.floor(2 * level / 5 + 2) * move.base_power * atk / dfn
            ) / 50
        ) + 2
    ) * 0.925  # average of 85-100% roll

    raw = base_damage * stab * effectiveness * acc_factor * pp_factor
    # Return as fraction of defender's max HP (like Showdex shows %)
    return raw / hp


def incoming_damage_fraction(attacker, defender) -> float:
    """
    Estimate the best damage the opponent could do to us (as HP fraction).
    Uses Showdex-style estimation for attacker's offensive stat.
    """
    defender_types = get_types(defender)
    best = 0.0
    level = getattr(attacker, "level", 100)

    for move in attacker.moves.values():
        if move.base_power == 0:
            continue
        is_special = move.category.name == "SPECIAL" if hasattr(move, "category") else False
        atk_stat   = "spa" if is_special else "atk"
        def_stat   = "spd" if is_special else "def"

        atk = estimate_opponent_stat(attacker, atk_stat, 100)
        dfn = get_stat(defender, def_stat, 100)
        hp  = get_stat(defender, "hp", 250)

        eff  = type_multiplier(move.type.name, defender_types)
        stab = 1.5 if move.type.name in get_types(attacker) else 1.0

        base_damage = (
            math.floor(
                math.floor(
                    math.floor(2 * level / 5 + 2) * move.base_power * atk / dfn
                ) / 50
            ) + 2
        ) * 0.925

        score = base_damage * stab * eff / hp
        if score > best:
            best = score

    return best if best > 0 else 0.25  # default ~25% if no moves known


def we_outspeed(our_pokemon, opponent) -> bool:
    our_spe = get_stat(our_pokemon, "spe", 80)
    opp_spe = estimate_opponent_stat(opponent, "spe", 80)
    return our_spe > opp_spe


def evaluate_switch(candidate, opponent) -> float:
    if candidate.current_hp_fraction < 0.15:
        return -1.0
    best_dmg = 0.0
    for move in candidate.moves.values():
        d = showdex_damage(move, candidate, opponent)
        if d > best_dmg:
            best_dmg = d
    if best_dmg == 0:
        for ct in get_types(candidate):
            eff = type_multiplier(ct, get_types(opponent))
            est = eff * 0.3
            if est > best_dmg:
                best_dmg = est
    threat = incoming_damage_fraction(opponent, candidate)
    defense_factor = 1.0 / (1.0 + threat)
    return best_dmg * candidate.current_hp_fraction * defense_factor


def status_move_value(move, battle) -> float:
    name   = move.id.lower()
    active = battle.active_pokemon
    opponent = battle.opponent_active_pokemon

    if name in ("stealthrock", "spikes", "toxicspikes"):
        return 0.30
    if name in ("toxic", "thunderwave", "willowisp"):
        if opponent and opponent.status is None and we_outspeed(active, opponent):
            return 0.20
        return 0.05
    if name in ("swordsdance", "nastyplot", "calmmind", "dragondance", "quiverdance"):
        if active.current_hp_fraction > 0.6:
            if opponent and incoming_damage_fraction(opponent, active) < 0.25:
                return 0.25
        return 0.05
    if name in ("recover", "roost", "moonlight", "synthesis", "slackoff", "softboiled"):
        return 0.30 if active.current_hp_fraction < 0.5 else 0.02
    return 0.03


# ---------------------------------------------------------------------------
# Main bot class
# ---------------------------------------------------------------------------

class SmartPlayer(Player):

    def choose_move(self, battle):
        active   = battle.active_pokemon
        opponent = battle.opponent_active_pokemon

        # --- Terastallize decision (Showdex-style: check type effectiveness) ---
        use_tera = False
        if battle.can_tera and opponent is not None:
            if hasattr(active, "tera_type") and active.tera_type:
                tera_eff = type_multiplier(active.tera_type.name, get_types(opponent))
                if tera_eff >= 2.0 and active.current_hp_fraction > 0.5:
                    use_tera = True

        # --- Score every available move ---
        best_move  = None
        best_score = -1.0
        for move in battle.available_moves:
            if move.base_power > 0:
                score = showdex_damage(move, active, opponent, use_tera) if opponent else move.base_power / 200
            else:
                score = status_move_value(move, battle)
            if score > best_score:
                best_score = score
                best_move  = move

        # --- Switch decision ---
        should_switch = False
        if opponent and battle.available_switches:
            threat = incoming_damage_fraction(opponent, active)
            # Switch if we're threatened and can't outspeed
            if not we_outspeed(active, opponent) and threat > 0.50:
                should_switch = True
            # Switch if low HP
            if active.current_hp_fraction < 0.30:
                should_switch = True
            # Switch if best move does basically nothing
            if best_score < 0.05:
                should_switch = True

        if should_switch and battle.available_switches:
            best_switch       = None
            best_switch_score = -1.0
            for candidate in battle.available_switches:
                score = evaluate_switch(candidate, opponent)
                if score > best_switch_score:
                    best_switch_score = score
                    best_switch       = candidate
            if best_switch and best_switch_score > 0:
                return self.create_order(best_switch)

        if best_move:
            if use_tera and best_move.base_power > 0:
                return self.create_order(best_move, terastallize=True)
            return self.create_order(best_move)

        return self.choose_random_move(battle)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    print("Fetching Showdex-style set + usage data from pkmn.github.io...")
    await fetch_pkmn_data()

    account = AccountConfiguration(BOT_USERNAME, BOT_PASSWORD)
    bot = SmartPlayer(
        account_configuration=account,
        server_configuration=ShowdownServerConfiguration,
        max_concurrent_battles=2,
        battle_format=BATTLE_FORMAT,
        team=AG_TEAM,
    )

    print(f"Connecting as {BOT_USERNAME} to pokemonshowdown.com...")
    print(f"Format: {BATTLE_FORMAT}")
    print("Accepting challenges from anyone (AG only)!")

    await asyncio.gather(
        bot.ladder(LADDER_GAMES),
        bot.accept_challenges(None, 9999),
    )


if __name__ == "__main__":
    asyncio.run(main())

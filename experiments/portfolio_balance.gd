extends Node

# A controlled sensitivity study. The intervention is stat scaling, not typing.
const MULTIPLIERS := [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]
const TRAIN_N := 256
const TEST_N := 1024
const LEVEL := 30
const ROSTER_SEED := 741911
const OUTPUT := "res://portfolio_balance.json"

var templates: Dictionary = {}
var singles: Array[String] = []
var duals: Array[String] = []
var failures: Array[String] = []

func _ready() -> void:
	call_deferred("run")

func run() -> void:
	GameBalance.restore_shipped()
	var roster_rng := RandomNumberGenerator.new()
	roster_rng.seed = ROSTER_SEED
	Gojomon.sim_rng = roster_rng
	if CombatResolver.load_effects() == null:
		push_error("The effects pipeline is unavailable; refusing a simplified simulation.")
		get_tree().quit(2)
		return
	var ids: Array = AspectsDB.aspects.keys()
	ids.sort()
	var roster: Array = []
	for id_value in ids:
		var id := String(id_value)
		var asp: Dictionary = AspectsDB.get_aspects(id)
		if Array(asp.get("tags", [])).has("legendary") or not Dictionary(asp.get("evolve_conditions", {})).is_empty():
			continue
		var types: Array = asp.get("types", [])
		if types.size() not in [1, 2]:
			continue
		var mon := Gojomon.new(id, LEVEL)
		mon.moves = Gojomon.moves_for_level(id, LEVEL)
		var unit := Gojomon.to_dict(mon)
		unit["instance_id"] = "portfolio_" + id
		templates[id] = unit
		if types.size() == 1: singles.append(id)
		else: duals.append(id)
		var exported := unit.duplicate(true)
		for key in ["display", "scene_path"]: exported.erase(key)
		roster.append(exported)
	if "--verify-only" in OS.get_cmdline_user_args():
		var original: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(OUTPUT))
		verify_order_and_scaling(original)
		original["checks"]["reverse_order_cases"] = 56
		original["checks"]["scale_survives_initialization"] = failures.is_empty()
		original["checks"]["failures"] = failures
		var checked_file := FileAccess.open(OUTPUT, FileAccess.WRITE)
		checked_file.store_string(JSON.stringify(original))
		checked_file.close()
		print("BALANCE VERIFY failures=", failures)
		get_tree().quit(0 if failures.is_empty() else 3)
		return
	var rows: Array = []
	var train_means: Dictionary = {}
	for mult in MULTIPLIERS:
		var batch := sample_batch("train", TRAIN_N, float(mult), 824001)
		rows.append_array(batch)
		var mean_score := 0.0
		for row in batch: mean_score += float(row.score)
		mean_score /= float(TRAIN_N)
		train_means[str(mult)] = mean_score
		print("BALANCE train scale=", mult, " score=", mean_score)
		await get_tree().process_frame
	var selected := 1.0
	var best_error := INF
	for mult in MULTIPLIERS:
		var error := absf(float(train_means[str(mult)]) - 0.5)
		if error < best_error:
			selected = float(mult)
			best_error = error
	print("BALANCE selected=", selected, " before opening holdout")
	for mult in [1.0, selected]:
		if mult == 1.0 and rows.any(func(r): return r.split == "test"):
			continue
		rows.append_array(sample_batch("test", TEST_N, mult, 924001))
		print("BALANCE holdout scale=", mult, " complete")
		await get_tree().process_frame
	var sanity := sample_batch("sanity", 8, 1.0, 7411)
	var repeated := sample_batch("sanity", 8, 1.0, 7411)
	if JSON.stringify(sanity) != JSON.stringify(repeated): failures.append("repeat-seed nondeterminism")
	var output := {"engine": Engine.get_version_info(), "level": LEVEL, "roster_seed": ROSTER_SEED, "existing_single_type_compensation": Gojomon.SINGLE_TYPE_MULT_FINAL, "train_n": TRAIN_N, "test_n": TEST_N, "multipliers": MULTIPLIERS, "selected": selected, "roster": roster, "single_count": singles.size(), "dual_count": duals.size(), "training_means": train_means, "rows": rows, "checks": {"deterministic": failures.is_empty(), "failures": failures}, "scope": "One versus one, level 30, no equipment or master. Family and subtype effects enabled. Both side orientations. One seeded style realization per species; multipliers are relative to current stats, including existing single-type compensation."}
	verify_order_and_scaling(output)
	output["checks"]["reverse_order_cases"] = 56
	output["checks"]["scale_survives_initialization"] = failures.is_empty()
	var f := FileAccess.open(OUTPUT, FileAccess.WRITE)
	f.store_string(JSON.stringify(output))
	f.close()
	print("BALANCE DONE rows=", rows.size(), " failures=", failures)
	get_tree().quit(0 if failures.is_empty() else 3)

func verify_order_and_scaling(original: Dictionary) -> void:
	# Replay the first eight training scenarios under every scale, in the reverse
	# order from the experiment. Compare against the saved forward-order results.
	var reverse: Array = MULTIPLIERS.duplicate()
	reverse.reverse()
	for mult in reverse:
		var replay := sample_batch("train", 8, float(mult), 824001)
		var saved: Array = Array(original.rows).filter(func(r): return r.split == "train" and float(r.scale) == float(mult) and int(r.case) < 8)
		if JSON.stringify(JSON.parse_string(JSON.stringify(replay))) != JSON.stringify(JSON.parse_string(JSON.stringify(saved))):
			failures.append("order-dependent result for scale " + str(mult))
	# Verify the experimental factor reaches the state used by the resolver.
	for mult in [0.8, 1.4]:
		var unit: Dictionary = templates["catra"].duplicate(true)
		var fields := ["hp", "max_hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]
		for key in fields: unit[key] = maxi(1, int(round(float(unit[key]) * float(mult))))
		var bs := BattleState.new()
		bs.rng = RandomNumberGenerator.new()
		bs.rng.seed = 171
		bs.party = BattleSimulator._clone_roster([unit])
		bs.enemy = BattleSimulator._clone_roster([templates["fishdel"]])
		BattleSimulator._snapshot_battle_types(bs.party)
		BattleSimulator._snapshot_battle_types(bs.enemy)
		bs.p_active = [0]
		bs.e_active = [0]
		GameState.data = {"relics": {}, "party": [], "enemy": [], "master": ""}
		CombatResolver.pre_turn(bs, CombatResolver.load_effects())
		for key in fields:
			if bs.party[0][key] != unit[key]: failures.append("initialization overwrote " + key)

func sample_batch(split: String, n: int, mult: float, batch_seed: int) -> Array:
	var sampler := RandomNumberGenerator.new()
	sampler.seed = batch_seed
	var rows: Array = []
	for i in range(n):
		var a: String = singles[sampler.randi_range(0, singles.size() - 1)]
		var b: String = duals[sampler.randi_range(0, duals.size() - 1)]
		var battle_seed := int(sampler.randi())
		var single: Dictionary = templates[a].duplicate(true)
		var dual: Dictionary = templates[b].duplicate(true)
		for key in ["hp", "max_hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]:
			single[key] = maxi(1, int(round(float(single[key]) * mult)))
		var before := JSON.stringify([single, dual])
		var x := battle(single, dual, battle_seed)
		var y := battle(dual, single, battle_seed)
		if before != JSON.stringify([single, dual]): failures.append("input mutation at " + str(i))
		var vx := String(x.victor)
		var vy := String(y.victor)
		var score := (score_for(vx, "p") + score_for(vy, "e")) / 2.0
		rows.append({"split": split, "case": i, "scale": mult, "single": a, "dual": b, "seed": battle_seed, "first": vx, "second": vy, "score": score, "turns": [x.turns, y.turns], "timeouts": int(vx == "timeout") + int(vy == "timeout"), "draws": int(vx == "draw") + int(vy == "draw")})
	return rows

func battle(a: Dictionary, b: Dictionary, battle_seed: int) -> Dictionary:
	GameState.data = {"relics": {}, "party": [], "enemy": [], "master": ""}
	var r := BattleSimulator.simulate([a], [b], {"seed": battle_seed, "battle_type": "1v1", "apply_effects": true, "diag": true, "max_turns": 80, "weather": "Clear"})
	if Dictionary(r.get("diag", {})).get("effects_seen", {}).is_empty():
		failures.append("empty effects diagnostic")
	return r

func score_for(victor: String, side: String) -> float:
	if victor == side: return 1.0
	if victor in ["draw", "timeout"]: return 0.5
	return 0.0

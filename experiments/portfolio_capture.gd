extends Node

func _ready() -> void:
	GameState.set_field("_playtest_session", true)
	call_deferred("run")

func run() -> void:
	var receipt: Dictionary = PlaytestScenarios.prepare("battle_2v2_ui")
	GameState.set_field("_playtest_session", true)
	var battle: Node = load(String(receipt.target)).instantiate()
	battle.set("battle_start_pause_sec", 0.5)
	add_child(battle)
	for tick in range(24):
		await get_tree().create_timer(1.0).timeout
		if tick in [2, 5, 9, 15, 21]:
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png("res://portfolio_battle_%02d.png" % tick)
	print("PORTFOLIO_CAPTURE complete")
	get_tree().quit()

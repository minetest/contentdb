import user_agents


def test_minetest_is_not_bot():
	assert not user_agents.parse("Minetest/5.5.1 (Linux/4.14.193+-ab49821 aarch64)").is_bot

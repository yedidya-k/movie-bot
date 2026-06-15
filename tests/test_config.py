from config import Config


def test_config_loads_all_required(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'DOWNLOAD_PATH=./downloads/\n'
        'BRIDGE_BOTS=@vid,@MoviesBot\n'
        'API_ID=12345\n'
        'API_HASH=abc123def456\n'
        'PHONE_NUMBER=+972501234567\n'
    )
    cfg = Config(str(env_file))
    assert cfg.download_path == "./downloads/"
    assert cfg.bridge_bots == ["@vid", "@MoviesBot"]
    assert cfg.api_id == 12345
    assert cfg.api_hash == "abc123def456"
    assert cfg.phone_number == "+972501234567"


def test_config_defaults(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text('')
    cfg = Config(str(env_file))
    assert cfg.download_path == "./downloads/"
    assert cfg.bridge_bots == []
    assert cfg.api_id is None
    assert cfg.api_hash == ""
    assert cfg.phone_number == ""


def test_config_with_bots_only(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        'BRIDGE_BOTS=@vid\n'
        'API_ID=12345\n'
        'API_HASH=abc\n'
        'PHONE_NUMBER=+123\n'
    )
    cfg = Config(str(env_file))
    assert cfg.bridge_bots == ["@vid"]

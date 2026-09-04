from ratvision.release_config import ReleaseConfig


def test_release_config_uses_public_repository_when_environment_absent(monkeypatch):
    monkeypatch.delenv('RATVISION_GITHUB_REPOSITORY', raising=False)
    cfg=ReleaseConfig.from_environment()
    assert cfg.configured is True
    assert cfg.repository == 'atikhobaev/rat-vision'


def test_release_config_treats_placeholder_as_unconfigured():
    assert ReleaseConfig('OWNER/rat-vision').configured is False


def test_release_config_accepts_environment_override(monkeypatch):
    monkeypatch.setenv('RATVISION_GITHUB_REPOSITORY','example/rat-vision')
    cfg=ReleaseConfig.from_environment()
    assert cfg.configured is True
    assert cfg.repository == 'example/rat-vision'


def test_release_config_reads_embedded_build_config_when_environment_absent(monkeypatch, tmp_path):
    import ratvision.release_config as module
    monkeypatch.delenv('RATVISION_GITHUB_REPOSITORY',raising=False)
    monkeypatch.setattr(module,'load_build_config',lambda:{'github_repository':'embedded/rat-vision'})
    assert module.ReleaseConfig.from_environment().repository == 'embedded/rat-vision'

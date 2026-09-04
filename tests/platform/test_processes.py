import psutil

from ratvision.platform.processes import ProcessDiscovery


class FakeProc:
    def __init__(self, info=None, exc=None):
        self._info = info or {}
        self._exc = exc

    @property
    def info(self):
        if self._exc:
            raise self._exc
        return self._info


def test_process_discovery_skips_inaccessible_processes():
    rows = [
        FakeProc({"pid": 10, "name": "HuntGame.exe", "exe": r"C:\\Games\\HuntGame.exe"}),
        FakeProc(exc=psutil.AccessDenied(11)),
        FakeProc({"pid": 12, "name": "Discord.exe", "exe": None}),
    ]
    discovery = ProcessDiscovery(process_iter=lambda: iter(rows))
    found = discovery.list_running()
    assert [item.executable for item in found] == ["huntgame.exe", "discord.exe"]
    assert found[0].friendly_name == "HuntGame"


def test_process_discovery_deduplicates_executable_names():
    rows = [
        FakeProc({"pid": 1, "name": "game.exe", "exe": "/a/game.exe"}),
        FakeProc({"pid": 2, "name": "GAME.EXE", "exe": "/b/GAME.EXE"}),
    ]
    found = ProcessDiscovery(process_iter=lambda: iter(rows)).list_running()
    assert len(found) == 1

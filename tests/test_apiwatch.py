import asyncio
import io
import yaml
import pytest
from unittest import mock

import apiwatch.apiwatch as aw


def test_list_command_outputs_apis(tmp_path, capsys):
	cfg = {
		"apis": [
			{"name": "Local", "url": "http://example.local"},
			{"name": "Remote", "url": "http://example.remote"},
		]
	}
	p = tmp_path / "cfg.yaml"
	p.write_text(yaml.safe_dump(cfg))

	# call the list function which prints to console
	aw.app.commands["list"].callback(str(p))

	captured = capsys.readouterr()
	assert "Local" in captured.out
	assert "Remote" in captured.out


@pytest.mark.asyncio
async def test_check_api_success_and_failure(monkeypatch):
	# create a fake session with get/post methods
	class FakeResp:
		def __init__(self, status=200):
			self.status = status

		async def __aenter__(self):
			return self

		async def __aexit__(self, exc_type, exc, tb):
			return False

	class FakeSession:
		def __init__(self, responses):
			self._responses = responses

		def get(self, url, timeout=None):
			# pop next response
			status = self._responses.pop(0)
			return FakeResp(status=status)

		async def post(self, *args, **kwargs):
			return None

	# two apis: one healthy (200), one failing (simulate exception by returning None status)
	apis = [{"name": "good", "url": "http://good"}, {"name": "bad", "url": "http://bad"}]

	async def fake_run_checks(config_path):
		# mimic run_checks internals minimally for unit test
		session = FakeSession([200, 500])
		tasks = [aw.check_api(session, api) for api in apis]
		results = await asyncio.gather(*tasks)
		return results

	results = await fake_run_checks(None)
	assert results[0][1] == 200
	assert results[1][1] == 500

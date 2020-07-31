"""Test the Settings service API.
"""

import pytest
import json
import tornado

from strict_rfc3339 import rfc3339_to_timestamp

from .utils import expected_http_error
from .utils import maybe_patch_ioloop, big_unicode_string

async def test_get(fetch, labserverapp):
    id = '@jupyterlab/apputils-extension:themes'
    r = await fetch('lab', 'api', 'settings', id)
    assert r.code == 200
    res = r.body.decode()
    data = json.loads(res)
    assert data['id'] == id
    schema = data['schema']
    # Check that overrides.json file is respected.
    assert schema['properties']['theme']['default'] == 'JupyterLab Dark'
    assert 'raw' in res

async def test_get_bad(fetch, labserverapp):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await fetch('foo')
    assert expected_http_error(e, 404)

async def test_listing(fetch, labserverapp):
    ids = [
        '@jupyterlab/apputils-extension:themes',
        '@jupyterlab/codemirror-extension:commands',
        '@jupyterlab/shortcuts-extension:plugin',
        '@jupyterlab/shortcuts-extension:plugin',
        '@jupyterlab/translation-extension:plugin',
    ]
    versions = ['N/A', 'N/A', 'test-version']
    r = await fetch('lab', 'api', 'settings')
    assert r.code == 200
    res = r.body.decode()
    response = json.loads(res)
    response_ids = [item['id'] for item in response['settings']]
    response_versions = [item['version'] for item in response['settings']]
    assert set(response_ids) == set(ids)
    assert set(response_versions) == set(versions)
    last_modifieds = [item['last_modified'] for item in response['settings']]
    createds = [item['created'] for item in response['settings']]
    assert {None} == set(last_modifieds + createds)


async def test_patch(fetch, labserverapp):
    id = '@jupyterlab/shortcuts-extension:plugin'
    r = await fetch('lab', 'api', 'settings', id, 
        method='PUT',
        body=json.dumps({})
        )
    assert r.code == 204
    data = self.settings_api.get(id).json()
    first_created = rfc3339_to_timestamp(data['created'])
    first_modified = rfc3339_to_timestamp(data['last_modified'])
    
    assert self.settings_api.put(id, dict()).status_code == 204
    data = self.settings_api.get(id).json()
    second_created = rfc3339_to_timestamp(data['created'])
    second_modified = rfc3339_to_timestamp(data['last_modified'])

    assert first_created <= second_created
    assert first_modified < second_modified
    
    listing = self.settings_api.get('').json()['settings']
    list_data = [item for item in listing if item['id'] == id][0]
    assert list_data['created'] == data['created']
    assert list_data['last_modified'] == data['last_modified']


async def test_patch_unicode(self):
    id = '@jupyterlab/unicode-extension:plugin'
    assert self.settings_api.put(id, dict(comment=big_unicode_string[::-1])).status_code == 204
    data = self.settings_api.get(id).json()
    assert data["settings"]["comment"] == big_unicode_string[::-1]

async def test_patch_wrong_id(fetch, labserverapp):
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await fetch('foo',
            method='PUT',
            body=json.dumps({})
        )
    assert expected_http_error(e, 404)

async def test_patch_bad_data(fetch, labserverapp):
    id = '@jupyterlab/codemirror-extension:commands'
    with pytest.raises(tornado.httpclient.HTTPClientError) as e:
        await fetch('foo',
            method='PUT',
            body=json.dumps({'keyMap': 10})
        )
    assert expected_http_error(e, 404)

import pytest

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories
from flask import Flask

from ckanext.sfb_layout.lib import Helper
from ckanext.sfb_layout.plugin import SfbLayoutPlugin


@pytest.mark.ckan_config('ckan.plugins', 'sfb_layout')
def test_plugin_loads(with_plugins):
    assert plugins.plugin_loaded('sfb_layout')


def test_blueprint_registers_json_export_route():
    blueprint = SfbLayoutPlugin().get_blueprint()
    flask_app = Flask(__name__)
    flask_app.register_blueprint(blueprint)
    rules = {rule.rule for rule in flask_app.url_map.iter_rules()}

    assert '/sfb_layout/get_json/<dataset_name>' in rules


@pytest.mark.parametrize(
    ('configured_plugins', 'expected'),
    [
        ('sfb_layout user_manual', True),
        (['sfb_layout', 'user_manual'], True),
        ('sfb_layout user_manual_extra', False),
    ],
)
def test_plugin_detection_supports_string_and_list_config(monkeypatch, configured_plugins, expected):
    monkeypatch.setitem(toolkit.config, 'ckan.plugins', configured_plugins)

    assert Helper.check_plugin_enabled('user_manual') is expected


def test_stage_count_uses_exact_plugin_names(monkeypatch):
    monkeypatch.setitem(
        toolkit.config,
        'ckan.plugins',
        ['sfb_layout', 'resource_custom_metadata', 'organization_group', 'sample_link_extra'],
    )

    assert Helper.stages_count() == 2


@pytest.mark.parametrize('project_id', ['1153', '1368'])
def test_project_id_config_selects_layout(monkeypatch, project_id):
    monkeypatch.setitem(toolkit.config, 'ckanext.crc.project.id', project_id)
    monkeypatch.setitem(toolkit.config, 'ckan.root_path', '/unrelated/path')

    assert Helper.which_sfb() == project_id


@pytest.mark.parametrize(
    ('query', 'expected'),
    [
        ('column: temperature:mean', ['temperature:mean', 'column']),
        ('Publication: Smith 2024', ['Smith 2024', 'publication']),
        ('ordinary search', ['ordinary search', '0']),
        (None, ['', '0']),
    ],
)
def test_search_query_preparation(query, expected):
    assert Helper.search_query_prepration(query) == expected


def test_export_url_handles_language_root_without_duplicate_slashes(monkeypatch):
    monkeypatch.setitem(toolkit.config, 'ckan.site_url', 'https://example.test/')
    monkeypatch.setitem(toolkit.config, 'ckan.root_path', '/portal/{{LANG}}')

    assert Helper.get_export_url('dataset-name', '.ttl') == 'https://example.test/portal/dataset/dataset-name.ttl'


@pytest.mark.ckan_config('ckan.plugins', 'sfb_layout')
def test_missing_json_export_returns_404(app, with_plugins):
    response = app.get('/sfb_layout/get_json/missing-dataset')

    assert response.status_code == 404


@pytest.mark.ckan_config('ckan.plugins', 'sfb_layout')
def test_public_json_export_returns_dataset(clean_db, app, with_plugins):
    dataset = factories.Dataset()

    response = app.get('/sfb_layout/get_json/' + dataset['name'])

    assert response.status_code == 200
    assert response.json['id'] == dataset['id']


@pytest.mark.ckan_config('ckan.plugins', 'sfb_layout')
def test_core_pages_render_with_layout_templates(clean_db, app, with_plugins):
    dataset = factories.Dataset(
        notes='Dataset description',
        resources=[
            {
                'name': 'Example resource',
                'url': 'https://example.test/data.csv',
                'format': 'CSV',
            }
        ],
    )
    resource = dataset['resources'][0]

    assert app.get('/').status_code == 200
    assert app.get('/dataset').status_code == 200
    assert app.get('/dataset/' + dataset['name']).status_code == 200
    response = app.get('/dataset/{}/resource/{}'.format(dataset['name'], resource['id']))

    assert response.status_code == 200
    assert b'data-resource-sfb-table' in response.data
    assert b'Export Dataset Metadata' in app.get('/dataset/' + dataset['name']).data

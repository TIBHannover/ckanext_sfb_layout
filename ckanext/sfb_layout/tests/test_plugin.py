import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.tests import factories
from flask import Flask

from ckanext.sfb_layout.lib import Helper
from ckanext.sfb_layout.plugin import SfbLayoutPlugin
from ckanext.sfb_layout.stats import SystemStats
from ckanext.sfb_layout.system_stats_plugin import SystemStatsPlugin


ASSET_ROOT = Path(__file__).parents[1] / 'public' / 'sfb_layout' / 'statics'
JAVASCRIPT_BUNDLES = {
    'search-js': ['search.js'],
    'sfb1153-js': ['ckan_1153.js'],
    'sfb1368-js': ['ckan_1368.js'],
    'stages-js': ['stages.js'],
}


def test_javascript_bundle_definitions_have_local_contents_and_no_jquery_ui():
    bundles = yaml.safe_load((ASSET_ROOT / 'webassets.yml').read_text())

    for name, contents in JAVASCRIPT_BUNDLES.items():
        assert bundles[name]['contents'] == contents
        assert 'vendor/jquery.ui.core' not in bundles[name]['extra']['preload']
        assert all((ASSET_ROOT / filename).is_file() for filename in contents)


@pytest.mark.ckan_config('ckan.plugins', 'sfb_layout')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.parametrize('bundle_name', JAVASCRIPT_BUNDLES)
def test_javascript_bundles_include_without_unknown_assets(app, caplog, bundle_name):
    from ckan.lib.webassets_tools import include_asset

    caplog.set_level(logging.ERROR, logger='ckan.lib.webassets_tools')

    with app.flask_app.test_request_context('/'):
        include_asset('ckanext-sfb-layout/' + bundle_name)

    assert 'Trying to include unknown asset' not in caplog.text


@pytest.mark.parametrize('stylesheet', ['ckan_1153_style.css', 'ckan_style.css'])
def test_project_stylesheets_use_full_width_layout(stylesheet):
    statics = Path(__file__).parents[1] / 'public' / 'sfb_layout' / 'statics'

    css = (statics / stylesheet).read_text()

    assert '.main > #content.container {' in css
    assert 'max-width: 100%;' in css


@pytest.mark.ckan_config('ckan.plugins', 'sfb_layout')
def test_plugin_loads(with_plugins):
    assert plugins.plugin_loaded('sfb_layout')


def test_plugin_registers_site_logo_helper():
    helpers = SfbLayoutPlugin().get_helpers()

    assert helpers['sfb_site_logo_url'] is Helper.site_logo_url


@pytest.mark.parametrize(
    ('root_path', 'site_logo', 'expected'),
    [
        ('/sfb1368/{{LANG}}', '/base/images/logo.png',
         '/sfb1368/base/images/logo.png'),
        ('/sfb1153/{{LANG}}', 'base/images/logo.png',
         '/sfb1153/base/images/logo.png'),
        ('', '/base/images/logo.png', '/base/images/logo.png'),
        ('/sfb1368/{{LANG}}', '/sfb1368/base/images/logo.png',
         '/sfb1368/base/images/logo.png'),
        ('/sfb1368/{{LANG}}', 'https://example.test/logo.png',
         'https://example.test/logo.png'),
    ],
)
def test_site_logo_url_respects_deployment_prefix(
    monkeypatch, root_path, site_logo, expected
):
    monkeypatch.setitem(toolkit.config, 'ckan.root_path', root_path)

    assert Helper.site_logo_url(site_logo) == expected


def test_blueprint_registers_json_export_route():
    blueprint = SfbLayoutPlugin().get_blueprint()
    flask_app = Flask(__name__)
    flask_app.register_blueprint(blueprint)
    rules = {rule.rule for rule in flask_app.url_map.iter_rules()}

    assert '/sfb_layout/get_json/<dataset_name>' in rules


def test_system_stats_blueprint_registers_admin_route():
    blueprint = SystemStatsPlugin().get_blueprint()
    flask_app = Flask(__name__)
    flask_app.register_blueprint(blueprint)
    rules = {rule.rule for rule in flask_app.url_map.iter_rules()}

    assert '/system_stats/stats_page' in rules


@pytest.mark.ckan_config('ckan.plugins', 'system_stats')
def test_system_stats_plugin_loads_separately(with_plugins):
    assert plugins.plugin_loaded('system_stats')


@pytest.mark.ckan_config('ckan.plugins', 'sfb_layout system_stats')
@pytest.mark.ckan_config('ckanext.crc.project.id', '1368')
def test_system_stats_rejects_non_sysadmins(app, with_plugins):
    response = app.get('/system_stats/stats_page')

    assert response.status_code == 403


@pytest.mark.ckan_config('ckan.plugins', 'sfb_layout system_stats')
@pytest.mark.ckan_config('ckanext.crc.project.id', '1153')
def test_system_stats_is_not_available_for_sfb_1153(app, with_plugins):
    response = app.get('/system_stats/stats_page')

    assert response.status_code == 404


@pytest.mark.ckan_config('ckan.plugins', 'sfb_layout system_stats')
@pytest.mark.ckan_config('ckanext.crc.project.id', '1368')
def test_system_stats_page_and_core_calculations(clean_db, app, with_plugins):
    sysadmin = factories.Sysadmin()
    token = factories.APIToken(user=sysadmin['id'])['token']
    factories.User()
    organization = factories.Organization(title='Test organization')
    factories.Dataset(
        user=sysadmin,
        owner_org=organization['id'],
        title='Statistics dataset',
        resources=[
            {
                'url': 'https://example.test/data.csv',
                'format': 'CSV',
            }
        ],
    )

    response = app.get(
        '/system_stats/stats_page',
        headers={'Authorization': token},
    )

    assert response.status_code == 200
    assert b'Overall stats' in response.data
    assert b'Test organization: 1' in response.data
    assert b'csv: 1' in response.data
    assert SystemStats.get_dataset_count() == 1
    assert SystemStats.get_user_count() == 1


def test_optional_statistics_are_empty_when_plugins_are_disabled(monkeypatch):
    monkeypatch.setitem(toolkit.config, 'ckan.plugins', 'sfb_layout system_stats')

    assert SystemStats.get_linked_machines_count([]) == (0, 0)
    assert SystemStats.get_linked_samples_count([]) == (0, 0)
    assert SystemStats.get_linked_publications_count([]) == 0
    assert SystemStats.get_dataset_with_publication([]) == []
    assert SystemStats.get_dataset_with_machines([]) == []
    assert SystemStats.get_dataset_with_samples([]) == []
    assert SystemStats.get_dataset_with_publication_per_group([]) == {}


def test_machine_and_sample_statistics_count_resources_and_datasets(monkeypatch):
    resources = [
        SimpleNamespace(id='linked', state='active'),
        SimpleNamespace(id='unlinked', state='active'),
        SimpleNamespace(id='inactive', state='deleted'),
    ]
    datasets = [
        SimpleNamespace(title='Linked dataset', resources=resources),
        SimpleNamespace(
            title='Unlinked dataset',
            resources=[SimpleNamespace(id='unlinked', state='active')],
        ),
    ]
    monkeypatch.setattr(
        Helper,
        'check_plugin_enabled',
        lambda name: name in {'machine_link', 'sample_link'},
    )
    monkeypatch.setattr(
        SystemStats,
        '_machine_links',
        lambda resource_id: {'machine': 'url'} if resource_id == 'linked' else {},
    )
    monkeypatch.setattr(
        SystemStats,
        '_sample_links',
        lambda resource_id: {'sample': 'url'} if resource_id == 'linked' else {},
    )

    assert SystemStats.get_linked_machines_count(datasets) == (1, 1)
    assert SystemStats.get_linked_samples_count(datasets) == (1, 1)
    assert SystemStats.get_dataset_with_machines(datasets) == ['Linked dataset']
    assert SystemStats.get_dataset_with_samples(datasets) == ['Linked dataset']


def test_publication_statistics_include_linked_datasets_and_groups(monkeypatch):
    group = SimpleNamespace(
        title='Research group',
        state='active',
        is_organization=False,
    )
    datasets = [
        SimpleNamespace(
            name='linked',
            title='Linked dataset',
            get_groups=lambda: [group],
        ),
        SimpleNamespace(
            name='unlinked',
            title='Unlinked dataset',
            get_groups=lambda: [group],
        ),
    ]
    monkeypatch.setattr(
        Helper,
        'check_plugin_enabled',
        lambda name: name == 'dataset_reference',
    )
    monkeypatch.setattr(
        SystemStats,
        '_publication_links',
        lambda dataset: [object()] if dataset.name == 'linked' else [],
    )

    assert SystemStats.get_linked_publications_count(datasets) == 1
    assert SystemStats.get_dataset_with_publication(datasets) == [
        'Linked dataset'
    ]
    assert SystemStats.get_dataset_with_publication_per_group(datasets) == {
        'Research group': ['Linked dataset']
    }


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


@pytest.mark.parametrize(
    ('configured_plugins', 'expected'),
    [
        (['sfb_layout', 'resource_custom_metadata', 'organization_group', 'sample_link_extra'], 2),
        ('sfb_layout resource_custom_metadata machine_link sample_link_extra', 2),
        ([], 0),
    ],
)
def test_stage_count_uses_exact_plugin_names(monkeypatch, configured_plugins, expected):
    monkeypatch.setitem(toolkit.config, 'ckan.plugins', configured_plugins)

    assert Helper.stages_count() == expected


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

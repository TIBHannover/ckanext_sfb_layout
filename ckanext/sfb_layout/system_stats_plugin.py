import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from flask import Blueprint

from ckanext.sfb_layout.lib import Helper
from ckanext.sfb_layout.stats import SystemStats


class SystemStatsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'stats_templates')

    def get_blueprint(self):
        blueprint = Blueprint('system_stats', self.__module__)
        blueprint.add_url_rule(
            '/system_stats/stats_page',
            'stats_page',
            SystemStats.index,
            methods=['GET'],
        )
        return blueprint

    def get_helpers(self):
        return {
            'system_stats_is_sfb_1368': lambda: Helper.which_sfb() == '1368',
        }

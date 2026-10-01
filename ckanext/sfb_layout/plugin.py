import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.sfb_layout.lib import Helper
from flask import Blueprint


class SfbLayoutPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public/sfb_layout')
        toolkit.add_resource('public/sfb_layout/statics', 'ckanext-sfb-layout')
    

     #plugin Blueprint

    def get_blueprint(self):

        blueprint = Blueprint(self.name, self.__module__)
        blueprint.template_folder = u'templates'

        blueprint.add_url_rule(
            u'/sfb_layout/get_json/<dataset_name>',
            u'get_json',
            Helper.get_json,
            methods=['GET']
            )

        return blueprint
        
    

    def get_helpers(self):
        return {'which_sfb': Helper.which_sfb, 
            'is_enabled': Helper.check_plugin_enabled,
            'stages_count': Helper.stages_count, 
            'set_stages': Helper.set_stages,
            'set_orders': Helper.set_orders,
            'set_titles': Helper.set_titles,
            'query_prepration': Helper.search_query_prepration,
            'is_selection_needed': Helper.is_selection_needed,
            'get_export_url': Helper.get_export_url
        }

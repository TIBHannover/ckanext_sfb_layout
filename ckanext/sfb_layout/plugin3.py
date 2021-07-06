import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from flask import Blueprint
from ckanext.sfb_layout.lib import FeatureImageFunctions


class FeatureImagePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates/feature_image')
        toolkit.add_public_directory(config_, 'public/feature_image')
        toolkit.add_resource('public/feature_image/statics', 'ckanext-sfb-layout-feature-image')
        
    
    def get_blueprint(self):

        blueprint = Blueprint(self.name, self.__module__)        
        blueprint.add_url_rule(
            u'/feature_image/config',
            u'config',
            FeatureImageFunctions.config,
            methods=['GET']
            )   
        
        blueprint.add_url_rule(
            u'/feature_image/save_config',
            u'save_config',
            FeatureImageFunctions.save_config,
            methods=['POST']
            )   

        return blueprint 
    
    
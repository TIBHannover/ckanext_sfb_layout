# encoding: utf-8

import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as h



class Helper():

    @staticmethod
    def which_sfb():
        '''
            Check which sfb server the plugin is runnung in. 
        '''

        project_id = str(toolkit.config.get('ckanext.crc.project.id') or '').strip()
        if project_id in {'1153', '1368'}:
            return project_id

        ckan_root_path = toolkit.config.get('ckan.root_path')
        if  ckan_root_path and 'sfb1368/ckan' in ckan_root_path:
            return '1368'
        elif ckan_root_path and 'sfb1153/ckan' in ckan_root_path:
            return '1153'
        else:
            # localhost
            return '1368'
    

    @staticmethod
    def check_plugin_enabled(plugin_name):
        configured_plugins = toolkit.config.get("ckan.plugins", [])
        if isinstance(configured_plugins, str):
            configured_plugins = configured_plugins.split()
        return plugin_name in configured_plugins
    

    @staticmethod
    def stages_count():
        plugins_with_stages = ['resource_custom_metadata', 'organization_group', 'machine_link', 'sample_link']
        enabled_plugins = toolkit.config.get("ckan.plugins")
        count = 0
        for pl in plugins_with_stages:
            if pl in enabled_plugins:
                count += 1
        
        return count


    @staticmethod
    def set_stages():
        stages= []
        if Helper.which_sfb() == '1368':
            if  'dataset/new' in  h.full_current_url():
                stages = ['active', 'uncomplete','uncomplete', 'uncomplete', 'uncomplete']
            
            elif 'resource/new' in h.full_current_url():
                stages = ['complete', 'active','uncomplete', 'uncomplete', 'uncomplete']
            
            elif 'resource_custom_metadata/index' in h.full_current_url():
                stages = ['complete', 'complete','active', 'uncomplete', 'uncomplete']
            
            elif 'upgrade_dataset/add_ownership_view' in h.full_current_url():
                stages = ['complete', 'complete','complete', 'active', 'uncomplete']
            
            elif 'smw/machines_view' in h.full_current_url():
                stages = ['complete', 'complete','complete', 'complete', 'active']
        
        else:
            # 1153
            if  'dataset/new' in  h.full_current_url():
                stages = ['active', 'uncomplete','uncomplete', 'uncomplete', 'uncomplete']
            
            elif 'resource/new' in h.full_current_url():
                stages = ['complete', 'active','uncomplete', 'uncomplete', 'uncomplete']
                        
            elif 'upgrade_dataset/add_ownership_view' in h.full_current_url():
                stages = ['complete', 'complete','active', 'uncomplete', 'uncomplete']
            
            elif 'smw/machines_view' in h.full_current_url():
                stages = ['complete', 'complete','complete', 'active', 'uncomplete']
            
            elif '/smw/add_samples_view' in h.full_current_url():
                stages = ['complete', 'complete','complete', 'complete', 'active']
        
        return stages


    @staticmethod
    def set_orders():
        if Helper.which_sfb() == '1368':
            return ['second', 'third', 'forth']
        else:
            return ['second', 'third', 'forth']
    


    @staticmethod
    def set_titles():
        if Helper.which_sfb() == '1368':
            return ['Add data', 'Metadata', 'Ownership', 'Equipment(s)'] 
        else:
            return ['Add data', 'Ownership', 'Equipment(s)', 'Sample(s)'] 



    @staticmethod
    def search_query_prepration(query):
        search_types = {
            'sample',
            'column',
            'material_combination',
            'surface_preparation',
            'atmosphere',
            'data_type',
            'analysis_method',
            'publication',
        }
        prefix, separator, value = (query or '').partition(':')
        prefix = prefix.strip().lower()
        if separator and prefix in search_types:
            return [value.strip(), prefix]
        return [query or '', '0']
    


    @staticmethod
    def is_selection_needed(form_id):
        if form_id in ["organization-search-form", "group-search-form"]:
            return False
        return True
    

    @staticmethod
    def get_export_url(dataset_name, export_format):
        base_url = (toolkit.config.get('ckan.site_url') or '').rstrip('/')
        root_path = (toolkit.config.get('ckan.root_path') or '').split('{{LANG}}')[0].strip('/')
        path_parts = [part for part in (root_path, 'dataset', dataset_name + export_format) if part]
        return base_url + '/' + '/'.join(path_parts)


   
    @staticmethod
    def get_json(dataset_name):
        context = {
            'user': toolkit.g.user,
            'auth_user_obj': toolkit.g.userobj,
        }
        try:
            return toolkit.get_action('package_show')(context, {'id': dataset_name})
        except toolkit.ObjectNotFound:
            return toolkit.abort(404, toolkit._('Dataset not found'))
        except toolkit.NotAuthorized:
            return toolkit.abort(403, toolkit._('Not authorized to see this dataset'))

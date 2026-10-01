import ckan.model as model
import ckan.plugins.toolkit as toolkit

from ckanext.sfb_layout.lib import Helper


class SystemStats:
    @staticmethod
    def index():
        if Helper.which_sfb() != '1368':
            return toolkit.abort(404, toolkit._('Page not found'))

        context = {
            'model': model,
            'user': toolkit.g.user,
            'auth_user_obj': toolkit.g.userobj,
        }
        try:
            toolkit.check_access('sysadmin', context, {})
        except toolkit.NotAuthorized:
            return toolkit.abort(
                403,
                toolkit._('Need to be system administrator to administer'),
            )

        datasets = SystemStats.get_active_datasets()
        organization_count, group_count = SystemStats.get_org_group_count()
        machine_resource_count, machine_dataset_count = (
            SystemStats.get_linked_machines_count(datasets)
        )
        sample_resource_count, sample_dataset_count = (
            SystemStats.get_linked_samples_count(datasets)
        )

        result = {
            'Number of Datasets': len(datasets),
            'Number of Organizations': organization_count,
            'Number of Groups': group_count,
            'Number of Users': SystemStats.get_user_count(),
            'Number of machines resource': machine_resource_count,
            'Number of machines dataset': machine_dataset_count,
            'Number of samples resource': sample_resource_count,
            'Number of samples dataset': sample_dataset_count,
            'Number of datasets linked to publication': (
                SystemStats.get_linked_publications_count(datasets)
            ),
            'dataset_per_org': SystemStats.get_dataset_per_org(datasets),
            'dataset_per_group': SystemStats.get_dataset_per_group(datasets),
            'resource_per_type': SystemStats.get_resources_by_type(datasets),
            'datasets_with_publication': (
                SystemStats.get_dataset_with_publication(datasets)
            ),
            'datasets_with_machines': (
                SystemStats.get_dataset_with_machines(datasets)
            ),
            'datasets_with_samples': (
                SystemStats.get_dataset_with_samples(datasets)
            ),
            'datasets_with_annotaion': (
                SystemStats.get_datasets_with_extra_annotaion(datasets)
            ),
            'group_with_datasets_with_publication': (
                SystemStats.get_dataset_with_publication_per_group(datasets)
            ),
        }
        return toolkit.render('stats_page.html', extra_vars={'result': result})

    @staticmethod
    def get_active_datasets():
        return (
            model.Session.query(model.Package)
            .filter(model.Package.state == 'active')
            .all()
        )

    @staticmethod
    def get_dataset_count():
        return len(SystemStats.get_active_datasets())

    @staticmethod
    def _datasets(datasets):
        if datasets is None:
            return SystemStats.get_active_datasets()
        return datasets

    @staticmethod
    def get_org_group_count():
        organizations = 0
        groups = 0
        for group in model.Group.all():
            if group.state != 'active':
                continue
            if group.is_organization:
                organizations += 1
            else:
                groups += 1
        return organizations, groups

    @staticmethod
    def get_user_count():
        return sum(
            user.state == 'active' and not user.sysadmin
            for user in model.User.all()
        )

    @staticmethod
    def get_linked_machines_count(datasets=None):
        if not Helper.check_plugin_enabled('machine_link'):
            return 0, 0

        resource_count = 0
        dataset_count = 0
        for dataset in SystemStats._datasets(datasets):
            dataset_has_link = False
            for resource in dataset.resources:
                if resource.state != 'active':
                    continue
                if SystemStats._machine_links(resource.id):
                    resource_count += 1
                    dataset_has_link = True
            dataset_count += dataset_has_link
        return resource_count, dataset_count

    @staticmethod
    def get_linked_samples_count(datasets=None):
        if not Helper.check_plugin_enabled('sample_link'):
            return 0, 0

        resource_count = 0
        dataset_count = 0
        for dataset in SystemStats._datasets(datasets):
            dataset_has_link = False
            for resource in dataset.resources:
                if resource.state != 'active':
                    continue
                if SystemStats._sample_links(resource.id):
                    resource_count += 1
                    dataset_has_link = True
            dataset_count += dataset_has_link
        return resource_count, dataset_count

    @staticmethod
    def _machine_links(resource_id):
        from ckanext.semantic_media_wiki.libs.media_wiki import Helper as MachineHelper

        return MachineHelper.get_machine_link(resource_id)

    @staticmethod
    def _sample_links(resource_id):
        from ckanext.semantic_media_wiki.libs.sample_link import SampleLinkHelper

        return SampleLinkHelper.get_sample_link(resource_id)

    @staticmethod
    def _publication_links(dataset):
        if not Helper.check_plugin_enabled('dataset_reference'):
            return []

        from sqlalchemy.sql.expression import false

        from ckanext.dataset_reference.models.package_reference_link import (
            PackageReferenceLink,
        )

        links = PackageReferenceLink({}).get_by_package(name=dataset.name)
        if links is false or not links:
            return []
        return links

    @staticmethod
    def get_linked_publications_count(datasets=None):
        if not Helper.check_plugin_enabled('dataset_reference'):
            return 0
        return sum(
            bool(SystemStats._publication_links(dataset))
            for dataset in SystemStats._datasets(datasets)
        )

    @staticmethod
    def get_dataset_per_org(datasets=None):
        result = {}
        for dataset in SystemStats._datasets(datasets):
            organization = (
                model.Group.get(dataset.owner_org) if dataset.owner_org else None
            )
            if not organization or organization.state != 'active':
                continue
            result[organization.title] = result.get(organization.title, 0) + 1
        return result

    @staticmethod
    def get_dataset_per_group(datasets=None):
        result = {}
        for dataset in SystemStats._datasets(datasets):
            for group in dataset.get_groups():
                if group.state == 'active' and not group.is_organization:
                    result[group.title] = result.get(group.title, 0) + 1
        return result

    @staticmethod
    def get_resources_by_type(datasets=None):
        result = {}
        for dataset in SystemStats._datasets(datasets):
            for resource in dataset.resources:
                if resource.state != 'active' or not resource.format:
                    continue
                resource_format = resource.format.lower()
                result[resource_format] = result.get(resource_format, 0) + 1
        return result

    @staticmethod
    def get_dataset_with_publication(datasets=None):
        if not Helper.check_plugin_enabled('dataset_reference'):
            return []
        return [
            dataset.title
            for dataset in SystemStats._datasets(datasets)
            if SystemStats._publication_links(dataset)
        ]

    @staticmethod
    def get_dataset_with_machines(datasets=None):
        if not Helper.check_plugin_enabled('machine_link'):
            return []

        return [
            dataset.title
            for dataset in SystemStats._datasets(datasets)
            if any(
                resource.state == 'active'
                and SystemStats._machine_links(resource.id)
                for resource in dataset.resources
            )
        ]

    @staticmethod
    def get_dataset_with_samples(datasets=None):
        if not Helper.check_plugin_enabled('sample_link'):
            return []

        return [
            dataset.title
            for dataset in SystemStats._datasets(datasets)
            if any(
                resource.state == 'active'
                and SystemStats._sample_links(resource.id)
                for resource in dataset.resources
            )
        ]

    @staticmethod
    def get_datasets_with_extra_annotaion(datasets=None):
        result = []
        for dataset in SystemStats._datasets(datasets):
            extras = (dataset.as_dict().get('extras') or {})
            if not extras or set(extras) == {'sfb_dataset_type'}:
                continue
            result.append(dataset.title)
        return result

    @staticmethod
    def get_dataset_with_publication_per_group(datasets=None):
        if not Helper.check_plugin_enabled('dataset_reference'):
            return {}

        result = {}
        for dataset in SystemStats._datasets(datasets):
            if not SystemStats._publication_links(dataset):
                continue
            for group in dataset.get_groups():
                if group.state == 'active' and not group.is_organization:
                    result.setdefault(group.title, []).append(dataset.title)
        return result

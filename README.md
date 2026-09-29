# ckanext-sfb-layout

This extension applies the shared SFB 1153/1368 presentation layer to CKAN.
It adds project-specific assets, guided dataset-creation stages, advanced
search controls, dataset export links, and resource metadata/integration
sections.

## Compatibility

| CKAN version | Status |
| --- | --- |
| 2.11 | Supported and tested with Python 3.10 |
| 2.10 | Supported and tested with Python 3.10 |
| 2.9 and earlier | Not supported |

The package requires Python 3.9 or newer.

## Behavior

- The `sfb_layout` plugin registers templates, static assets, helper functions,
  and the JSON dataset-export route.
- `ckanext.crc.project.id` selects the `1153` or `1368` theme. For older
  deployments, the helper falls back to detecting the project in
  `ckan.root_path`.
- The search form works with `ckanext-sfb-search` prefixes such as `column:`,
  `sample:`, `publication:`, and resource metadata fields.
- Dataset pages provide RDF, JSON, XML, and TTL export links.
- Resource pages can show equipment, samples, custom resource metadata, and
  data-comparison controls when the corresponding plugins are enabled.
- If `user_manual` is enabled, the main navigation includes its Help page.

The templates extend CKAN core templates and override only SFB-specific blocks.
This keeps authentication, logout CSRF protection, accessibility, Bootstrap
markup, resource previews, and route names aligned with CKAN 2.10 and 2.11.

## Installation

1. Activate the CKAN virtual environment.
2. Clone and install the extension:

       git clone https://github.com/TIBHannover/ckanext_sfb_layout.git
       cd ckanext_sfb_layout
       pip install -r requirements.txt
       pip install -e .

3. Add the plugin to `ckan.plugins`:

       ckan.plugins = ... sfb_layout

4. Configure the project where possible:

       ckanext.crc.project.id = 1368

   Use `1153` for SFB 1153.

5. Restart CKAN.

## Tests

Install `dev-requirements.txt`, then run:

    pytest --ckan-ini=test.ini --cov=ckanext.sfb_layout ckanext/sfb_layout

The GitHub Actions matrix and `docker-compose.ci.yml` run the functional suite
against CKAN 2.10 and 2.11.

## License

[AGPL](LICENSE)

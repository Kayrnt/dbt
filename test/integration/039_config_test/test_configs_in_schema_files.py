import os
import shutil

from test.integration.base import DBTIntegrationTest, use_profile, get_manifest
from dbt.exceptions import CompilationException


class TestSchemaFileConfigs(DBTIntegrationTest):
    @property
    def schema(self):
        return "config_039-alt"

    def unique_schema(self):
        return super().unique_schema().upper()

    @property
    def project_config(self):
        return {
            'config-version': 2,
            'data-paths': ['data-alt'],
            'models': {
                '+meta': {
                    'company': 'NuMade',
                },
                'test': {
                    '+meta': {
                        'project': 'test',
                    },
                    'tagged': {
                        '+meta': {
                            'team': 'Core Team',
                        },
                        'tags': ['tag_in_project'],
                        'model': {
                            'materialized': 'table',
                            '+meta': {
                                'owner': 'Julie Dent',
                            },
                        }
                    }
                },
            },
            'seeds': {
                'quote_columns': False,
            },
        }

    @property
    def models(self):
        return "models-alt"

    @use_profile('postgres')
    def test_postgres_config_layering(self):
        self.assertEqual(len(self.run_dbt(['seed'])), 1)
        # test the project-level tag, and both config() call tags
        self.assertEqual(len(self.run_dbt(['run', '--model', 'tag:tag_in_project'])), 1)
        self.assertEqual(len(self.run_dbt(['run', '--model', 'tag:tag_1_in_model'])), 1)
        self.assertEqual(len(self.run_dbt(['run', '--model', 'tag:tag_2_in_model'])), 1)
        self.assertEqual(len(self.run_dbt(['run', '--model', 'tag:tag_in_schema'])), 1)
        manifest = get_manifest()
        model_id = 'model.test.model'
        model_node = manifest.nodes[model_id]
        model_tags = ['tag_1_in_model', 'tag_2_in_model', 'tag_in_project', 'tag_in_schema']
        model_node_tags = model_node.tags.copy()
        model_node_tags.sort()
        self.assertEqual(model_node_tags, model_tags)
        model_node_config_tags = model_node.config.tags.copy()
        model_node_config_tags.sort()
        self.assertEqual(model_node_config_tags, model_tags)
        model_meta = {
            'company': 'NuMade',
            'project': 'test',
            'team': 'Core Team',
            'owner': 'Julie Smith',
        }
        self.assertEqual(model_node.config.meta, model_meta)
        # make sure we overwrote the materialization properly
        models = self.get_models_in_schema()
        self.assertEqual(models['model'], 'table')
        self.assertTablesEqual('some_seed', 'model')



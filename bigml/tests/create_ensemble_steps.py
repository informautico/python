# -*- coding: utf-8 -*-
#
# Copyright 2012-2022 BigML
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import time
import json
import os
from datetime import datetime
from .world import world, res_filename
from nose.tools import eq_, assert_less

from bigml.api import HTTP_CREATED
from bigml.api import HTTP_ACCEPTED
from bigml.api import FINISHED
from bigml.api import FAULTY
from bigml.api import get_status
from bigml.ensemble import Ensemble
from bigml.ensemblepredictor import EnsemblePredictor
from bigml.model import Model
from bigml.supervised import SupervisedModel

from .read_resource_steps import wait_until_status_code_is

NO_MISSING_SPLITS = {'missing_splits': False}
ENSEMBLE_SAMPLE = {'seed': 'BigML',
                   'ensemble_sample': {"rate": 0.7, "seed": 'BigML'}}

#@step(r'I create an ensemble of (\d+) models$')
def i_create_an_ensemble(step, number_of_models=2, shared=None):
    if shared is None or world.shared.get("ensemble", {}).get(shared) is None:
        dataset = world.dataset.get('resource')
        try:
            number_of_models = int(number_of_models)
            # tlp is no longer used
            args = {'number_of_models': number_of_models}
        except:
            args = {}
        args.update(NO_MISSING_SPLITS)
        args.update(ENSEMBLE_SAMPLE)
        resource = world.api.create_ensemble(dataset, args=args)
        world.status = resource['code']
        eq_(world.status, HTTP_CREATED)
        world.location = resource['location']
        world.ensemble = resource['object']
        world.ensemble_id = resource['resource']
        world.ensembles.append(resource['resource'])

#@step(r'I wait until the ensemble status code is either (\d) or (-\d)
# less than (\d+)')
def wait_until_ensemble_status_code_is(step, code1, code2, secs):
    world.ensemble = wait_until_status_code_is(
        code1, code2, secs, world.ensemble)


#@step(r'I wait until the ensemble is ready less than (\d+)')
def the_ensemble_is_finished_in_less_than(step, secs, shared=None):
    if shared is None or world.shared.get("ensemble", {}).get(shared) is None:
        wait_until_ensemble_status_code_is(step, FINISHED, FAULTY, secs)
        if shared is not None:
            if "ensemble" not in world.shared:
                world.shared["ensemble"] = {}
            world.shared["ensemble"][shared] = world.ensemble
    else:
        world.ensemble = world.shared["ensemble"][shared]
        world.ensemble_id = world.ensemble["resource"]
        print("Reusing %s" % world.ensemble["resource"])


#@step(r'I create a local Ensemble$')
def create_local_ensemble(step, path=None):
    if path is None:
        world.local_ensemble = Ensemble(world.ensemble_id, world.api)
        world.local_model = Model(world.local_ensemble.model_ids[0], world.api)
    else:
        world.local_ensemble = Ensemble(res_filename(path))
        world.local_model = world.local_ensemble.multi_model.models[0]

#@step(r'I create a local Ensemble$')
def create_local_supervised_ensemble(step):
    world.local_ensemble = SupervisedModel(world.ensemble_id, world.api)
    world.local_model = Model(world.local_ensemble.model_ids[0], world.api)


#@step(r'I create a local EnsemblePredictor from (.*?)$')
def create_local_ensemble_predictor(step, directory):
    module_dir = directory
    directory = res_filename(directory)
    with open(os.path.join(directory, "ensemble.json")) as file_handler:
        ensemble = json.load(file_handler)
    world.local_ensemble = EnsemblePredictor(ensemble, module_dir)

#@step(r'Given I load the full ensemble information from "(.*?)"$')
def load_full_ensemble(step, directory):
    module_dir = directory
    model_list = []
    directory = res_filename(directory)
    with open(os.path.join(directory, "ensemble.json")) as file_handler:
        ensemble = json.load(file_handler)
        model_list.append(ensemble)
    for model_id in ensemble["object"]["models"]:
        with open(os.path.join(directory, model_id.replace("/", "_"))) \
                as file_handler:
            model = json.load(file_handler)
            model_list.append(model)
    return model_list

#@step(r'I create a local Ensemble with the last (\d+) models$')
def create_local_ensemble_with_list(step, number_of_models):
    world.local_ensemble = Ensemble(world.models[-int(number_of_models):],
                                    world.api)

#@step(r'I create a local ensemble from the ensemble +  models list$')
def create_local_ensemble_from_list(step, model_list):
    world.local_ensemble = Ensemble(model_list)

#@step(r'I create a local Ensemble with the last (\d+) local models$')
def create_local_ensemble_with_list_of_local_models(step, number_of_models):
    local_models = [Model(model) for model in
                    world.models[-int(number_of_models):]]
    world.local_ensemble = Ensemble(local_models, world.api)

#@step(r'the field importance text is (.*?)$')
def field_importance_print(step, field_importance):
    field_importance_data = world.local_ensemble.field_importance_data()[0]
    eq_(field_importance_data, json.loads(field_importance))

#@step(r'I create an ensemble with "(.*)"$')
def i_create_an_ensemble_with_params(step, params):
    dataset = world.dataset.get('resource')
    try:
        args = json.loads(params)
    except:
        args = {}
    args.update(ENSEMBLE_SAMPLE)
    resource = world.api.create_ensemble(dataset, args=args)
    world.status = resource['code']
    eq_(world.status, HTTP_CREATED)
    world.location = resource['location']
    world.ensemble = resource['object']
    world.ensemble_id = resource['resource']
    world.ensembles.append(resource['resource'])


#@step(r'I export the ensemble$')
def i_export_ensemble(step, filename):
    world.api.export(world.ensemble.get('resource'),
                     filename=res_filename(filename))

#@step(r'I create a local ensemble from file "(.*)"')
def i_create_local_ensemble_from_file(step, export_file):
    world.local_ensemble = Ensemble(res_filename(export_file))


#@step(r'the ensemble ID and the local ensemble ID match')
def check_ensemble_id_local_id(step):
    eq_(world.local_ensemble.resource_id, world.ensemble["resource"])

#@step(r'I clone ensemble')
def clone_ensemble(step, ensemble):
    resource = world.api.clone_ensemble(ensemble,
                                        {'project': world.project_id})
    # update status
    world.status = resource['code']
    world.location = resource['location']
    world.ensemble = resource['object']
    # save reference
    world.ensembles.append(resource['resource'])

def the_cloned_ensemble_is(step, ensemble):
    eq_(world.ensemble["origin"], ensemble)

"""
'Main' views: index.html, other documentation

app/main/views.py

Author: Jose Painumkal
Date: 23 May 2017
"""
import json
import os
import uuid
import shutil
import urllib
import time
from collections import defaultdict
from flask import current_app as app
from flask import redirect, render_template, session, request, flash
from . import main
from .forms import SearchForm
from gstore_adapter.client import VWClient
from app import cache
from functools import wraps
from flask.ext.security import login_required, current_user
from gstore_client import VWClient
import requests
from ..models import User
from .. import db

requests.packages.urllib3.disable_warnings()


def set_api_token(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if current_user and 'api_token' not in session:
            session['api_token'] = _default_jwt_encode_handler(current_user)
        return func(*args, **kwargs)
    return decorated


@cache.cached(timeout=50)
@main.route('/')
def index():
    """"
    Splash page reads index.md

    """
    user_name = None
    if 'email' in session:
        user_name = session['email']

    content = open(
        os.path.join(os.getcwd(), 'app', 'static', 'docs', 'index.md')
    ).read()

    cc_file = open(
        os.path.join(os.getcwd(), 'app', 'static', 'docs', 'roster.json')
    )
    contributor_cards = json.load(cc_file)

    return render_template("index-info.html", **locals())

def find_user_folder():
    username = current_user.email
    # get the first part of username as part of the final file name
    username_part = username.split('.')[0]
    app_root = os.path.dirname(os.path.abspath(__file__))
    app_root = app_root + '/../static/user_data/' + username_part
    return app_root


def upload_model_data(vwclient, modeluuid_vwp, upload_file):
    swift_upload = app.config['SWIFT_UPLOAD']
    if swift_upload=='TRUE':
        c = vwclient.uploadModelData_swift(modeluuid_vwp, upload_file) 
    else:
        c = vwclient.upload_data(modeluuid_vwp, upload_file)
    return c

def gstore_push(model_id,model_name, model_title, description, push_files):
    # 1) download the model files
    # 2) push the files to gstore
    # 3) push the metadata for each file
    # 4) update gstore_Pushed attribute for pushed model resource and model id
    
    gstore_url = app.config['GSTORE_HOST']
    gstore_uname = app.config['GSTORE_USERNAME']
    gstore_pwd = app.config['GSTORE_PASSWORD']

    if len(push_files)<1:
        return

    resp = {}
    app_root = find_user_folder()
    # clean up previous downloaded files
    shutil.rmtree(app_root, ignore_errors=True)
    if not os.path.exists(app_root):
        os.makedirs(app_root)

    # changing the working directory to the folder where model resources are downloaded
    os.chdir(app_root)

    control_file = app_root + app.config['TEMP_CONTROL']
    data_file = app_root + app.config['TEMP_DATA']
    param_file = app_root + app.config['TEMP_PARAM']
    log = app_root + app.config['TEMP_LOG']
    output_file = app_root + app.config['TEMP_OUTPUT']
    animation = app_root + app.config['TEMP_ANIMATION']
    animation_original = app_root + app.config['TEMP_ANIMATION_ORIGINAL']
    statsvar_original = app_root + app.config['TEMP_STATSVAR_ORIGINAL']
    gsflow_log = app_root + app.config['TEMP_GSFLOW_LOG']
    statsvar = app_root + app.config['TEMP_STATSVAR']

    if current_user.uuid is None:
        user_details = User.query.get(current_user.id)
        if user_details:
            user_details.uuid = str(uuid.uuid4())
            db.session.commit()

            # user_details=user_details.update()

    vwclient = VWClient(gstore_url, gstore_uname, gstore_pwd)
    vwclient.authenticate()

    externaluserid = current_user.uuid
    vwclient.tie_account(application_name='virtualwatershed.org')


    if externaluserid is not None:
        resp_verify = vwclient.verify_external_user(application_name='virtualwatershed.org', user_uuid=externaluserid)
        if resp_verify == False:
            resp_create_external_user = vwclient.create_external_user(application_name='virtualwatershed.org', user_uuid=externaluserid)



    model_run_name = model_title+'_'+time.strftime("%d/%m/%Y_%I:%M:%S")
    modeluuid_vwp = vwclient.createNewModelRun(model_id, model_run_name, model_name, description)
    if modeluuid_vwp == '':
        return
    
    resp['gstore_id'] = modeluuid_vwp
    file_upload_filed = []
    file_metadataUpload_failed = []

    # download the files, push the files, push the metada 

    api_headers={'Authorization': 'JWT %s' % session['api_token']}
    for res_id in push_files:
            model_resource_url = app.config['MODEL_HOST']+'/api/modelresources/'+str(res_id)
            r = requests.get(url=model_resource_url, headers=api_headers)
            resp_dict = json.loads(r.content)
            resource_url = resp_dict['resource_url']
            resource_type = resp_dict['resource_type']
            file_ext = resource_url.split('.')[-1] 

            if resource_type =='control':
                urllib.urlretrieve(resource_url, control_file)
                control_file = app.config['TEMP_CONTROL'].strip("/")
                c = upload_model_data(vwclient, modeluuid_vwp, control_file) 
                if c.status_code !=200:
                    file_upload_filed.append('control')
                else:
                    watershed_metadata = vwclient.metadata_from_file(input_file=control_file,parent_model_run_uuid=modeluuid_vwp, 
                                                    model_run_uuid=modeluuid_vwp, model_run_name=model_run_name, description=description,
                                                    watershed_name='Lehman Creek', state='Nevada',model_name=model_name, model_set='inputs', file_ext=file_ext, externaluserid = externaluserid)
                    metadata_push = vwclient.insert_metadata(watershed_metadata=watershed_metadata)   
                    if metadata_push.status_code !=200:
                        file_metadataUpload_failed.append('control')
                       

            elif resource_type =='data':
                urllib.urlretrieve(resource_url, data_file)
                data_file = app.config['TEMP_DATA'].strip("/")
                d = upload_model_data(vwclient, modeluuid_vwp, data_file) 
                if d.status_code !=200:
                    file_upload_filed.append('data')
                else:
                    watershed_metadata = vwclient.metadata_from_file(input_file=data_file,parent_model_run_uuid=modeluuid_vwp, 
                                                    model_run_uuid=modeluuid_vwp, model_run_name=model_run_name, description=description,
                                                    watershed_name='Lehman Creek', state='Nevada',model_name=model_name ,model_set='inputs', file_ext=file_ext, externaluserid = externaluserid)
                    metadata_push = vwclient.insert_metadata(watershed_metadata=watershed_metadata)   
                    if metadata_push.status_code !=200:
                        file_metadataUpload_failed.append('data')              

            elif resource_type =='param':
                urllib.urlretrieve(resource_url, param_file)
                param_file = app.config['TEMP_PARAM'].strip("/")
                p = upload_model_data(vwclient, modeluuid_vwp, param_file)
                if p.status_code !=200:
                    file_upload_filed.append('param')
                else:
                    watershed_metadata = vwclient.metadata_from_file(input_file=param_file,parent_model_run_uuid=modeluuid_vwp, 
                                                    model_run_uuid=modeluuid_vwp, model_run_name=model_run_name, description=description,
                                                    watershed_name='Lehman Creek', state='Nevada',model_name=model_name ,model_set='inputs', file_ext=file_ext, externaluserid = externaluserid)
                    metadata_push = vwclient.insert_metadata(watershed_metadata=watershed_metadata)   
                    if metadata_push.status_code !=200:
                        file_metadataUpload_failed.append('param')  
                        
            elif resource_type =='animation':
                urllib.urlretrieve(resource_url, animation)
                animation = app.config['TEMP_ANIMATION'].strip("/")
                a = upload_model_data(vwclient, modeluuid_vwp, animation) 
                if a.status_code !=200:
                    file_upload_filed.append('animation')
                else:
                    watershed_metadata = vwclient.metadata_from_file(input_file=animation,parent_model_run_uuid=modeluuid_vwp, 
                                                    model_run_uuid=modeluuid_vwp, model_run_name=model_run_name, description=description,
                                                    watershed_name='Lehman Creek', state='Nevada',model_name=model_name ,model_set='outputs',  file_ext=file_ext, externaluserid = externaluserid)
                    metadata_push = vwclient.insert_metadata(watershed_metadata=watershed_metadata)   
                    if metadata_push.status_code !=200:
                        file_metadataUpload_failed.append('animation')  
                        
            elif resource_type =='log':
                urllib.urlretrieve(resource_url, log)
                log = app.config['TEMP_LOG'].strip("/")
                l = upload_model_data(vwclient, modeluuid_vwp, log) 
                if l.status_code !=200:
                    file_upload_filed.append('log')
                else:
                    watershed_metadata = vwclient.metadata_from_file(input_file=log,parent_model_run_uuid=modeluuid_vwp, 
                                                    model_run_uuid=modeluuid_vwp, model_run_name=model_run_name, description=description,
                                                    watershed_name='Lehman Creek', state='Nevada',model_name=model_name ,model_set='outputs', file_ext=file_ext, externaluserid = externaluserid)
                    metadata_push = vwclient.insert_metadata(watershed_metadata=watershed_metadata)   
                    if metadata_push.status_code !=200:
                        file_metadataUpload_failed.append('log')  


            elif resource_type =='output':
                urllib.urlretrieve(resource_url, output_file)
                output_file = app.config['TEMP_OUTPUT'].strip("/")
                o = upload_model_data(vwclient, modeluuid_vwp, output_file) 
                if o.status_code !=200:
                    file_upload_filed.append('output')
                else:
                    watershed_metadata = vwclient.metadata_from_file(input_file=output_file,parent_model_run_uuid=modeluuid_vwp, 
                                                    model_run_uuid=modeluuid_vwp, model_run_name=model_run_name, description=description,
                                                    watershed_name='Lehman Creek', state='Nevada',model_name=model_name ,model_set='outputs', file_ext=file_ext, externaluserid = externaluserid)
                    metadata_push = vwclient.insert_metadata(watershed_metadata=watershed_metadata)   
                    if metadata_push.status_code !=200:
                        file_metadataUpload_failed.append('output')  
                       

            elif resource_type =='animation_original':
                urllib.urlretrieve(resource_url, animation_original)
                animation_original = app.config['TEMP_ANIMATION_ORIGINAL'].strip("/")
                a_org = upload_model_data(vwclient, modeluuid_vwp, animation_original) 
                if a_org.status_code !=200:
                    file_upload_filed.append('animation_original')
                else:
                    watershed_metadata = vwclient.metadata_from_file(input_file=animation_original,parent_model_run_uuid=modeluuid_vwp, 
                                                    model_run_uuid=modeluuid_vwp, model_run_name=model_run_name, description=description,
                                                    watershed_name='Lehman Creek', state='Nevada',model_name=model_name ,model_set='outputs',  file_ext=file_ext, externaluserid = externaluserid)
                    metadata_push = vwclient.insert_metadata(watershed_metadata=watershed_metadata)   
                    if metadata_push.status_code !=200:
                        file_metadataUpload_failed.append('animation_original')  
                        
            elif resource_type =='statsvar_original':
                urllib.urlretrieve(resource_url, statsvar_original)
                statsvar_original = app.config['TEMP_STATSVAR_ORIGINAL'].strip("/")
                statsvar_org = upload_model_data(vwclient, modeluuid_vwp, statsvar_original) 
                if statsvar_org.status_code !=200:
                    file_upload_filed.append('statsvar_original')
                else:
                    watershed_metadata = vwclient.metadata_from_file(input_file=statsvar_original,parent_model_run_uuid=modeluuid_vwp, 
                                                    model_run_uuid=modeluuid_vwp, model_run_name=model_run_name, description=description,
                                                    watershed_name='Lehman Creek', state='Nevada',model_name=model_name ,model_set='outputs', file_ext=file_ext, externaluserid = externaluserid)
                    metadata_push = vwclient.insert_metadata(watershed_metadata=watershed_metadata)   
                    if metadata_push.status_code !=200: 
                        file_metadataUpload_failed.append('statsvar_original') 
                        
            elif resource_type =='gsflow_log':
                urllib.urlretrieve(resource_url, gsflow_log)
                gsflow_log = app.config['TEMP_GSFLOW_LOG'].strip("/")
                g = upload_model_data(vwclient, modeluuid_vwp, gsflow_log) 
                if g.status_code !=200:
                    file_upload_filed.append('gsflow_log')
                else:
                    watershed_metadata = vwclient.metadata_from_file(input_file=gsflow_log,parent_model_run_uuid=modeluuid_vwp, 
                                                    model_run_uuid=modeluuid_vwp, model_run_name=model_run_name, description=description,
                                                    watershed_name='Lehman Creek', state='Nevada',model_name=model_name ,model_set='outputs', file_ext=file_ext, externaluserid = externaluserid)
                    metadata_push = vwclient.insert_metadata(watershed_metadata=watershed_metadata)   
                    if metadata_push.status_code !=200:
                        file_metadataUpload_failed.append('gsflow_log')  
                       
            elif resource_type =='statsvar':
                urllib.urlretrieve(resource_url, statsvar)
                statsvar = app.config['TEMP_STATSVAR'].strip("/")
                s = upload_model_data(vwclient, modeluuid_vwp, statsvar) 
                if s.status_code !=200:
                    file_upload_filed.append('statsvar')
                else:
                    watershed_metadata = vwclient.metadata_from_file(input_file=statsvar,parent_model_run_uuid=modeluuid_vwp, 
                                                    model_run_uuid=modeluuid_vwp, model_run_name=model_run_name, description=description,
                                                    watershed_name='Lehman Creek', state='Nevada',model_name=model_name ,model_set='outputs', file_ext=file_ext, externaluserid = externaluserid)
                    metadata_push = vwclient.insert_metadata(watershed_metadata=watershed_metadata)   
                    if metadata_push.status_code !=200:
                        file_metadataUpload_failed.append('statsvar')  
            else:
                app.logger.error("Unknown resource type")


    resp['failed_file_upload'] = file_upload_filed
    resp['file_metadataUpload_failed'] = file_metadataUpload_failed
    resp['SWIFT_UPLOAD'] = app.config['SWIFT_UPLOAD']

    return resp


@main.route('/push_to_gstore', methods=['POST'])
@login_required
@set_api_token
def push_to_gstore():
    if request.method == 'POST':

        content = request.get_json(silent=True)
        model_id = content['model_id']
        model_name = content['model_name']
        model_title = content['model_title']
        push_files = content['push_files']
        description = content['description']

        ### TODO: call Gstore, push files, and store the VWP id in modeldb
        resp = gstore_push(model_id,model_name, model_title, description, push_files)

        if resp is None:
            return "Gstore Push Failed"

        gstore_id = resp['gstore_id']
        api_headers={'Authorization': 'JWT %s' % session['api_token']}
        # 1) update gstore_Pushed attribute of pushed model resources
        for res_id in push_files:
            model_resource_url = app.config['MODEL_HOST']+'/api/modelresources/gstorepush/'+str(res_id)
            r = requests.put(url=model_resource_url, headers=api_headers)

        # 2) update gstorePushed attibute of model
        model_id_apiUrl = app.config['MODEL_HOST']+'/api/modelruns/gstorepush/'+str(model_id)+'/'+str(gstore_id)
        r = requests.put(url=model_id_apiUrl, headers=api_headers)
        resp_dict = json.loads(r.content)
       
        return json.dumps(resp)




@main.route('/remove_from_gstore', methods=['POST'])
@login_required
@set_api_token
def remove_from_gstore():
    if request.method == 'POST':

        content = request.get_json(silent=True)
        model_id = content['model_id']
        gstore_id = content['gstore_id']

        #remove from GStore
        gstore_url = app.config['GSTORE_HOST']
        gstore_uname = app.config['GSTORE_USERNAME']
        gstore_pwd = app.config['GSTORE_PASSWORD']

        vwclient = VWClient(gstore_url, gstore_uname, gstore_pwd)
        vwclient.authenticate()
        result = vwclient.deleteModelRun(gstore_id);

        if result==True:
            #remove from virtualwatershed db

            api_headers={'Authorization': 'JWT %s' % session['api_token']}
            model_run_url = app.config['MODEL_HOST']+'/api/modelruns/'+str(model_id)

            r = requests.get(url=model_run_url, headers=api_headers)
            resp_dict = json.loads(r.content)
            
            # 1) change gstore_Push attribute of resources to false
            resource_list = resp_dict['resources']
            for res in resource_list:
                res_id = res['id']
                if res['gstore_Pushed'] == 'true':
                    model_resource_url = app.config['MODEL_HOST']+'/api/modelresources/gstore_remove/'+str(res_id) 
                    r = requests.put(url=model_resource_url, headers=api_headers)

            # 2) change gstore_Push attribute of model to false
            model_id_apiUrl = app.config['MODEL_HOST']+'/api/modelruns/gstore_remove/'+str(model_id)+'/'+str(gstore_id)
            r = requests.put(url=model_id_apiUrl, headers=api_headers)
            resp_dict = json.loads(r.content)
            return json.dumps(resp_dict)

        else:
            gstore_delete_error = "Unknown exception occured while deleting model run from gstore."
            return json.dumps(gstore_delete_error)




       



@main.route('/search', methods=['GET', 'POST'])
def search():
    """
    Create model run panels, rectangles on the search/home page that display
    summary information about the data that the VW has for a particular model
    run.

    Returns: (str) HTML string of the model run panel
    """
    panels = []
    search_fields = ['model_run_name', 'researcher_name', 'model_keywords',
                     'description']
    search_results = []
    form = SearchForm(request.args)

    vw_client = VWClient(app.config['GSTORE_HOST'],
                         app.config['GSTORE_USERNAME'],
                         app.config['GSTORE_PASSWORD'])

    if request.args and not form.validate():
        flash('Please fill out at least one field')

        return render_template('search.html', form=form, panels=panels)
    if request.args:
        words = form.model_run_name.data.split()

    if request.args:
        for search_field in search_fields:
            search_args = defaultdict()
            for w in words:
                search_args[search_field] = w
                results = vw_client.modelrun_search(**search_args)
                search_results += results.records

    records = search_results
    if records:
        # make a panel of each metadata record
        panels = [_make_panel(rec) for rec in records if rec]

        panels = {p['model_run_uuid']: p for p in panels}.values()

    # pass the list of parsed records to the template to generate results page
    return render_template('search.html', form=form, panels=panels)

@main.route('/docs/vwpy', methods=['GET'])
def vwpydoc():
    return redirect('/static/docs/vwpy/index.html')

@main.route('/docs', methods=['GET'])
def docredir():
    return redirect('/static/docs/vwpy/index.html')


def _make_panel(search_record):
    """
    Extract fields we currently support from a single JSON metadata file and
    prepare them in dict form to render search.html.

    Returns: (dict) that will be an element of the list of panel_data to be
        displayed as search results
    """
    panel = {"keywords": search_record['Keywords'],
             "description": search_record['Description'],
             "researcher_name": search_record['Researcher Name'],
             "model_run_name": search_record['Model Run Name'],
             "model_run_uuid": search_record['Model Run UUID']}

    return panel

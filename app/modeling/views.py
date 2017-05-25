import random
import string
from functools import wraps

from flask import render_template,session, request, flash
from flask import current_app as app
from flask.ext.security import login_required
from ..main.gstore_client import VWClient 
import requests
requests.packages.urllib3.disable_warnings()

from . import modeling


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


from flask.ext.login import user_logged_in
from flask import session
from flask_jwt import _default_jwt_encode_handler
from flask.ext.security import current_user
#
# @user_logged_in.connect_via(app)
# def on_user_logged_in(sender, user):
#     key = _default_jwt_encode_handler(current_user)
#     session['api_token'] = key

def set_api_token(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if current_user and 'api_token' not in session:
            session['api_token'] = _default_jwt_encode_handler(current_user)
        return func(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return '.' in filename and\
        filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


@modeling.route('/', methods=['GET'])
def modeling_index():
    return render_template('modeling/index.html')


@modeling.route('/dashboard/', methods=['GET'])
@login_required
@set_api_token
def modelling_dashboard():

    return render_template('modeling/dashboard.html',
                           VWMODEL_SERVER_URL=app.config['MODEL_HOST'])



@modeling.route('/search_gstore/', methods=['GET'])
@login_required
@set_api_token
def search_gstore():
    return render_template('modeling/search_gstore.html',
                           VWMODEL_SERVER_URL=app.config['MODEL_HOST'])



@modeling.route('/gstore/', methods=['GET'])
@login_required
@set_api_token
def search_in_gstore():
    gstore_url = app.config['GSTORE_HOST']
    gstore_uname = app.config['GSTORE_USERNAME']
    gstore_pwd = app.config['GSTORE_PASSWORD']

    vwclient = VWClient(gstore_url, gstore_uname, gstore_pwd)
    vwclient.authenticate()


    kwargs = {}
    if request.args.get('model_name'):
        kwargs['model_name'] = request.args.get('model_name')
    if request.args.get('model_set_taxonomy'):
        kwargs['model_set_taxonomy'] = request.args.get('model_set_taxonomy')
    if request.args.get('model_run_uuid'):
        kwargs['model_run_uuid'] = request.args.get('model_run_uuid')
    if request.args.get('externaluserid') :
        kwargs['externaluserid'] = request.args.get('externaluserid')
    if request.args.get('model_set') :
        kwargs['model_set'] = request.args.get('model_set')
    if request.args.get('taxonomy'):
        kwargs['taxonomy'] = request.args.get('taxonomy')
    if request.args.get('model_set_type') :
        kwargs['model_set_type'] = request.args.get('model_set_type')
    if request.args.get('service'):
        kwargs['service'] = request.args.get('service')
    if request.args.get('sort_order') :
        kwargs['sort_order'] = request.args.get('sort_order')
    search_results = vwclient.search_datasets(**kwargs)
    # resp_dict = json.loads(search_results.content)
       
    return search_results
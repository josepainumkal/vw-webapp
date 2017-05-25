"""
'Main' views: index.html, other documentation

app/main/views.py

Author: Matthew Turner
Date: 20 January 2016
"""
import json
import os
import time
import urllib
from datetime import datetime

from collections import defaultdict

from flask import current_app as app
from flask import redirect, render_template, session, request, flash
from jinja2 import Environment, FileSystemLoader

from gstore_client import VWClient
import requests

requests.packages.urllib3.disable_warnings()

gstore_username = 'josepainumkal@gmail.com'
gstore_password = 'Rosh@2016'
gstore_host_url = 'https://vwp-dev.unm.edu/'

vwclient = VWClient(gstore_host_url, gstore_username, gstore_password)
vwclient.authenticate()

model_Id = '61'
model_title = "test08"
model_type = 'prms'
model_desc = 'test08'



kwargs = {}
kwargs['dir'] = 'ASC'


search_results = vwclient.search_datasets(**kwargs)
# resp_dict = json.loads(search_results.content)
   
print search_results








# externaluserid = 'cd04d159-bdc8-41e2-8bf0-cb20311ed630'
# watershed_metadata = vwclient.metadata_from_file(input_file='prms_statsvar_output_txtTNPRLE.txt',parent_model_run_uuid=modeluuid_vwp, model_run_uuid=modeluuid_vwp, model_run_name=model_run_name, description=model_desc,
#  	                                             watershed_name='Lehman Creek', state='Nevada',model_name='prms',model_set='inputs', externaluserid = externaluserid)

# #print watershed_metadata


# metadatapush_result = vwclient.insert_metadata(watershed_metadata=watershed_metadata)
# print metadatapush_result.text
# print metadatapush_result

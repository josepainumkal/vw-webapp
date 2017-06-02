"""
Virtual Watershed Adaptor. Handles fetching and searching of data, model
run initialization, and pushing of data. Does this for associated metadata
as well. Each file that's either taken as input or produced as output gets
associated metadata.
"""

import configparser
import json
import logging
import os
import requests
import subprocess
import urllib
import uuid

from datetime import datetime, date, timedelta
from jinja2 import Environment, FileSystemLoader

requests.packages.urllib3.disable_warnings()
import base64


VARNAME_DICT = \
    {
        'in': ["I_lw", "T_a", "e_a", "u", "T_g", "S_n"],
        'em': ["R_n", "H", "L_v_E", "G", "M", "delta_Q", "E_s", "melt",
               "ro_predict", "cc_s"],
        'snow': ["z_s", "rho", "m_s", "h2o", "T_s_0", "T_s_l", "T_s",
                 "z_s_l", "h2o_sat"],
        'init': ["z", "z_0", "z_s", "rho", "T_s_0", "T_s", "h2o_sat"],
        'precip': ["m_pp", "percent_snow", "rho_snow", "T_pp"],
        'mask': ["mask"],
        'dem': ["alt"]
    }


class VWClient:
    """
    Client class for interacting with a Virtual Watershed (VW). A VW
    is essentially a structured database with certain rules for its
    metadata and for uploading or inserting data.
    """
    # number of times to re-try an http request
    _retry_num = 3

    def __init__(self, host_url, uname, passwd):
        self.host_url = host_url
        self.auth_url = host_url + "/apilogin"
        self.gettoken_url = host_url + "/gettoken"
        self.checkmodeluuidURL = self.host_url+"/apps/vwp/checkmodeluuid"
        self.newmodelrunURL = self.host_url+"/apps/vwp/newmodelrun"
        self.modelrun_delete_url = self.host_url + "/apps/vwp/deletemodelid"
        self.swiftuploadurl = self.host_url + 'apps/vwp/swiftdata'
        self.insert_dataset_url = self.host_url + "apps/vwp/datasets"
        self.uname = uname
        self.passwd = passwd
        self.session = requests.Session()
        self.auth = (self.uname, self.passwd)

        self.tie_account_url = self.host_url+"createexternalapp"
        self.show_external_users_url = self.host_url+"showexternalusers"
        self.create_external_users_url = self.host_url+"createexternaluser"
        self.verify_external_user_url = self.host_url+"showexternalusers?userid="

        self.search_url = self.host_url+"/apps/vwp/search/datasets.json"
        self.upload_url = self.host_url+"/apps/vwp/data"


    def search_datasets(self, **kwargs):
        payload={}

        if 'model_name' in kwargs:
            payload['modelname'] = kwargs['model_name']
        if 'model_set_taxonomy' in kwargs:
            payload['model_set_taxonomy'] = kwargs['model_set_taxonomy']
        if 'model_run_uuid' in kwargs:
            payload['model_run_uuid'] = kwargs['model_run_uuid']
        if 'externaluserid' in kwargs:
            payload['externaluserid'] = kwargs['externaluserid']
        if 'model_set' in kwargs:
            payload['model_set'] = kwargs['model_set']
        if 'taxonomy' in kwargs:
            payload['taxonomy'] = kwargs['taxonomy']
        if 'model_set_type' in kwargs:
            payload['model_set_type'] = kwargs['model_set_type']
        if 'service' in kwargs:
            payload['service'] = kwargs['service'] 
        if 'sort_order' in kwargs:
            payload['dir'] = kwargs['sort_order']   
        
        print "\n\n\n payload: ",payload


        result = self.session.get(self.search_url, params=payload, verify=False)

        print result


        result = json.dumps(json.loads(result.content))
        return result

    

    def authenticate(self):
        try:
            login = self.session.get(self.auth_url, auth=(self.uname,self.passwd), verify=False)     
            token = self.session.get(self.gettoken_url)
            self.token = json.loads(token.text)
            if login.status_code==200:
                return True 
        except Exception as e:
            return False

    def tie_account(self, application_name):
        result = None
        try:    
            # application_name='virtualwatershed.org'
            payload = {'application':application_name}
            result = self.session.post(self.tie_account_url, data=json.dumps(payload), verify=False)
            # print result.status_code
            if result.status_code == 200 or result.status_code == 422:
                # 422 means Relationship already exists
                return True
            
        except Exception as e:
            if result.status_code == 422:
                return True
            else:
                print '\t', result.content
                return False

    
    def get_external_users(self, application_name):
        # returns list of users
        payload = {'application':application_name}
        result = self.session.get(self.show_external_users_url, data=json.dumps(payload), verify=False)

        result = json.loads(result.content)
        return result['userids']

    def verify_external_user(self, application_name, user_uuid):
        result = None
        try:
            payload = {'application':application_name}
            result = self.session.get(self.verify_external_user_url+user_uuid, data=json.dumps(payload), verify=False)
            result = json.loads(result.content)
            if result['exists'] == 'True':
                return True
            else:
                return False

        except Exception as e:
            print '\t', result.content
            return False


    def create_external_user(self, application_name, user_uuid):
        # returns list of users
        try:   
            payload = {'application':application_name, 'userid':user_uuid}
            result = self.session.post(self.create_external_users_url, data=json.dumps(payload), verify=False)
            if result.status_code != 200:
                return True
            else:
                print '\t', result.content
                return False
        except Exception as e:
            print '\t', result.content
            return False

    
    # Verifies if a model run UUID already exists | Returns True or False
    def verifyModelRun(self, modelRunId):
        data = {'modelid': modelRunId}
        base64string = base64.b64encode('%s:%s' % (self.uname, self.passwd)).replace('\n', '')
        str ='Basic '+base64string
        headers = {'Authorization':str}
        
        result = self.session.post(self.checkmodeluuidURL, data=data, auth=self.auth, headers=headers, verify=False)
        print result.text
        return result.text


    #  Creates a new model run in VWP | Returns modelID, if success
    def createNewModelRun(self, modelRunId, model_run_name, modelType, description=''):
        # newmodelname = modelTitle + ' [VW-Modejl Id = '+modelRunId+']'
        # newmodelname = "VWModel " + modelRunId
        modeldata = json.dumps({"description": description,"model_run_name":model_run_name ,"model_keywords":modelType})
        result = self.session.post(self.newmodelrunURL, data=modeldata, auth=self.auth, verify=False)
        if result.status_code == 200:
            return result.text    #result.text is the modelID in VWP platform
        else:
            print result.text
 
#  Deletes a model run in VWP | Returns True, if successfully deleted
    def deleteModelRun(self, model_run_uuid):
#        Delete a model run associated with model_run_uuid
#        Returns:
#             (bool) True if successful, False if not

        full_url = self.modelrun_delete_url + model_run_uuid
        result = self.session.delete(self.modelrun_delete_url,data=json.dumps({'model_uuid': model_run_uuid}), verify=False)

        if result.status_code == 200:
            return True
        elif result.status_code == 422:
            print 'The model run uuid is not located in the list of model runs'
            return False
        else:
            print 'Unknown exception occurred on deleting model run'
            return False


    def upload_data(self, model_id, path_to_file):
        payload = {"modelid": model_id}
        files = {'file': open(path_to_file, 'rb')}
        result = self.session.post(self.upload_url, files=files, data=payload, auth=self.auth, verify=False)

        if result.status_code == 200:
            print result.text
            return result
        else:
            print "FAILED UPLOAD! The error is: " + result.text
            return result

    
    def uploadModelData_swift(self, modelID_VWP, file_name):
#       Use the Swift client from openstack to upload data.
#       (http://docs.openstack.org/cli-reference/content/swiftclient_commands.html)
#       Seems to outperform 'native' watershed uploads via HTTP.
#       Returns:
#             None
#       Raises:
#             requests.HTTPError if the file cannot be successfully uploaded

        preauthurl = self.token['preauthurl']
        preauthtoken = self.token['preauthtoken']

         # Upload to Swift using token
        containername = modelID_VWP
        filename = file_name
        # filename = os.path.abspath(file_name)
        # print filename
        segmentsize = 1073741824 # 1 Gig

        command = ['swift']
        command.append('upload')
        command.append(containername)
        command.append('-S')
        command.append(str(segmentsize))
        command.append(filename)
        command.append('--os-storage-url='+preauthurl)
        command.append('--os-auth-token='+preauthtoken)

        # print command
        ls_output = subprocess.check_output(command)
        print ls_output

        params = {'modelid':modelID_VWP,'filename':filename,'preauthurl':preauthurl,'preauthtoken':preauthtoken}
        uploadURL = self.host_url + 'apps/vwp/swiftdata'

        r = self.session.get(self.swiftuploadurl, params=params)
        if r.status_code == 200:
            print "File has successfully uploaded to VWP!"
        else:
            print r.content
            raise requests.HTTPError("Swift Upload Failed! Server response:\n" + r.text)
        return r


    def insert_metadata(self, watershed_metadata):
        """ Insert metadata to the virtual watershed. The data that gets
            uploaded is the FGDC XML metadata.
            Returns:
                (requests.Response) Returned so that the user may inspect
                the response.
        """
        num_tries = 0
        result = None
        while num_tries < self._retry_num:
            try:
                result = self.session.put(self.insert_dataset_url,
                                       data=watershed_metadata,
                                       auth=(self.uname, self.passwd),
                                       verify=False)
                
                if result.status_code != 200:
                    print "\n\nERROR---------------------------------------------insert_metadata---------------------"
                    print result.content
                   

                logging.debug(result.content)

                result.raise_for_status()
                return result

            except requests.HTTPError:
                num_tries += 1
                print result.content
                continue

        return result



    def _get_config(self,config_file=None):
        """Provide user with a ConfigParser that has read the `config_file`
            Returns:
                (ConfigParser) Config parser with three sections: 'Common',
                'FGDC Metadata', and 'Watershed Metadata'
        """
        if config_file is None:
            config_file = \
                os.path.join(os.path.dirname(__file__), '../templates/default.conf')

        assert os.path.isfile(config_file), "Config file %s does not exist!" \
            % os.path.abspath(config_file)

        config = configparser.ConfigParser()
        config.read(config_file)
        
        return config



    def metadata_from_file(self,input_file, parent_model_run_uuid, model_run_uuid, model_run_name,
                           description, watershed_name, state, start_datetime=None,
                           end_datetime=None, model_name=None, fgdc_metadata=None,
                           model_set_type=None, model_set_taxonomy=None,
                           taxonomy=None, water_year_start=2010,
                           water_year_end=2011, config_file=None, dt=None,
                           model_set=None, model_vars=None, file_ext=None, externaluserid=None,
                           **kwargs):
        """
        Generate metadata for input_file.
        Arguments:
            **kwargs: Set union of kwargs from make_fgdc_metadata and
                make_watershed_metadata
        Returns:
            (str) watershed metadata
        """
        assert dt is None or issubclass(type(dt), timedelta)
        dt_multiplier = 1  # default if nothing else is known

        if config_file:
            config = self._get_config(config_file)
        else:
            config = self._get_config(os.path.join(os.path.dirname(__file__), 'templates/default.conf'))

        input_basename = os.path.basename(input_file)

        input_split = input_basename.split('.')

        input_prefix = input_split[0]

        if not file_ext:
            file_ext = input_file.split('.')[-1]

        if not model_set:
            model_set = ("outputs", "inputs")[input_prefix == "in"]

        start_datetime_str = ""
        end_datetime_str = ""

        is_ipw = False
        try:
            # the number on the end of an isnobal file is the time index
            dt_multiplier = int(input_split[1])
            is_ipw = True
        except (ValueError, IndexError):
            pass

       ############ PRMS ##########################
        if model_name.lower() == 'prms':
            if file_ext == 'nc':
                model_set_type = 'vis'
                taxonomy = 'netcdf'
            else:
                model_set_type = 'file'
                taxonomy = 'file'

            kwargs['taxonomy'] = taxonomy
            model_set_taxonomy= 'file'
            kwargs['model_run_name'] = model_run_name
            # kwargs['name'] = 'Incline_Creek_Gaging_Stations'
            kwargs['lastupdate'] = datetime.now().strftime ("%Y%m%d")
            kwargs['type'] = 'dataset'
        ##########################################

        if file_ext == 'tif':

            model_set_type = 'vis'
            kwargs['taxonomy'] = 'geoimage'
            kwargs['mimetype'] = 'application/x-zip-compressed'

        elif file_ext == 'asc':
            file_ext = 'ascii'
            model_set_type = 'file'
            model_set_taxonomy = 'file'
            kwargs['taxonomy'] = 'file'

        elif file_ext == 'xlsx':
            model_set_taxonomy = 'file'
            model_set_type = 'file'
            kwargs['taxonomy'] = 'file'

        elif model_name == 'isnobal' and is_ipw:
            #: ISNOBAL variable names to be looked up to make dataframes + metadata
            try:
                model_vars = ','.join(VARNAME_DICT[input_prefix])
            except:
                model_vars = ''

            if 'proc_date' in kwargs:
                proc_date = kwargs['proc_date']
            else:
                # proc_date = '20150505'
                proc_date = datetime.now().strftime ("%Y%m%d")

            fgdc_metadata = make_fgdc_metadata(input_basename, config,
                                               model_run_uuid, start_datetime,
                                               end_datetime, proc_date=proc_date)

        elif model_name == 'isnobal' and file_ext == 'nc':

            model_vars = ','.join([','.join(v) for v in VARNAME_DICT.itervalues()])

        if dt is None:
            dt = timedelta(hours=1)

        # calculate the "dates" fields for the watershed JSON metadata
        start_dt = dt * dt_multiplier

        if (start_datetime is None and end_datetime is None):
            start_datetime = datetime(water_year_start, 10, 01) + start_dt
            start_datetime_str = start_datetime.strftime('%Y-%m-%d %H:%M:%S')

            end_datetime = start_datetime + dt
            end_datetime_str = datetime.strftime(start_datetime + dt,
                                                 '%Y-%m-%d %H:%M:%S')

        elif type(start_datetime) is str and type(end_datetime) is str:
            start_datetime_str = start_datetime
            end_datetime_str = end_datetime

        elif type(start_datetime) is datetime and type(end_datetime) is datetime:
            start_datetime_str = datetime.strftime(start_datetime,
                                                   '%Y-%m-%d %H:%M:%S')
            end_datetime_str = datetime.strftime(end_datetime,
                                                 '%Y-%m-%d %H:%M:%S')

        else:
            raise TypeError('bad start_ and/or end_datetime arguments')

        # we pretty much always want to try to set these
        kwargs['wms'] = 'wms'
        kwargs['wcs'] = 'wcs'

        if file_ext == 'nc' and model_name == 'isnobal':
            kwargs['taxonomy'] = 'netcdf_isnobal'

        if 'taxonomy' not in kwargs:
            kwargs['taxonomy'] = 'file'
        elif kwargs['taxonomy'] == '':
            kwargs['taxonomy'] = 'file'

        return \
            self.make_watershed_metadata(input_basename,
                                    config,
                                    parent_model_run_uuid,
                                    model_run_uuid,
                                    model_set,
                                    watershed_name,
                                    state,
                                    model_name=model_name,
                                    model_set_type=model_set_type,
                                    model_set_taxonomy=model_set_taxonomy,
                                    fgdc_metadata=fgdc_metadata,
                                    description=description,
                                    model_vars=model_vars,
                                    start_datetime=start_datetime_str,
                                    end_datetime=end_datetime_str,
                                    file_ext=file_ext, externaluserid=externaluserid, **kwargs)


    def make_fgdc_metadata(self, file_name, config, model_run_uuid, beg_date, end_date,
                           **kwargs):
        """
        For a single `data_file`, write the XML FGDC metadata
           valid kwargs:
               proc_date: date data was processed
               theme_key: thematic keywords
               model: scientific model, e.g., WindNinja, iSNOBAL, PRMS, etc.
               researcher_name: name of researcher
               mailing_address: researcher's mailing address
               city: research institute city
               state: research institute state
               zip_code: research institute zip code
               researcher_phone: researcher phone number
               row_count: number of rows in dataset
               column_count: number of columns in dataset
               lat_res: resolution in latitude direction (meters)
               lon_res: resolution in longitude direction (meters)
               map_units: distance units of the map (e.g. 'm')
               west_bound: westernmost longitude of bounding box
               east_bound: easternmost longitude of bounding box
               north_bound: northernmost latitude of bounding box
               south_bound: southernmost latitude of bounding box
               file_ext: extension of file used to fill out digtinfo:formname;
                if not specified, make_fgdc_metadata takes extension
            Any other kwargs will be ignored
        Returns: XML FGDC metadata string
        """
        try:
            statinfo = os.stat(file_name)
            file_size = "%s" % str(statinfo.st_size/1000000)
        except OSError:
            file_size = "NA"

        if not config:
            config = _get_config(
                os.path.join(os.path.dirname(__file__), '../templates/default.conf'))

        # handle missing required fields not provided in kwargs
        geoconf = config['Geo']
        resconf = config['Researcher']

        # if any of the bounding boxes are not given, all go to default
        if not ('west_bound' in kwargs and 'east_bound' in kwargs
                and 'north_bound' in kwargs and 'south_bound' in kwargs):
            kwargs['west_bound'] = geoconf['default_west_bound']
            kwargs['east_bound'] = geoconf['default_east_bound']
            kwargs['north_bound'] = geoconf['default_north_bound']
            kwargs['south_bound'] = geoconf['default_south_bound']

        if not 'proc_date' in kwargs:
            kwargs['proc_date'] = date.strftime(date.today(), '%Y%m%d')

        if not 'researcher_name' in kwargs:
            kwargs['researcher_name'] = resconf['researcher_name']

        if not 'mailing_address' in kwargs:
            kwargs['mailing_address'] = resconf['mailing_address']

        if not 'city' in kwargs:
            kwargs['city'] = resconf['city']

        if not 'state' in kwargs:
            kwargs['state'] = resconf['state']

        if not 'zip_code' in kwargs:
            kwargs['zip_code'] = resconf['zip_code']

        if not 'researcher_phone' in kwargs:
            kwargs['researcher_phone'] = resconf['phone']

        if not 'researcher_email' in kwargs:
            kwargs['researcher_email'] = resconf['email']

        if 'file_ext' not in kwargs:
            kwargs['file_ext'] = file_name.split('.')[-1]


        ##### handling Unknowns ############

        if 'geoform' not in kwargs:
            kwargs['geoform'] = 'Unknown'

        if 'pubplace' not in kwargs:
            kwargs['pubplace'] = 'Unknown'

        if 'publish' not in kwargs:
            kwargs['publish'] = 'Unknown'

        if 'abstract' not in kwargs:
            kwargs['abstract'] = 'Unknown'

        if 'purpose' not in kwargs:
            kwargs['purpose'] = 'Unknown'

        if 'supplinf' not in kwargs:
            kwargs['supplinf'] = 'Unknown'

        if 'accconst' not in kwargs:
            kwargs['accconst'] = 'Unknown'

        if 'useconst' not in kwargs:
            kwargs['useconst'] = 'Unknown'
        
        if 'beg_date' not in kwargs:
            kwargs['beg_date'] = 'Unknown'
        
        if 'end_date' not in kwargs:
            kwargs['end_date'] = 'Unknown'


        template_env = Environment(loader=FileSystemLoader(
                                   os.path.join(os.path.dirname(__file__), 'templates')))

        template = template_env.get_template('fgdc_template.xml')

        output = template.render(file_name=file_name,
                                 file_size=file_size,
                                 model_run_uuid=model_run_uuid,
                                 **kwargs)

        return output


    def make_watershed_metadata(self, file_name, config, parent_model_run_uuid,
                                model_run_uuid, model_set, watershed_name,
                                state, fgdc_metadata=None, file_ext=None, externaluserid=None,
                                **kwargs):

        """ For a single `file_name`, write the corresponding Virtual Watershed JSON
            metadata.
            valid kwargs:
                orig_epsg: original EPSG code of projection
                epsg: current EPSG code
                taxonomy: likely 'file'; representation of the data
                model_vars: variable(s) represented in the data
                model_set: 'inputs', 'outputs', or 'reference'; AssertionError if not
                model_set_type: e.g., 'binary', 'csv', 'tif', etc.
                model_set_taxonomy: 'grid', 'vector', etc.
                west_bound: westernmost longitude of bounding box
                east_bound: easternmost longitude of bounding box
                north_bound: northernmost latitude of bounding box
                south_bound: southernmost latitude of bounding box
                start_datetime: datetime observations began, formatted like "2010-01-01 22:00:00"
                end_datetime: datetime observations ended, formatted like "2010-01-01 22:00:00"
                wms: True if wms service can and should be enabled
                wcs: True if wcs service can and should be enabled
                watershed_name: Name of watershed, e.g. 'Dry Creek' or 'Lehman Creek'
                model_name: Name of model, if applicaple; e.g. 'iSNOBAL', 'PRMS'
                mimetype: defaults to application/octet-stream
                file_ext: extension to be associated with the dataset; make_watershed_metadata
                 will take the extension of file_name if not given explicitly
                fgdc_metadata: FGDC md probably created by make_fgdc_metadata; if not
                 given, a default version is created (see source for details)
            Returns: JSON metadata string
        """

        assert model_set in ["inputs", "outputs", "reference"], \
            "parameter model_set must be either 'inputs' or 'outputs', not %s" \
            % model_set

        # TODO get valid_states and valid_watersheds from VW w/ TODO VWClient method
        valid_states = ['Idaho', 'Nevada', 'New Mexico']
        assert state in valid_states, "state passed was " + state + \
                ". Must be one of " + ", ".join(valid_states)

        valid_watersheds = ['Dry Creek', 'Valles Caldera', 'Jemez Caldera','Lehman Creek', 'Reynolds Creek']
        assert watershed_name in valid_watersheds, "watershed passed was " + watershed_name + ". Must be one of " + ", ".join(valid_watersheds)

        # logic to figure out mimetype and such based on extension
        if not file_ext:
            file_ext = file_name.split('.')[-1]

            # check that the file extension is not a digit as might happen for isnobal
            if file_ext.isdigit():
                raise ValueError("The extension is a digit. You must explicitly"
                    + " provide the file extension with keyword 'file_ext'")

        if file_ext == 'tif':
            if 'wcs' not in kwargs:
                kwargs['wcs'] = True
            if 'wms' not in kwargs:
                kwargs['wms'] = True
            if 'tax' not in kwargs:
                kwargs['tax'] = 'geoimage'
            if 'mimetype' not in kwargs:
                kwargs['mimetype'] = 'application/x-zip-compressed'
            if 'model_set_type' not in kwargs:
                kwargs['model_set_type'] = 'vis'

        if 'mimetype' not in kwargs:
            kwargs['mimetype'] = 'application/octet-stream'

        # If one of the datetimes is missing
        if not ('start_datetime' in kwargs and 'end_datetime' in kwargs):
            kwargs['start_datetime'] = "1970-10-01 00:00:00"
            kwargs['end_datetime'] = "1970-10-01 01:00:00"

        if not fgdc_metadata:

            fgdc_kwargs = {k: v for k,v in kwargs.iteritems()
                           if k not in ['start_datetime', 'end_datetime']}
            # can just include all remaining kwargs; no problem if they go unused
            fgdc_metadata = self.make_fgdc_metadata(file_name, config, model_run_uuid,
                                               kwargs['start_datetime'],
                                               kwargs['end_datetime'],
                                               **fgdc_kwargs)
            # print "\n\nfgdc_metadata***************************************",fgdc_metadata

        basename = os.path.basename(file_name)

        geo_config = config['Geo']

        firstTwoUUID = model_run_uuid[:2]
        input_file_path = os.path.join("/geodata/watershed-data",
                                     firstTwoUUID,
                                     model_run_uuid,
                                     os.path.basename(file_name))

        #properly escape xml metadata escape chars
        fgdc_metadata = fgdc_metadata.replace('\n', '\\n').replace('\t', '\\t')

        
        # fgdc_metadata.replace('\n', '')
        # fgdc_metadata.replace('\t', '')
        # print "\n\nfgdc_metadata------------------------------------",fgdc_metadata

        geoconf = config['Geo']
        resconf = config['Researcher']

        # if any of the bounding boxes are not given, all go to default
        if not ('west_bound' in kwargs and 'east_bound' in kwargs
                and 'north_bound' in kwargs and 'south_bound' in kwargs):
            kwargs['west_bound'] = geoconf['default_west_bound']
            kwargs['east_bound'] = geoconf['default_east_bound']
            kwargs['north_bound'] = geoconf['default_north_bound']
            kwargs['south_bound'] = geoconf['default_south_bound']

        # write the metadata for a file
        # output = template.substitute(# determined by file file_ext, set within function
        template_env = Environment(loader=FileSystemLoader(
                                   os.path.join(os.path.dirname(__file__),
                                                'templates')))

        template = template_env.get_template('watershed_template.json')


        if 'wcs' in kwargs and kwargs['wcs']:
            wcs_str = 'wcs'
        else:
            wcs_str = None

        if 'wms' in kwargs and kwargs['wms']:
            wms_str = 'wms'
        else:
            wms_str = None

        if kwargs['model_name'] == 'isnobal' and file_ext != 'tif':
            basename = basename
        else:
            basename = os.path.splitext(basename)[0]

        output = template.render(basename=basename,
                                 parent_model_run_uuid=parent_model_run_uuid,
                                 model_run_uuid=model_run_uuid,
                                 model_set=model_set,
                                 watershed_name=watershed_name,
                                 state=state,
                                 wcs_str=wcs_str,
                                 wms_str=wms_str,
                                 input_file_path=input_file_path,
                                 fgdc_metadata=fgdc_metadata,
                                 file_ext=file_ext,
                                 externaluserid = externaluserid,
                                 **kwargs) + '\n'

        # print '\n\n\n\n\nmake_watershed_metadata: \n\n\n\n', output
        return output

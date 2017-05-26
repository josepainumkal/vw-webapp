var converter = new showdown.Converter();

var ModelRun = React.createClass({
  

  getInitialState: function() {

   // console.log('success!',this.props.data.resources.length);
   var init_gstorePushFiles=[];
   for(var i=0;i<this.props.data.resources.length;i++){
       // console.log('onebyone!',this.props.data.resources[i].id);
       init_gstorePushFiles.push(parseInt(this.props.data.resources[i].id));
   }
   // console.log('init_gstorePushFiles!',init_gstorePushFiles);

    var runButton;
   
    if (this.props.data.progress_state=='NOT_STARTED') {
      runButton = <ReactBootstrap.Button
                            onClick={this.onRunClick}
                            bsSize="large" className="run-btn"
                            bsStyle="primary">Run Model</ReactBootstrap.Button>;
    }

    if(this.props.data.progress_state=='RUNNING' || this.props.data.progress_state=='QUEUED'){
      var btnClass = this.getButtonClass(this.props.data.progress_state);
      runButton = <ReactBootstrap.Button
                      bsSize="large" className="run-btn"
                      bsStyle={btnClass['class']}>
                      <i className={btnClass['iconClass']}></i>
                      {this.props.data.progress_state}
                  </ReactBootstrap.Button>;

    }

    return {
      id: this.props.data.id,
      isRunning:false,
      progressBars: null,
      progressButton: runButton,
      resources: this.props.data.resources,
      gstorePushFiles: init_gstorePushFiles,
      gstore_Pushed: this.props.data.gstore_Pushed,
      gpush_btn_text: 'Gstore-PUSH',
      gstore_id: this.props.data.gstore_id

    };
  },
  addFileToGstore: function(file){
    this.state.gstorePushFiles.push(parseInt(file))

    // this.setState({
    //     gstorePushFiles: this.state.gstorePushFiles.push(parseInt(file))
    // });
    // console.log('addFileToGstore_afterAdd!',this.state.gstorePushFiles);
  },
  deleteFileFromGstore: function(file){

    this.state.gstorePushFiles = jQuery.grep(this.state.gstorePushFiles, function(value) {return value != file; });
    // this.setState({ gstorePushFiles: temp });
    // console.log('deleteFileFromGstore:After_Delete!',this.state.gstorePushFiles);
    
  },
  getButtonClass: function(state){
    return modelrunApi.states_vars[state];
  },
  componentDidMount:function(){
     if(this.props.data.progress_state=='RUNNING' || this.props.data.progress_state=='QUEUED'){
       this.intervalId = setInterval(this.getProgress, 2000);
     }
  },
  componentWillUpdate: function(nextProps,nextState){

  },
  getProgress: function(){
    var progUrl = this.props.apiUrl+"modelruns/"+this.state.id;
    var intervalId = this.intervalId;
    $.ajax({
      url: progUrl,
      method:'GET',
      dataType: 'json',
      cache: false,
      success: function(response) {
        var modelrun = response;
        var progress_events = response['progress_events'];

        var btnClass = this.getButtonClass(modelrun.progress_state);
        this.setState({progressButton:<ReactBootstrap.Button bsSize="large" className="run-btn" bsStyle={btnClass['class']}>
                                        <i className={btnClass['iconClass']}></i> {modelrun.progress_state}
                                      </ReactBootstrap.Button>});
        this.setState({isRunning:true});
        this.updateProgressBar(progress_events);
        if(modelrun.progress_state=='FINISHED'){
          this.setState({isRunning:false});
          clearInterval(intervalId);
          this.updateResource();
        }
        else if(modelrun.progress_state=='ERROR'){
          this.setState({isRunning:false});
          clearInterval(intervalId);
        }
        this.props.onModelRunProgress();

      }.bind(this),
      error: function(xhr, status, err) {
        console.error(startUrl, status, err.toString());
      }.bind(this)
    });

  },
  updateResource: function(){
    var modelrunUrl = this.props.apiUrl+'modelruns/'+this.state.id;
    $.ajax({
      url: modelrunUrl,
      method:'GET',
      dataType: 'json',
      cache: false,
      success: function(modelrun) {
        this.setState({resources:modelrun['resources']});
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(startUrl, status, err.toString());
      }.bind(this)
    });

  },
  updateProgressBar: function(data){
    var progBars = [];
    if(data.length>0){
      for(var i=0;i<data.length;i++){
        var obj = data[i];
        var progVal = Math.floor(obj.progress_value);
        var active=false;
        if(progVal<100){
          var active=true;
        }
        var progBar = <ModelProgress active={active} progressVal={progVal} eventName={obj.event_name} eventDescription={obj.event_description} />;
        progBars.push(progBar);
        this.setState({progressBars:progBars});
      }
    }

  },

  onRunClick: function (event) {
    var startUrl  =this.props.url+"/"+this.props.data.id+"/start";
    $.ajax({
      url: startUrl,
      method:'PUT',
      dataType: 'json',
      cache: false,
      success: function(data) {
        var btnClass = this.getButtonClass('QUEUED');
        this.setState({isRunning:true});
        this.setState({progressButton:<ReactBootstrap.Button bsSize="large" className="run-btn" bsStyle={btnClass['class']}>
                                          <i className={btnClass['iconClass']}></i> QUEUED
                                        </ReactBootstrap.Button>});
        this.intervalId = setInterval(this.getProgress, 2000);

      }.bind(this),
      error: function(xhr, status, err) {
        console.error(startUrl, status, err.toString());
      }.bind(this)
    });

  },
  
  handleRemoveFromGstore: function(){
    var descision=confirm("\nAre you sure you want to remove the model from Gstore?");
    if(descision){
        $.ajax({
            url: '/remove_from_gstore',
            method: 'POST',
            dataType: 'json',
            cache: false,
            contentType: "application/json; charset=utf-8",
            data:JSON.stringify({
                model_id: this.state.id,
                gstore_id: this.state.gstore_id
            }),
            success: function(data) {

              var init_gstorePushFiles=[];
              for(var i=0;i<this.props.data.resources.length;i++){
                  //console.log('onebyone!',this.props.data.resources[i].id);
                  init_gstorePushFiles.push(parseInt(this.props.data.resources[i].id));
              }

                this.setState({ gstore_Pushed: 'false', gstorePushFiles: init_gstorePushFiles, gstore_id: null});

            }.bind(this),
            error: function(xhr, status, err) {
              console.error(url, status, err.toString());
            }.bind(this)
        }); 
    }
  },

  handlePushToGstore: function(){
    if(this.state.isRunning == 'true'){
      alert("\nSorry. Please wait for the model run to finish and then perform Gstore-PUSH");
      return;
    }
    
    if (this.state.gstorePushFiles.length ==0){
      alert("\nSorry. You have not chosen any of the resources. \n\n Use the checkbox to choose the resources you want to push to gstore.\n\n\n");
      return;
    }

    var descision=confirm("\nAre you sure you want to push the model to Gstore? This will take 1-3 minutes.\n\nThank you for your patience.\n\n\n");
    if(descision){
      this.setState({ gpush_btn_text: 'Please Wait...'});
      var url = '/push_to_gstore';

      $.ajax({
          url: url,
          method: 'POST',
          dataType: 'json',
          cache: false,
          contentType: "application/json; charset=utf-8",
          data:JSON.stringify({
              model_id: this.state.id,
              description: this.props.data.description,
              model_name: this.props.data.model_name,
              model_title: this.props.data.title,
              push_files:this.state.gstorePushFiles,
              resources: this.state.resources,
              gstore_Pushed: this.state.gstore_Pushed
          }),
          success: function(data) {
              var init_gstorePushFiles=[];
              for(var i=0;i<this.props.data.resources.length;i++){
                  //console.log('onebyone!',this.props.data.resources[i].id);
                  init_gstorePushFiles.push(parseInt(this.props.data.resources[i].id));
              }

              this.setState({ gstore_id: data.gstore_id, gstore_Pushed: 'true', gpush_btn_text: 'Gstore-PUSH', gstorePushFiles: init_gstorePushFiles});

              // this.setState({ });
              // this.setState({ });
              // this.updateResource(); 

              //


          }.bind(this),
          error: function(xhr, status, err) {
            console.error(url, status, err.toString());
          }.bind(this)
      }); 
    }

  },

  render: function() {
        var desc = converter.makeHtml(this.props.data.description);

        return (
          <div data-id="{this.props.data.id}" className="col-lg-12">
            <ReactBootstrap.Panel header={this.props.data.title}
              className="modelrun"  bsStyle="primary">
              <div className="col-lg-6">
                <ReactBootstrap.Table striped>
                <tbody>
                  <tr>
                    <td>Title</td>
                    <td> {this.props.data.title}</td>
                  </tr>
                  <tr>
                    <td>Model</td>
                    <td> {this.props.data.model_name}</td>
                  </tr>
                  <tr>
                    <td>Status</td>
                    <td> {this.props.data.progress_state}</td>
                  </tr>
                  {this.state.gstore_Pushed=='true'?(<tr><td>Gstore Id</td><td> {this.state.gstore_id}</td></tr>):null}
                  </tbody>
                </ReactBootstrap.Table>
                <div className="modelrundesc" >
                    <h4>Description</h4>
                     <div dangerouslySetInnerHTML={{__html: desc}} ></div>
                  </div>

                <ModelResourceList title='Resources' url={this.props.apiUrl} data={this.state.resources} addFileToGstore = {this.addFileToGstore}  deleteFileFromGstore = {this.deleteFileFromGstore}  modelPushed = {this.state.gstore_Pushed}></ModelResourceList>

                
                <ReactBootstrap.Table>
                <tbody>
                <tr>
                <td> <ReactBootstrap.Button onClick={this.props.onDelete} bsSize="small" className="run-btn" bsStyle="danger">Delete</ReactBootstrap.Button>
                </td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td>
                <td>
                {this.state.gstore_Pushed=='false'?
                 (<ReactBootstrap.Button onClick={this.handlePushToGstore} bsSize="small" bsStyle="success">{this.state.gpush_btn_text}</ReactBootstrap.Button>)
                 :(<ReactBootstrap.Button onClick={this.handleRemoveFromGstore} bsSize="small" bsStyle="warning">Gstore-Remove</ReactBootstrap.Button>)}
                </td>
                </tr>
                </tbody>
                </ReactBootstrap.Table>
                
                 
                <div className="logbox">
                  { this.props.data.logs && <h3>Logs</h3> }
                  { this.props.data.logs }
                </div>
              </div>
              <div ref="runBtn" className="col-lg-6 margin-bottom">
                {this.state.progressButton}
              </div>
              <div className="col-lg-6" ref="progressbarcontainer">
                {this.state.progressBars}
              </div>

            </ReactBootstrap.Panel>
          </div>
        );
  }
});

var ModelRunList = React.createClass({
  onDelete:function(modelrun) {
    if(this.refs[modelrun.id].state.isRunning){
      alert("You can't delete a run while model is running");
      return;
    }
    var descision=confirm("Are you sure you want to delete the model run?");
    if(descision){
      $.ajax({
        url: this.props.url+'/'+modelrun.id,
        type: 'DELETE',
        success: function(result) {
          window.location.reload(true);
        }
      });
    }


  },
  render: function() {
    var url = this.props.url;
    var apiUrl = this.props.apiUrl;
    var onModelRunProgress = this.props.onModelRunProgress;
    var modelrunNodes = this.props.data.map(function (modelrun) {
      return (
        <ModelRun key={modelrun.id} ref={modelrun.id} onDelete={this.onDelete.bind(this, modelrun)} onModelRunProgress={onModelRunProgress} apiUrl={apiUrl}  url={url} data={modelrun}>

        </ModelRun>
      );
    }.bind(this));
    return (
      <div className="modelrunList">
        {modelrunNodes}
      </div>
    );
  }
});


window.ModelRun=ModelRun;
window.ModelRunList=ModelRunList;

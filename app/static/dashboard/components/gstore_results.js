

var GstoreResult = React.createClass({
  

  getInitialState: function() {


    return {
      results: this.props.data
    };
  },

  render: function() {
        var services = [];
        var downloads = [];
        var outputfile_name =null;
    
    		for (var i=0,j=0; i < this.props.data.downloads.length; i++) {
              for(var propName in this.props.data.downloads[i]) {
                  if(this.props.data.downloads[i].hasOwnProperty(propName)) {
                      var propValue = this.props.data.downloads[i][propName];
                      // console.log("downloads: " +propValue);
                      outputfile_name = propValue.split('/').pop();
		      downloads.push(<div><a href={propValue} key={j}>{outputfile_name}</a></div>);
                      j=j+1;
                  }
              } 
		    }
        
        for (var i=0,j=0; i < this.props.data.services.length; i++) {
              for(var propName in this.props.data.services[i]) {
                  if(this.props.data.services[i].hasOwnProperty(propName)) {
                      var propValue = this.props.data.services[i][propName];
                      // console.log("services: " +propValue);
                      services.push(<div key={j}>{propValue}</div>);
                      j=j+1;
                  }
              } 
		    }


        return (
                                    
          <div className="col-lg-12">
            <ReactBootstrap.Panel  className="modelrun"  bsStyle="primary">
              <div className="col-lg-12">
                <ReactBootstrap.Table striped>
                <tbody>
                  <tr>
                    <td width="300">Modelrun Name</td>
                    <td> {this.props.data.model_run_name}</td>
                  </tr>
                  <tr>
                    <td>Description</td>
                    <td> {this.props.data.description}</td>
                  </tr>
                  <tr>
                    <td>Parent Model UUID</td>
                    <td> {this.props.data.parent_model_run_uuid}</td>
                  </tr>
                  <tr>
                    <td>Model Set</td>
                    <td> {this.props.data.model_set}</td>
                  </tr>
                  <tr>
                    <td>Taxonomy</td>
                    <td> {this.props.data.taxonomy}</td>
                  </tr>
                  <tr>
                    <td>Downloads</td>
                    <td> {downloads}</td>
                  </tr>
                 
                  </tbody>
                </ReactBootstrap.Table>
              </div>
             
            </ReactBootstrap.Panel>
          </div>
        );
  }
});




var GstoreResultsList = React.createClass({

  render: function() {
    var url = this.props.url;
    var apiUrl = this.props.apiUrl;
    var onModelRunProgress = this.props.onModelRunProgress;
    var modelrunNodes = this.props.data.map(function (result) {
      return (
        <GstoreResult key={result.id} ref={result.id} data={result}/>
      );
    }.bind(this));
    return (
      <div className="modelrunList">
        {modelrunNodes}
      </div>
    );
  }
});



window.GstoreResult=GstoreResult;
window.GstoreResultsList=GstoreResultsList;


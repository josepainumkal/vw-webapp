

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
          if(this.props.data.downloads[i].nc != null){
              outputfile_name = this.props.data.downloads[i].nc.split('/').pop();
              // console.log("download: " + output);
              downloads.push(<a href={this.props.data.downloads[i].nc} key={j}>{outputfile_name}</a>)
              j=j+1;
          }
          if(this.props.data.downloads[i].zip != null){   
              outputfile_name = this.props.data.downloads[i].zip.split('/').pop();
              downloads.push(<a href={this.props.data.downloads[i].zip} key={j}>{outputfile_name}</a>)
              j=j+1;
          }
          if(this.props.data.downloads[i].control != null){   
              outputfile_name = this.props.data.downloads[i].control.split('/').pop();
              downloads.push(<a href={this.props.data.downloads[i].control} key={j}>{outputfile_name}</a>)
              j=j+1;
          }
          if(this.props.data.downloads[i].txt != null){   
              outputfile_name = this.props.data.downloads[i].txt.split('/').pop();
              downloads.push(<a href={this.props.data.downloads[i].txt} key={j}>{outputfile_name}</a>)
              j=j+1;
          }
          if(this.props.data.downloads[i].png != null){   
              outputfile_name = this.props.data.downloads[i].png.split('/').pop();
              downloads.push(<a href={this.props.data.downloads[i].png} key={j}>{outputfile_name}</a>)
              j=j+1;
          }
          if(this.props.data.downloads[i].xml != null){   
              outputfile_name = this.props.data.downloads[i].xml.split('/').pop();
              downloads.push(<a href={this.props.data.downloads[i].xml} key={j}>{outputfile_name}</a>)
              j=j+1;
          }
          if(this.props.data.downloads[i].pdf != null){   
              outputfile_name = this.props.data.downloads[i].pdf.split('/').pop();
              downloads.push(<a href={this.props.data.downloads[i].pdf} key={j}>{outputfile_name}</a>)
              j=j+1;
          }
        }


        for (var i = 0,j=0; i < this.props.data.services.length; i++) {
          services.push(<div className='service' key={j}>{this.props.data.services[i].wms} </div>); 
            j=j+1;
          services.push(<div className='service' key={j}>{this.props.data.services[i].wcs} </div>);
           j=j+1;
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


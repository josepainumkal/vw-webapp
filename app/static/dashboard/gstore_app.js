
var ModelRunBox = React.createClass({
  getInitialState: function() {
    return {
      model_name:'',
      model_taxonomy:'',
      model_run_uuid:'',
      externaluserid:'',
      model_set:'',
      taxonomy:'',
      model_set_type:'',
      service:'',
      offset:'',
      dir:'',
      gstore_results:''

    }
  },

  handleModelNameChange: function(e) {
   this.setState({model_name: e.target.value});
  },
  handleModelTaxonomyChange: function(e) {
     this.setState({model_taxonomy: e.target.value});
  },
  handleModelUUIDChange: function(e) {
     this.setState({model_run_uuid: e.target.value});
  },
  handleExternalUserIdChange: function(e) {
     this.setState({externaluserid: e.target.value});
  },

  handleModelSetChange: function(e) {   
     // this.setState({model_set: e.target.value});
     this.setState({model_set: e.target.value });
  },
  handleTaxonomyChange: function(e) {
     this.setState({taxonomy: e.target.value});
  },
  handleSetTypeChange: function(e) {
     this.setState({model_set_type: e.target.value});
  },
  handleServiceChange: function(e) {
     this.setState({service: e.target.value});
  },
  handleDirChange: function(e) {
     this.setState({dir: e.target.value});
  },

  handleSubmit: function(e){
      console.log("model_name: " + this.state.model_name);
      console.log("model_taxonomy: " + this.state.model_taxonomy);     

      $.ajax({
        url: '/modeling/gstore/',
        method: 'GET',
        data: { 
        "model_name": this.state.model_name, 
        "model_set_taxonomy": this.state.model_taxonomy, 
        "model_run_uuid": this.state.model_run_uuid, 
        "externaluserid": this.state.externaluserid,
        "model_set": this.state.model_set,
        "taxonomy":this.state.taxonomy,
        "model_set_type": this.state.model_set_type,
        "service": this.state.service,
        "sort_order": this.state.dir,
        },
        dataType: 'json',
        cache: false,
        success: function(data) {
          console.log("data.total: " +data.total);
          console.log("data.results: " +data.results);
          this.setState({gstore_results: data.results});
        }.bind(this),
        error: function(xhr, status, err) {
          // console.error(this.props.url, status, err.toString());
        }.bind(this)
      });
  },
  componentDidMount: function(){
    this.handleSubmit();

  },

  render: function() {
     return (

        <div className="modlerunBox">
            
          <div className="col-lg-12">
              <h3 className="page-header">
                   Search in Gstore 
              </h3>

               <ReactBootstrap.Panel header="Select atleast one from below options to filter the results " className="modelrun"  bsStyle="danger">
                    <form id='search_queries'>
                        <div className='row'>
                            <div className='col-lg-2'>
                                  <label for="model_name" className="control-label">Model Name </label> 
                                  <input type="text" className="form-control input-sm" id="model_name" value={this.state.model_name} name="model_name" placeholder="prms / isnobal" onChange={this.handleModelNameChange}/>
                            </div>
                            <div className='col-lg-3'>
                                  <label for="model_run_uuid" className="control-label">Model Run UUID </label> 
                                  <input type="text" className="form-control input-sm" id="model_run_uuid"  value={this.state.model_run_uuid} name="model_run_uuid" placeholder="Gstore UUID" onChange={this.handleModelUUIDChange}/>
                            </div>
                            <div className='col-lg-2'>
                                  <label for="model_taxonomy" className="control-label">Model Set Taxonomy </label> 
                                  <select id="model_set" className="form-control input-sm" id="model_taxonomy" value={this.state.model_taxonomy}  onChange={this.handleModelTaxonomyChange}>
                                        <option value=""></option>
                                        <option value="grid">grid</option>
                                        <option value="vector">vector</option>
                                        <option value="file">file</option>
                                </select>

                            </div>

                            <div className='col-lg-3'>
                                  <label for="externaluserid" className="control-label">User UUID </label> 
                                  <input type="text" className="form-control input-sm" id="externaluserid" value={this.state.externaluserid} name="externaluserid" placeholder="User UUID" onChange={this.handleExternalUserIdChange}/>
                            </div>

                            <div className='col-md-2'>
                                <label for="model_set" className="control-label">Model Set </label> 
                                <select id="model_set" className="form-control input-sm" value={this.state.model_set}  onChange={this.handleModelSetChange}>
                                        <option value=""></option>
                                        <option value="inputs">inputs</option>
                                        <option value="outputs">outputs</option>
                                        <option value="reference">reference</option>
                                        <option value="analytics">analytics</option>     
                                </select>
                            </div>

                        </div><br/>
                        <div className='row'>

                             <div className='col-md-2'>
                                <label for="taxonomy" className="control-label">Taxonomy </label> 
                                <select id="taxonomy" className="form-control input-sm" value={this.state.taxonomy}  onChange={this.handleTaxonomyChange}>
                                        <option value=""></option>
                                        <option value="file">file</option>
                                        <option value="vector">vector</option>
                                        <option value="geoimage">geoimage</option>
                                        <option value="table">table</option>  
                                        <option value="service">service</option>   
                                </select>
                            </div>
                            <div className='col-md-2'>
                                <label for="model_set_type" className="control-label">Model Set Type </label> 
                                <select id="model_set_type" className="form-control input-sm" value={this.state.model_set_type}  onChange={this.handleSetTypeChange}>
                                        <option value=""></option>
                                        <option value="raw">raw</option>
                                        <option value="binary">binary</option>
                                        <option value="viz">viz</option>
                                </select>
                            </div>
                            <div className='col-md-2'>
                                <label for="service" className="control-label">Service </label> 
                                <select id="service" className="form-control input-sm" value={this.state.service}  onChange={this.handleServiceChange}>
                                        <option value=""></option>
                                        <option value="wms">wms</option>
                                        <option value="wfs">wfs</option>
                                        <option value="wcs">wcs</option>
                                </select>
                            </div>
                            <div className='col-md-2'>
                                <label for="dir" className="control-label">Sort </label> 
                                <select id="dir" className="form-control input-sm" value={this.state.dir}  onChange={this.handleDirChange}>
                                        <option value=""></option>
                                        <option value="ASC">ASC</option>
                                        <option value="DESC">DESC</option>
                                </select>
                            </div>
                            <div className='col-md-2'>  

                                  <ReactBootstrap.Button onClick={this.handleSubmit} bsSize="medium" bsStyle="success">Search-Gstore</ReactBootstrap.Button>
                            </div>
                        </div>
                  </form>
              </ReactBootstrap.Panel>
              <br/><br/>
              <div className="modleruns">
                  {this.state.gstore_results!=''? (<GstoreResultsList  data={this.state.gstore_results}/>):null}  
              </div>
          </div>
      </div>
    );
  }
});


window.ModelRunBox = ModelRunBox;


var ModelResource = React.createClass({
  getInitialState: function(){
    return {
      type:'',
      name:'',
      url:'',
      gstore_Pushed:''

    }
  },
  handleGstoreCheckbox: function(e){
  if(e.target.checked ){
    this.props.addToGstore(e.target.value);
    console.log('Added!',e.target.value);
  }else{
    this.props.deleteFromGstore(e.target.value);
    console.log('Deleted!',e.target.value);
  }
 
  },
  getResource: function(){
    var modelresourceUrl = this.props.url+'modelresources/'+this.props.id;
    $.ajax({
      url: modelresourceUrl,
      dataType: 'json',
      cache: false,
      success: function(data) {
          //console.log('success!',data);
        this.setState({
          name: data['resource_name'],
          url:data['resource_url'],
          type:data['resource_type'],
          gstore_Pushed:data['gstore_Pushed']
        });
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString());
      }.bind(this)
    });
  },
  componentDidMount: function(){
    this.getResource();
  },
  componentWillReceiveProps: function(){
    this.getResource();
  },
  render: function() {

    if(this.props.modelPushed=='false'){
          if(this.state.gstore_Pushed=='true'){
              return (
                          <tr>
                            <td>{this.state.type}</td>
                            <td><a href={this.state.url} className="">{this.state.name}</a></td>
                          </tr>
              );
          }
          else {
              return (
                      <tr>
                        <td>{this.state.type}</td>
                        <td><a href={this.state.url} className="">{this.state.name}</a></td>
                        <td><input type="checkbox" name="gstore_push" value={this.props.id} onChange={this.handleGstoreCheckbox}  defaultChecked/></td>
                      </tr>
              );
          }
    }else{
       // if the model is pushed 
       if(this.state.gstore_Pushed=='true'){
              return (
                          <tr>
                            <td>{this.state.type}</td>
                            <td><a href={this.state.url} className="">{this.state.name}</a></td>
                            <td><span className="glyphicon glyphicon-ok" ></span></td>
                          </tr>
              );
          }
          else {
              return (
                      <tr>
                        <td>{this.state.type}</td>
                        <td><a href={this.state.url} className="">{this.state.name}</a></td>
                        <td><span className="glyphicon glyphicon-remove"></span></td>
                      </tr>
              );
          }
    }
  }
});

var ModelResourceList = React.createClass({
  render: function() {
    var apiUrl = this.props.url;
    var modelResourceNodes = this.props.data.map(function (modelresource) {
      return (
        <ModelResource key={modelresource.id} url={apiUrl} id={modelresource.id} addToGstore={this.props.addFileToGstore} deleteFromGstore={this.props.deleteFileFromGstore} modelPushed={this.props.modelPushed}></ModelResource>
      );
    }, this);
    return (
      <div className="model-resouces">
          <h4>{this.props.title}</h4>
          <ReactBootstrap.Table striped>
            <tbody>
            {modelResourceNodes}
            </tbody>
          </ReactBootstrap.Table>
      </div>
    );
  }
});

window.ModelResource=ModelResource
window.ModelResourceList=ModelResourceList

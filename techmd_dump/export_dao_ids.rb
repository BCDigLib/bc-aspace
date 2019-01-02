require 'rest-client'
require 'yaml'
require 'json'

@conf = YAML::load_file(File.join(__dir__, 'config.yml'))

auth_resp = RestClient::Request.execute(method: :post, 
                                       url: @conf["aspace_base_uri"] + '/users/admin/login',
                                       payload: { password: @conf["aspace_password"] }
)
auth_resp_serialized = JSON.parse(auth_resp)
@session_id = auth_resp_serialized["session"]

def get_record(uri_suffix)
  endpoint = @conf["aspace_base_uri"] + uri_suffix
  response = RestClient.get(endpoint, {"X-ArchivesSpace-Session": @session_id})
  JSON.parse(response)
end

resource_id = ARGV[0]
resource_tree_suffix = '/repositories/2/resources/' + resource_id + '/tree'

tree = get_record(resource_tree_suffix)
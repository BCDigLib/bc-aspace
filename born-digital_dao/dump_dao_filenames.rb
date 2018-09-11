# Outputs a CSV of DO component filenames and AO component unique IDs for a 
# given resource. Takes a resource ID as input and requires a YAML file that 
# includes some basic configuration info (see example_config.yml).

require 'json'
require 'csv'
require 'yaml'
require 'rest-client'

conf = YAML::load_file(File.join(__dir__, 'config.yml'))

resource_id = ARGV[0]

if ARGV[0].to_i == 0
  puts "Usage: ruby dump_dao_filenames.rb aspace_resource_id"
  exit
end

auth_resp = RestClient::Request.execute(method: :post, 
                                       url: conf["aspace_base_uri"] + '/users/admin/login',
                                       payload: { password: conf["aspace_password"] }
)
auth_resp_serialized = JSON.parse(auth_resp)
session_id = auth_resp_serialized["session"]

endpoint = conf["aspace_base_uri"] + "/repositories/" + conf["aspace_repo_id"] + "/resources/" + resource_id + "/tree"
response = RestClient.get(endpoint, {"X-ArchivesSpace-Session": session_id})
resource_tree = JSON.parse(response)


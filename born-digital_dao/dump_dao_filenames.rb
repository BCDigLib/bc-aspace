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

resource_endpoint = conf["aspace_base_uri"] + "/repositories/" + conf["aspace_repo_id"] + "/resources/" + resource_id + "/tree"
resource_response = RestClient.get(resource_endpoint, {"X-ArchivesSpace-Session": session_id})
resource_tree = JSON.parse(resource_response)

ao_suffixes = resource_tree["children"].map { |child| child["record_uri"] if child["instance_types"].include?("digital_object") }
ao_suffixes.compact!.reject! { |el| el.empty? }
ao_endpoints = ao_suffixes.map! { |suffix| conf["aspace_base_uri"] + suffix }

fnames = []
component_fnames = {}

ao_endpoints.each do |ao_endpoint|
  ao_response = RestClient.get(ao_endpoint, {"X-ArchivesSpace-Session": session_id})
  ao = JSON.parse(ao_response)
  ao_component_id = ao["component_id"]

  do_instance = ao["instances"].select { |instance| instance["instance_type"] == "digital_object" }[0]
  do_suffix = do_instance["digital_object"]["ref"]
  do_tree_endpoint = conf["aspace_base_uri"] + do_suffix + "/tree"
  do_tree_response = RestClient.get(do_tree_endpoint, {"X-ArchivesSpace-Session": session_id})
  do_tree = JSON.parse(do_tree_response)
  do_tree["children"].each { |child| child["file_versions"].map { |file_version| fnames << file_version["file_uri"] } }

  component_fnames[ao_component_id] = fnames
end


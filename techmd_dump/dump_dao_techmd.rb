# Outputs a CSV of techmd note fields for digital object components. 
# Takes as input a text file containing a list of digital object IDs 
# and requires a config file (see example_config.yml).

require 'json'
require 'csv'
require 'yaml'
require 'rest-client'

conf = YAML::load_file(File.join(__dir__, 'config.yml'))

auth_resp = RestClient::Request.execute(method: :post, 
                                       url: conf["aspace_base_uri"] + '/users/admin/login',
                                       payload: { password: conf["aspace_password"] }
)
auth_resp_serialized = JSON.parse(auth_resp)
session_id = auth_resp_serialized["session"]

begin
  input_ids = File.readlines(ARGV[0]).collect(&:strip)
  test_endpoint = conf["aspace_base_uri"] + "/repositories/" + conf["aspace_repo_id"] + "/digital_objects/" + input_ids.first + "/tree"
  test_response = RestClient.get(test_endpoint, {"X-ArchivesSpace-Session": session_id})
  test_tree = JSON.parse(test_response)
rescue
  puts "Requires an input file of digital object IDs."
  puts "Sample usage: ruby dump_dao_techmd.rb do_ids.txt"
  puts ""
  exit
end

do_component_uris = []

input_ids.each do |id|
  do_tree_endpoint = conf["aspace_base_uri"] + "/repositories/" + conf["aspace_repo_id"].to_s + "/digital_objects/" + id + "/tree"
  do_tree_response = RestClient.get(do_tree_endpoint, {"X-ArchivesSpace-Session": session_id})
  do_tree = JSON.parse(do_tree_response)

  do_component_uris << do_tree["children"].map { |child| child["record_uri"] }
end

do_components_techmd = []

do_component_uris.flatten.each do |uri|
  do_component_endpoint = conf["aspace_base_uri"] + uri
  do_component_response = RestClient.get(do_component_endpoint, {"X-ArchivesSpace-Session": session_id})
  do_component = JSON.parse(do_component_response)

  do_component_title = do_component["title"]
  do_component_id = do_component["uri"].split('/').last
  do_id = do_component["digital_object"]["ref"].split('/').last

  file_version = do_component["file_versions"].select { |file_version| file_version["use_statement"] == "master" }[0]
  file_uri = file_version["file_uri"]
  file_size_bytes = file_version["file_size_bytes"]
  checksum = file_version["checksum"]
  file_format_name = file_version["file_format_name"]

  techmd = do_component["notes"].map { |note| note["content"][0] }
  techmd << file_uri
  techmd << file_size_bytes
  techmd << checksum
  techmd << file_format_name

  techmd.unshift(do_component_title)
        .unshift(do_component_id)
        .unshift(do_id)

  do_components_techmd << techmd
end

CSV.open("do_components_techmd.csv", "wb") do |csv|
  csv << ["digital_object_id", "component_id", "component_label", "pixel_dimensions", 
          "resolution", "bits_per_sample", "color_space", "file_uri", "file_size_bytes", 
          "checksum", "file_format_name"]
  do_components_techmd.each { |techmd| csv << techmd }
end

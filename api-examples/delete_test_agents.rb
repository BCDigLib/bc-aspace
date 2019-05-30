# Just a little script to batch delete agents. Used for testing Brooker and 
# Hanvey batch imports.

require 'json'
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
  test_endpoint = conf["aspace_base_uri"] +  "/agents/people/" + input_ids.first
  test_response = RestClient.get(test_endpoint, {"X-ArchivesSpace-Session": session_id})
rescue
  puts test_endpoint
  puts test_response
  puts "Requires an input file of agent IDs."
  puts "Sample usage: ruby dump_dao_techmd.rb agent_ids.txt"
  puts ""
  exit
end

input_ids.each do |id|
  endpoint = conf["aspace_base_uri"] + "/agents/people/" + id
  response = RestClient.delete(endpoint, {"X-ArchivesSpace-Session": session_id})
  puts delete_response
end

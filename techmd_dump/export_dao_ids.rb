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

begin
  resource_id = ARGV[0]
  resource_tree_suffix = '/repositories/2/resources/' + resource_id + '/tree'
  resource_tree = get_record(resource_tree_suffix)
  resource_title = resource_tree["title"].gsub(/ /, '_')
rescue
  puts "Requires a resource ID (database primary key)."
  puts "Sample usage: ruby export_dao_ids.rb 250"
  puts ""
end

archival_object_refs = []
digital_object_refs = []

resource_tree["children"].map do |child|
  if child["has_children"] == true
    child["children"].map do |child|
      archival_object_refs << child["record_uri"] if child["instance_types"].include?("digital_object")
      if child["has_children"] == true
        child["children"].map do |child|
          archival_object_refs << child["record_uri"] if child["instance_types"].include?("digital_object")
          if child["has_children"] == true
            child["children"].map do |child|
              archival_object_refs << child["record_uri"] if child["instance_types"].include?("digital_object")
              if child["has_children"] == true
                child["children"].map do |child|
                  archival_object_refs << child["record_uri"] if child["instance_types"].include?("digital_object")
                  if child["has_children"] == true
                    child["children"].map do |child|
                      archival_object_refs << child["record_uri"] if child["instance_types"].include?("digital_object")
                    end
                  end
                end
              end
            end
          end
        end
      end
    end
  end
end

archival_object_refs.map do |ref|
  archival_object = get_record(ref)
  archival_object["instances"].map { |instance| digital_object_refs << instance["digital_object"]["ref"] if instance["instance_type"] == "digital_object" }
end

digital_object_ids = digital_object_refs.map { |ref| ref.split('/').last }

output = File.new("#{resource_title}.txt", "w")

digital_object_ids.each do |id|
  output.write(id)
  output.write("\n")
end

output.close
require 'rest-client'
require 'yaml'

conf = YAML::load_file(File.join(__dir__, 'config.yml'))

auth_resp = RestClient::Request.execute(method: :post, 
                                       url: conf["aspace_base_uri"] + '/users/admin/login',
                                       payload: { password: conf["aspace_password"] }
)
auth_resp_serialized = JSON.parse(auth_resp)
session_id = auth_resp_serialized["session"]


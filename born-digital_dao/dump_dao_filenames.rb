# Outputs a list of DO component filenames and AO component unique IDs for a 
# given resource. Takes a resource ID as input and requires a YAML config file 
# that includes credentials for an ASpace user with read access.

require 'json'
require 'csv'
require 'yaml'

conf = YAML::load_file(File.join(__dir__, 'config.yml'))
username = conf["aspace_username"]
password = conf["aspace_password"]

resource_id = ARGV[0]

if ARGV[0].to_i == 0
  puts "Usage: ruby dump_dao_filenames.rb"
  exit
end


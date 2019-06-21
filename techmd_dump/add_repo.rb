require 'yaml'
require 'csv'

input_tsv = CSV.read('av_aos_without_daos.tsv', col_sep: "\t", liberal_parsing: true)

input_tsv.each do |row|
  next if row[2] == 'identifier'
  id_arr = YAML.load(row[2])
  if id_arr[0] == ('IM' || 'IMC')
    id_arr[0] = "IMA"
  else
    id_arr[0] = "AMD"
  end
end

input_tsv[0][2] = "dept"

CSV.generate(col_sep: "\t", liberal_parsing: true) { |output_tsv| output_tsv << input_tsv }
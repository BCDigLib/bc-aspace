require 'time'

class METSSerializer < ASpaceExport::Serializer 
  serializer_for :mets

  private

  def mets(data, xml, dmd = "mods")
    xml.mets('xmlns' => 'http://www.loc.gov/METS/', 
             'xmlns:mods' => 'http://www.loc.gov/mods/v3', 
             'xmlns:dc' => 'http://purl.org/dc/elements/1.1/', 
             'xmlns:xlink' => 'http://www.w3.org/1999/xlink',
             'xmlns:xsi' => "http://www.w3.org/2001/XMLSchema-instance",
             'xsi:schemaLocation' => "http://www.loc.gov/METS/ http://www.loc.gov/standards/mets/mets.xsd"){
      xml.metsHdr(:CREATEDATE => Time.now.iso8601) {
        xml.agent(:ROLE => data.header_agent_role, :TYPE => data.header_agent_type) {
          xml.name data.header_agent_name
          data.header_agent_notes.each do |note|
            xml.note note
          end
        }        
      }

      xml.dmdSec(:ID => data.dmd_id) {
        if dmd == 'mods'
          xml.mdWrap(:MDTYPE => 'MODS') {
            xml.xmlData {
              ASpaceExport::Serializer.with_namespace('mods', xml) do
                mods_serializer = ASpaceExport.serializer(:mods).new
                mods_serializer.serialize_mods(data.mods_model, xml)
              end
            }
          }          
        elsif dmd == 'dc'
          xml.mdWrap(:MDTYPE => 'DC') {
            xml.xmlData {
              ASpaceExport::Serializer.with_namespace('dc', xml) do
                dc_serializer = ASpaceExport.serializer(:dc).new
                dc_serializer.serialize_dc(data.dc_model, xml)
              end
            }
          }
        end
      }

      data.children.each do |component_data|
        serialize_child_dmd(component_data, xml, dmd)
      end

      xml.amdSec {
        
      }

      xml.fileSec { 
        data.with_file_groups do |file_group|
          xml.fileGrp(:USE => file_group.use) {
            file_group.with_files do |file|
              xml.file(:ID => file.id, :GROUPID => file.group_id) {
                xml.FLocat("xlink:href" => file.uri)
              }
            end
          }
        end
      }

      xml.structMap(:TYPE => 'logical') {
        serialize_logical_div(data.root_logical_div, xml)
      }

      xml.structMap(:TYPE => 'physical') {
        serialize_physical_div(data.root_physical_div, xml)
      }
    }
  end

end

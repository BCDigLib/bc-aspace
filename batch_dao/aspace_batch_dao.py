# modified version of the script written by the Bentley Historical Library to automatically create Digital Objects by
# re-using archival object metadata in ArchivesSpace. Original script available at
# https://github.com/djpillen/bentley_scripts/blob/master/update_archival_object.py
# this script recreates the first steps in using a csv to locate archival objects and retrieve their metadata,
# but adds additional project-dependant metadata before creating the Digital Object, and creates Digital Object
# Components to hang file information off of rather than attaching files directly to the Digital Object.
# Also imports technical metadata from an exif file and stores it on the pertinent Digital Object Components.
# METS exports for every created Digital Object are also saved off in a folder labeled "METS".

# USAGE: |aspace_batch_dao.py tab_file.txt fits_file.csv| where tab_file.txt is the output of aspace_ead_to_tab.xsl
# and fits_file.csv is provided by the Digital Preservation Librarian and meets the specifications listed in the readme.

import requests
import json
import sys
import os


def main():
    # set up some variables
    # aspace access
    aspace_url = 'http://xxxxxx'
    username = 'xxxxxx'
    password = 'xxxxxx'
    # the following group are based on assumptions and may need to be changed project-to-project.
    format_note = "reformatted digital"
    file_type = "image/tiff"
    # open the exif file and read its contents into a dictionary that can be accessed to add techMD to digital
    # object components as they are built. If the dictionary fails to build, end process with an error indicating
    # the exif file is invalid.
    tech_struct = dict()
    techmd_file = sys.argv[2]
    tech_in = open(techmd_file, 'r')
    tech_data = tech_in.read()
    tech_lines = tech_data.splitlines()
    for line in tech_lines:
        fields = line.split('\t')
        if "format" not in fields[0]:
            if fields[1] not in tech_struct:
                try:
                    tech_struct[fields[1]] = [fields[0], fields[2], fields[3], fields[4], fields[5], fields[6],
                                              fields[7], fields[8], fields[9], fields[10]]
                except IndexError:
                    print("Exif file missing one or more values for " + fields[1] + ". Please check exif file and"
                                " try again.")
                    sys.exit()
    # use the tab file created with aspace_ead_to_tab.xsl to gather variables and make the API calls
    # tab_file = 'output.txt'
    tab_file = sys.argv[1]
    tab_in = open(tab_file, 'r')
    ead_data = tab_in.read()
    ead_lines = ead_data.splitlines()
    # make file to save IDs in for IIIF manifest generator
    ids_for_manifest = open('ids_for_manifest.txt', 'w')
    for line in ead_lines:
        # data from the file
        metadata = line.split("\t")
        use_note = metadata[3]
        dimensions_note = "1 " + metadata[2]
        aspace_id = metadata[1]
        id_ref = aspace_id[7:len(aspace_id)]
        collection_dates = metadata[4].split("/")
        lang_code = metadata[5]
        genre = metadata[6]
        type_of_resouce = metadata[7]
        # aspace login info
        auth = requests.post(aspace_url + '/users/' + username + '/login?password=' + password).json()
        session = auth['session']
        headers = {'X-ArchivesSpace-Session': session}
        params = {'ref_id[]': id_ref}
        lookup = requests.get(aspace_url + '/repositories/2/find_by_id/archival_objects', headers=headers, params=params).json()
        archival_object_uri = lookup['archival_objects'][0]['ref']
        archival_object_json = requests.get(aspace_url + archival_object_uri, headers=headers).json()
        # check for necessary metadata & only proceed if it's all present.
        print(archival_object_json)
        try:
            unique_id = archival_object_json['component_id']
        except KeyError:
            print("Please make sure all items have a component unique ID before creating DAOs")
            sys.exit()
        try:
            obj_title = archival_object_json['title']
        except KeyError:
            try:
                obj_title = archival_object_json['dates'][0]['expression']
            except KeyError:
                print("Item " + unique_id + " has no title or date expression. Please check the metadata & try again")
                sys.exit()
        try:
            agent_data = archival_object_json['linked_agents']
        except KeyError:
            agent_data = []
        # check for expression type 'single' before looking for both start and end dates
        date_json = create_date_json(archival_object_json, unique_id, collection_dates)
        # make the JSON
        dig_obj = {'jsonmodel_type':'digital_object','title':obj_title, 'digital_object_type':
                get_resource_type(type_of_resouce, id_ref), 'language': lang_code,
                'digital_object_id': 'http://hdl.handle.net/2345.2/' + unique_id, 'publish': True, 'notes':[{'content':
                [use_note], 'type':'userestrict', 'jsonmodel_type':'note_digital_object'},{'content':[dimensions_note],
                'type':'dimensions', 'jsonmodel_type':'note_digital_object'}, {'content':[format_note], 'type':'note','jsonmodel_type':'note_digital_object'},
                {'content':[file_type], 'type':'note', 'jsonmodel_type':'note_digital_object'}], 'dates':date_json,
                'linked_agents':agent_data, 'subjects': get_genre_type(genre)}
        # format the JSON
        dig_obj_data = json.dumps(dig_obj)
        # Post the digital object
        dig_obj_post = requests.post(aspace_url + '/repositories/2/digital_objects', headers=headers, data=dig_obj_data).json()
        print(dig_obj_post)
        # Grab the digital object uri and only proceed if the DO hasn't already been created
        try:
            dig_obj_uri = dig_obj_post['uri']
        except KeyError:
            print("DO for item " + unique_id + " already exists. Moving to next item in list.")
            continue
        # save off the ID of the newly created Digital object to feed the IIIF manifest generator
        id_start = dig_obj_uri.rfind('/')
        dig_ob_id = dig_obj_uri[(id_start+1):len(dig_obj_uri)]
        ids_for_manifest.write(dig_ob_id + '\n')
        # Build a new instance to add to the archival object, linking to the digital object
        dig_obj_instance = {'instance_type': 'digital_object', 'digital_object': {'ref': dig_obj_uri}}
        # Append the new instance to the existing archival object record's instances
        archival_object_json['instances'].append(dig_obj_instance)
        archival_object_data = json.dumps(archival_object_json)
        # Repost the archival object
        archival_object_update = requests.post(aspace_url + archival_object_uri, headers=headers, data=archival_object_data).json()
        print(archival_object_update)
        # find and open the component file to get the data to create digital object components. assumes files in the same
        # directory that include the ref_id in the filename and contain a list of all image files associated with the object
        files_list = os.listdir('.')
        for components_file in files_list:
            if unique_id in components_file:
                infile = open(components_file, 'r')
                contents = infile.read()
                file_names = contents.splitlines()
                for name in file_names:
                    lab_val = "Master"
                    if "INT" in name:
                        lab_val = "Intermediate"
                    period_loc = name.index('.')
                    base_name = name[0:period_loc]
                    dig_obj = {'jsonmodel_type': 'digital_object_component', 'publish': False, 'label': lab_val,
                               'file_versions':build_comp_file_version(name, tech_struct), 'title': base_name,
                               'display_string': name, 'notes': build_comp_exif_notes(name, tech_struct),
                               'digital_object': {'ref': dig_obj_uri}}
                    dig_obj_data = json.dumps(dig_obj)
                    print(dig_obj_data)
                    # Post the digital object component
                    dig_obj_post = requests.post(aspace_url + '/repositories/2/digital_object_components', headers=headers,
                                             data=dig_obj_data).json()
                    print(dig_obj_post)
                    if "invalid_object" in dig_obj_post:
                        print("Whoops, you tried to post an invalid object! Check your error logs and try again")
                        sys.exit()
        # create the mets call URI by modifying the digital object uri
        id_start = dig_obj_uri.rfind('/')
        mets_uri = dig_obj_uri[0:id_start] + '/mets' + dig_obj_uri[id_start:len(dig_obj_uri)] + '.xml'
        # Save off the METS export for the completed and fully component-laden Digital Object
        mets_call = requests.get(aspace_url + mets_uri, headers=headers)
        mets_file = mets_call.text
        if not os.path.exists('METS'):
            os.makedirs('METS')
        with open('METS/' + unique_id + '.xml', 'w') as outfile:
            outfile.write(mets_file)
        outfile.close()


# put date json creation in a separate function because different types need different handling.
def create_date_json(jsontext, itemid, collection_dates):
    if "single" in jsontext['dates'][0]['date_type']:
        try:
            start_date = jsontext['dates'][0]['begin']
        except KeyError:
            print(
                "Item " + itemid + " has a single-type date with no start value. Please check the metadata & try again")
            sys.exit()
        try:
            expression = jsontext['dates'][0]['expression']
        except KeyError:
            expression = start_date
        date_json = [{'begin':start_date, 'date_type':'single', 'expression':expression, 'label':'creation', 'jsonmodel_type':'date'}]
        return date_json
    elif "single" not in jsontext['dates'][0]['date_type']:
        date_type = jsontext['dates'][0]['date_type']
        try:
            start_date = jsontext['dates'][0]['begin']
        except KeyError:
            try:
                expression = jsontext['dates'][0]['expression']
            except KeyError:
                print(itemid + " has no start date or date expression. Please check the metadata and try again.")
                sys.exit()
            if "undated" in expression:
                start_date = collection_dates[0]
                end_date = collection_dates[1]
                date_json = [{'begin': start_date, 'end': end_date, 'date_type': date_type, 'expression': expression,
                              'label': 'creation', 'jsonmodel_type': 'date'}]
                return date_json
            else:
                print(itemid + " has no start date and date expression is not 'undated'. Please check the metadata "
                               "and try again")
                sys.exit()
        try:
            end_date = jsontext['dates'][0]['end']
        except KeyError:
            print("Item " + itemid + " has no end date. Please check the metadata & try again")
            sys.exit()
        try:
            expression = jsontext['dates'][0]['expression']
        except KeyError:
            if end_date in start_date:
                expression = start_date
            else:
                expression = start_date + "-" + end_date
        date_json = [{'begin':start_date, 'end':end_date, 'date_type':date_type, 'expression':expression, 'label':'creation', 'jsonmodel_type':'date'}]
        return date_json


# Sets an Aspace instance type for the DAO based on the typeOfResource assigned in the EAD-to-tab XSL
def get_resource_type(instance_type, item_id):
    print(instance_type)
    if instance_type == "text":
        return "text"
    elif instance_type == "cartographic":
        return "cartographic"
    elif instance_type == "notated music":
        return "notated_music"
    elif instance_type == "sound recording":
        return "sound_recording"
    elif instance_type == "sound recording-musical":
        return "sound_recording_musical"
    elif instance_type == "sound recording-nonmusical":
        return "sound_recording_nonmusical"
    elif instance_type == "still image":
        return "still_image"
    elif instance_type == "moving image":
        return "moving_image"
    elif instance_type == "three dimensional object":
        return "three dimensional object"
    elif instance_type == "software, multimedia":
        return "software_multimedia"
    elif instance_type == "mixed material":
        return "moving_image"
    else:
        print(item_id + " has an improperly formatted Digital Commonwealth typeOfResource. Please check the metadata & try again.")
        sys.exit()


# Sets a linked subject for the DAO to hold the Digital Commonwealth genre term based on the value set in the EAD-to-tab
# XSL. This mapping is based on database IDs for subjects in BC's production Aspace server and WILL NOT WORK for other
# schools/servers.
def get_genre_type(dc_genre_term):
    if dc_genre_term == "Albums":
        return [{"ref": "/subjects/656"}]
    elif dc_genre_term == "Books":
        return [{"ref": "/subjects/657"}]
    elif dc_genre_term == "Cards":
        return [{"ref": "/subjects/658"}]
    elif dc_genre_term == "Correspondence":
        return [{"ref": "/subjects/669"}]
    elif dc_genre_term == "Documents":
        return [{"ref": "/subjects/659"}]
    elif dc_genre_term == "Drawings":
        return [{"ref": "/subjects/660"}]
    elif dc_genre_term == "Ephemera":
        return [{"ref": "/subjects/661"}]
    elif dc_genre_term == "Manuscripts":
        return [{"ref": "/subjects/655"}]
    elif dc_genre_term == "Maps":
        return [{"ref": "/subjects/662"}]
    elif dc_genre_term == "Motion pictures":
        return [{"ref": "/subjects/668"}]
    elif dc_genre_term == "Music":
        return [{"ref": "/subjects/670"}]
    elif dc_genre_term == "Musical notation":
        return [{"ref": "/subjects/671"}]
    elif dc_genre_term == "Newspapers":
        return [{"ref": "/subjects/672"}]
    elif dc_genre_term == "Objects":
        return [{"ref": "/subjects/673"}]
    elif dc_genre_term == "Paintings":
        return [{"ref": "/subjects/663"}]
    elif dc_genre_term == "Periodicals":
        return [{"ref": "/subjects/664"}]
    elif dc_genre_term == "Photographs":
        return [{"ref": "/subjects/665"}]
    elif dc_genre_term == "Posters":
        return [{"ref": "/subjects/666"}]
    elif dc_genre_term == "Prints":
        return [{"ref": "/subjects/667"}]
    elif dc_genre_term == "Sound recordings":
        return [{"ref": "/subjects/674"}]
    else:
        print(dc_genre_term + " is an invalid or improperly formatted genre term. Please check the Digital Commonwealth"
                              " documentation and try again.")
        sys.exit()


# builds a [file version] segment for the Digital object component json that contains appropriate tech metadata from the
# FITS file. HARD CODED ASSUMPTIONS: Checksum type = MD5
def build_comp_file_version(filename, techmd_dict):
    check_value = techmd_dict[filename][2]
    size = int(techmd_dict[filename][1])
    format_type = get_format_enum(techmd_dict[filename][0])
    use_statement = "master"
    if "INT" in filename:
        use_statement = "intermediate_copy"
    blob = [{'file_uri': filename, 'use_statement': use_statement, 'file_size_bytes': size, 'checksum_method': 'md5',
             'checksum': check_value, 'file_format_name': format_type, 'jsonmodel_type': 'file_version'}]

    return blob


# translation table/function to turn FITS-reported file formats into ASpace enums
def get_format_enum(fits):
    filetype= ""
    if "TIFF" in fits:
        filetype = "tiff"
    if "Waveform" in fits:
        filetype = "wav"
    if "RF64" in fits:
        filetype = "rf64"
    return filetype


# builds the notes section for the digital object component where techMD that can't live on the file version is stored.
# not all components have all metadata, so is not None tests are needed for every field.
def build_comp_exif_notes(filename, techmd_dict):
    note_list = []
    if len(techmd_dict[filename][3]) > 0:
        note_list.append(note_builder(techmd_dict[filename][3], 'duration'))
    if len(techmd_dict[filename][4]) > 0:
        note_list.append(note_builder(techmd_dict[filename][4], 'sample rate'))
    if len(techmd_dict[filename][5]) > 0:
        note_list.append(note_builder(techmd_dict[filename][5], 'bit depth'))
    if len(techmd_dict[filename][6]) > 0:
        note_list.append(note_builder(techmd_dict[filename][5], 'pixel dimensions'))
    if len(techmd_dict[filename][7]) > 0:
        note_list.append(note_builder(techmd_dict[filename][5], 'resolution'))
    if len(techmd_dict[filename][8]) > 0:
        note_list.append(note_builder(techmd_dict[filename][5], 'bits per sample'))
    if len(techmd_dict[filename][9]) > 0:
        note_list.append(note_builder(techmd_dict[filename][5], 'color space'))
    return note_list


def note_builder(list_index, label_value):
    note_text = {'jsonmodel_type':'note_digital_object', 'publish':False, 'content':[list_index], 'type':'note',
                 'label':label_value}
    return note_text


main()

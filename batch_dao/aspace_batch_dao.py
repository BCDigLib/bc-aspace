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
    # open the fits file and read in its contents. This dictionary is used for techMD calls, also create another dict
    # for file lists.
    files_listing = dict()
    techmd_file = sys.argv[2]
    tech_in = open(techmd_file, 'r')
    tech_data = json.load(tech_in)
    for key, values in tech_data.items():
        # integer in the line below may need updating for items with differently formatted CUIs
        cutoff = key.replace('_', "|", 2).find('_')
        short_name = key[0:cutoff]
        if short_name not in files_listing:
            files_listing[short_name] = [key]
        elif short_name in files_listing:
            files_listing[short_name].append(key)
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
                get_resource_type(archival_object_json, id_ref), 'language': lang_code,
                'digital_object_id': 'http://hdl.handle.net/2345.2/' + unique_id, 'publish': True, 'notes':[{'content':
                [use_note], 'type':'userestrict', 'jsonmodel_type':'note_digital_object'},{'content':[dimensions_note],
                'type':'dimensions', 'jsonmodel_type':'note_digital_object'}, {'content':[format_note], 'type':'note','jsonmodel_type':'note_digital_object'},
                {'content':[get_file_type(files_listing[unique_id][0])], 'type':'note', 'jsonmodel_type':'note_digital_object'}], 'dates':date_json,
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
        # pull in files list from dictionary to get data to create digital object components.
        file_names = files_listing[unique_id]
        file_names.sort()
        for name in file_names:
            period_loc = name.index('.')
            base_name = name[0:period_loc]
            dig_obj = {'jsonmodel_type': 'digital_object_component', 'publish': False, 'label': base_name,
                        'file_versions':build_comp_file_version(name, tech_data), 'title': base_name,
                        'display_string': name, 'digital_object': {'ref': dig_obj_uri}}
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


# Sets an Aspace instance type for the DAO based on the physical instance of the AO
def get_resource_type(ao_json, item_id):
    instance_type = ""
    for instance in ao_json['instances']:
        if 'digital' in instance['instance_type']:
            pass
        else:
            instance_type = instance['instance_type']
            break
    if instance_type == "text" or instance_type == "books":
        return "text"
    elif instance_type == "maps":
        return "cartographic"
    elif instance_type == "notated music":
        return "notated_music"
    elif instance_type == "audio":
        return "sound_recording"
    elif instance_type == "graphic_materials" or instance_type == "photo":
        return "still_image"
    elif instance_type == "moving_images":
        return "moving_image"
    elif instance_type == "realia":
        return "three dimensional object"
    elif instance_type == "mixed_materials":
        return "mixed_materials"
    else:
        print(item_id + " can't be assigned a typeOfResource based on the physical istance. Please check the metadata & try again.")
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
    check_value = techmd_dict[filename]['checksum']
    size = int(techmd_dict[filename]['filesize'])
    format_type = get_format_enum(techmd_dict[filename]['format'])
    use_statement = "master"
    if "INT" in filename:
        use_statement = "intermediate_copy"
    elif "ACC" in filename:
        use_statement = "access_copy"
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
    if "Quicktime" in fits:
        filetype = "mov"
    if "Microsoft Word Binary File Format" in fits:
        filetype = "doc"
    if "Office Open XML Document" in fits:
        filetype = "docx"
    return filetype


# builds the notes section for the digital object component where techMD that can't live on the file version is stored.
# not all components have all metadata, try-catch blocks are needed to prevent key errors. Value > 0 tests are required
# because Aspace won't consider JSON valid if it contains an 'empty' note field.
# This function is currently commented out b/c decision was made not to store techMD in general notes. To re-enable,
# call from within 'dig_obj' variable definition at ~ line 130
#def build_comp_exif_notes(filename, techmd_dict):
    #note_list = []
    #try:
        #if len(techmd_dict[filename]['duration-Ms']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['duration-Ms'], 'duration Ms'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['duration-H:M:S']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['duration-H:M:S'], 'duration H:M:S'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['sampleRate']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['sampleRate'], 'sample rate'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['bitDepth']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['bitDepth'], 'bit depth'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['pixelDimensions']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['pixelDimensions'], 'pixel dimensions'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['resolution']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['resolution'], 'resolution'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['bitsPerSample']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['bitsPerSample'], 'bits per sample'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['colorSpace']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['colorSpace'], 'color space'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['createDate']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['createDate'], 'create date'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['creatingApplicationName']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['creatingApplicationName'], 'creating application name'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['creatingApplicationVersion']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['creatingApplicationVersion'], 'creating application version'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['author']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['author'], 'author'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['title']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['title'], 'title'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['duration-Ms']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['duration-Ms'], 'duration-Ms'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['bitRate']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['bitRate'], 'bit rate'))
    #except KeyError:
        #pass
    #try:
        #if len(techmd_dict[filename]['frameRate']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['frameRate'], 'frame rate'))
    #except KeyError:
       # pass
    #try:
        #if len(techmd_dict[filename]['chromaSubsampling']) > 0:
            #note_list.append(note_builder(techmd_dict[filename]['chromaSubsampling'], 'chroma subsampling'))
    #except KeyError:
        #pass
    #return note_list


def note_builder(list_index, label_value):
    note_text = {'jsonmodel_type':'note_digital_object', 'publish':False, 'content':[list_index], 'type':'note',
                 'label':label_value}
    return note_text


def get_file_type(filename):
    period_loc = filename.rfind('.')
    extension = filename[period_loc:len(filename)]
    if 'tif' in extension:
        value = 'image/tiff'
    elif 'wav' in extension:
        value = 'audio/und.wav'
    elif 'pdf' in extension:
        value = 'application/pdf'
    elif extension == 'doc':
        value = 'application/msword'
    elif 'docx' in extension:
        value = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif 'mov' in extension:
        value = 'video/quicktime'
    else:
        print("File extension for " + filename + " not recognized. Please reformat files or add extension to "
                                                 "get_file_type function")
        sys.exit()
    return value

main()

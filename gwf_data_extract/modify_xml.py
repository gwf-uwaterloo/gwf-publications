import os
import pandas as pd
import xml.etree.ElementTree as et
import html
import requests
import collections
import json
from zlib import crc32 
import xml.dom.minidom as md
from lxml import etree
import yaml

def handle_HTML_entities(file_name: str):

    tree = et.parse(file_name)
    for element in tree.iter():
        text = element.text
        if text: element.text = html.unescape(text)

    with open (file_name, "wb") as files :
        tree.write(files, encoding='UTF-8', xml_declaration=True, method='xml')

def add_abstract_to_missing(in_file: str, out_file: str):
    data_url = 'https://api.semanticscholar.org/v1/paper/{DOI}'
    tree = et.parse(in_file)

    for paper_element in tree.findall(".//paper"):
        abstract_element = paper_element.find("abstract")
        doi = paper_element.find("doi").text
        if abstract_element is not None and abstract_element.text is None:
            r = requests.get(url = data_url.replace("{DOI}", doi))
            if r.status_code!=200: print("r: " + str(r.content))
            try:                
                abstract_element.text = r.json()['abstract']
            except:
                print(doi)
            
    with open (out_file, "wb") as files :
        tree.write(files, encoding='UTF-8', xml_declaration=True, method='xml')

def get_website_dois():
    all_website_dois = []
    files_path = 'data/xml/'
    for file in os.listdir(files_path):        
        input = files_path+ file        
        tree = et.parse(input)
        root = tree.getroot()

        for paper in root.iter('paper'):
            all_website_dois.append(paper.find("doi").text)

    return all_website_dois

def get_website_bibkeys():
    all_website_bibkeys = []
    files_path = 'data/xml/'
    for file in os.listdir(files_path):
        input = files_path+ file        
        tree = et.parse(input)
        root = tree.getroot()

        for paper in root.iter('paper'):
            all_website_bibkeys.append(paper.find("bibkey").text)

    return all_website_bibkeys

def find_doi_diffs(all_to_compare_file: str):
    dois = pd.read_csv(all_to_compare_file, header=0).fillna("").values.tolist()
    dois = [item[0] for item in dois]
    websit_dois = get_website_dois()
    print(len(dois))
    print(len(websit_dois))

    added_dois = [x for x in dois if x not in websit_dois]
    print(len(added_dois))
    
def get_new_doi_data(extra_publication: str):
    # gets all the data and abstracts for newly added DOIs
    # updates the result.json and abstract.json files with this new DOIs

    script_dir = os.path.dirname(__file__)
    dois = pd.read_csv(script_dir+'/'+extra_publication, header=None).iloc[:,0].values.tolist()
    
    data_url =('https://api.crossref.org/works/{DOI}')
    
    with open(script_dir+'/result.json', 'r') as openfile:
        detail_dict = json.load(openfile)

    for doi in dois:
        if doi not in detail_dict:
            try:
                # print(doi)
                url = data_url.replace("{DOI}", doi)
                r = requests.get(url)
                if r.status_code != 200:
                    print(r.text)
                    print(doi)

                data = r.json()
                detail_dict[data['message']['DOI']] = data['message']
            except: 
                print('exception')
                print(doi)
                pass            

    with open(script_dir+'/result.json', "w") as outfile:
        outfile.write(json.dumps(detail_dict, indent=4)) 


    with open(script_dir+'/abstract.json', 'r') as openfile:
        abs_dict = json.load(openfile)

    data_url='https://api.openalex.org/works/https://doi.org/{DOI}'
    for doi in dois:
        if doi not in abs_dict:    
            r = requests.get(url = data_url.replace("{DOI}", doi))
            # print(doi)
            if r.status_code != 200:
                print(r.status_code)
                print(doi)
            else:
                response = r.json()
                if response['abstract_inverted_index']:   
                    abstract = {}         
                    for key, indexes in response['abstract_inverted_index'].items():
                        for index in indexes:
                            abstract[index] = key
                    
                    abs_dict[response['doi'].replace('https://doi.org/', '')] = ' '.join(list(collections.OrderedDict(sorted(abstract.items())).values()))

    with open(script_dir+'/abstract.json', "w") as outfile:
        outfile.write(json.dumps(abs_dict, indent=4))            

def add_doi_to_xml(new_doi_file:str, xml_folder: str, yaml_folder: str):
    # adds new papers to the existing DOIs
    # run this after you updated result.json and abstract.json with get_new_doi_data() function    

    def compute_hash(value: bytes) -> str:
        checksum = crc32(value) & 0xFFFFFFFF
        return f"{checksum:08x}"

    def generate_bibkey(title, author, year, bibkey_list):
        author_list = [(item['family'] if 'family' in item else '') for item in author] + [(item['given'] if 'given' in item else '') for item in author]    
        title_list = title.split()
        count=1
        while True:
            bibkey = '-'.join(author_list[:count] + [str(year)] + title_list[:count])
            if bibkey not in bibkey_list: return bibkey
            count += 1

    script_dir = os.path.dirname(__file__)
    website_dois = get_website_dois()
    dois = pd.read_csv(script_dir+'/'+new_doi_file, header=None).iloc[:,0].values.tolist()
    dois = [item.lower() for item in dois if item not in website_dois] # drop DOIs that already exist

    with open(script_dir+'/result.json', 'r') as openfile:     
        json_object = json.load(openfile)

    with open(script_dir+'/abstract.json', 'r') as openfile:     
        abstract_dict = json.load(openfile)

    paper_dict = {}
    json_object = {key:item for key, item in json_object.items() if key in dois}
    json_object = {key: item for key, item in json_object.items() if ('author' in item) and (item['title'])} # drop papers without title or author 
        
    for key, item in json_object.items():
        try:
            year = item['published']['date-parts'][0][0]
            journal = item['container-title'][0] if item['container-title'] else ' '
            volume = item['volume'] if 'volume' in item else ''
            issue = item['issue'] if 'issue' in item else ''
            pub_key = 'journal: '+journal+' volume: '+volume+' issue: '+issue
            if year not in paper_dict: paper_dict[year]={}
            if pub_key not in paper_dict[year]: paper_dict[year][pub_key]={}
            paper_dict[year][pub_key][key] = item     
        except:            
            pass

    bibkey_list = get_website_bibkeys()

    for year, year_dict in paper_dict.items():
        if year<2016: continue # we don't have any paper befor 2016
        tree = et.parse(xml_folder+"G"+str(year)[-2:]+".xml")
        root = tree.getroot()

        for index, (volume, item) in enumerate(year_dict.items()):
            first_item = list(item.items())[0][1]
            booktitle = (first_item['container-title'][0] if first_item['container-title'] else ' ')+((', Volume '+first_item['volume']) if 'volume' in first_item else '')+((', Issue '+first_item['issue']) if 'issue' in first_item else '')

            tag_vol = root.find('.//booktitle[.="'+booktitle+'"]/....')
            if tag_vol: # check if volume has existed
                paper_id_ofs = int(tag_vol.findall("./paper")[-1].get('id')) if tag_vol.findall("./paper") else 0
            else:
                tag_vol = et.Element("volume")
                root.append(tag_vol)
                tag_vol.set('id', str(int(root.findall("./volume")[-2].get('id'))+1))

                tag_meta = et.Element("meta")
                tag_vol.append(tag_meta)
                tag_subelement = et.SubElement(tag_meta, "booktitle")
                tag_subelement.text = booktitle
                tag_subelement = et.SubElement(tag_meta, "publisher")
                tag_subelement.text = first_item['publisher']
                tag_subelement = et.SubElement(tag_meta, "address")
                tag_subelement.text = ""
                tag_subelement = et.SubElement(tag_meta, "year")
                tag_subelement.text = str(year)
                paper_id_ofs = 0

            tmep_dict = year_dict[volume]
            for idx, (key, tmep_dict_item) in enumerate(tmep_dict.items()):
                skip_flag = 0
                for author in tmep_dict_item['author']: # skip papers that don't have author name or family
                    if ('given' not in author) or ('family' not in author): skip_flag = 1
                if skip_flag: continue
            
                tag_paper = et.Element("paper")
                tag_vol.append(tag_paper)
                tag_paper.set('id', str(idx+1+paper_id_ofs))
                tag_subelement = et.SubElement(tag_paper, "title")
                tag_subelement.text = tmep_dict_item['title'][0]
                for author in tmep_dict_item['author']:
                    tag_subelement = et.SubElement(tag_paper, "author")
                    tag_subsubelement = et.SubElement(tag_subelement, "first")
                    tag_subsubelement.text = (author['given'] if 'given' in author else '')
                    tag_subsubelement = et.SubElement(tag_subelement, "last")
                    tag_subsubelement.text = (author['family'] if 'family' in author else '')

                tag_subelement = et.SubElement(tag_paper, "abstract")
                tag_subelement.text = abstract_dict[tmep_dict_item['DOI']] if tmep_dict_item['DOI'] in abstract_dict else ''
                tag_subelement = et.SubElement(tag_paper, "url")
                tag_subelement.text =  f'G{str(year)[-2:]}-{index+1}{(idx+1):03}'
                tag_subelement.set('hash', compute_hash(str.encode(tag_subelement.text)))
            
                if 'page' in tmep_dict_item:
                    tag_subelement = et.SubElement(tag_paper, "pages")
                    tag_subelement.text = tmep_dict_item['page']

                tag_subelement = et.SubElement(tag_paper, "doi")
                tag_subelement.text = tmep_dict_item['DOI']
                tag_subelement = et.SubElement(tag_paper, "bibkey")
                bibkey = generate_bibkey(tmep_dict_item['title'][0], tmep_dict_item['author'], year, bibkey_list)
                tag_subelement.text = bibkey
                bibkey_list.append(bibkey)

        print(year)

        tree = et.ElementTree(root)    
        file_name = xml_folder+"G"+str(year)[-2:]+".xml"   
        with open(file_name, "w", encoding="UTF-8") as f:
            f.write(etree.tostring(etree.XML(et.tostring(root, encoding="UTF-8", xml_declaration=True), parser=etree.XMLParser(remove_blank_text=True))).decode())

        xml_pretty_str = md.parse(file_name)
        xml_pretty_str = xml_pretty_str.toprettyxml(encoding='UTF-8').decode()
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(xml_pretty_str)    

        handle_HTML_entities(file_name)    

    with open(yaml_folder+'name_variants.yaml', 'r') as file:
        dict_file = yaml.safe_load(file)
    for key in json_object:
        for item in json_object[key]['author']:
            if ('given' in item) and ('family' in item): element = {'canonical' : {'first': (item['given'] if 'given' in item else ''), 'last': (item['family'] if 'family' in item else '')}, 'id':(item['given'] if 'given' in item else '').replace('.', '')+'-'+(item['family'] if 'family' in item else '').replace('.', '')}
            if element not in dict_file: dict_file.append(element)

    with open(yaml_folder+'name_variants.yaml', 'w') as file:
        documents = yaml.dump(dict_file, file, default_flow_style=None)

def assign_prj(in_file: str, out_file: str, doi2prj_file: str):
    doi_prj_df = pd.read_excel(doi2prj_file)
    tree = et.parse(in_file)

    for paper_element in tree.findall(".//paper"):
        # abstract_element = paper_element.find("abstract")
        doi = paper_element.find("doi").text
        prj = paper_element.find("project")
        project_num = doi_prj_df[doi_prj_df['DOI'] == doi]['prj']
        prj.text = "prj46" if project_num.empty else project_num.iloc[0]
        pass
        # if abstract_element is not None and abstract_element.text is None:
        #     r = requests.get(url = data_url.replace("{DOI}", doi))
        #     if r.status_code!=200: print("r: " + str(r.content))
        #     try:                
        #         abstract_element.text = r.json()['abstract']
        #     except:
        #         print(doi)
            
    with open (out_file, "wb") as files :
        tree.write(files, encoding='UTF-8', xml_declaration=True, method='xml')

# get_new_doi_data('DOI_extra.csv')
# get_new_doi_data('non_doi_titles.csv')
# find_doi_diffs('gwf_data_extract/doi_from_USask.csv')

# add_doi_to_xml('non_doi_titles.csv', 'data/xml/', 'data/yaml/')
# add_doi_to_xml('extra_publication_cleaned.csv', 'data/xml/', 'data/yaml/')
# add_doi_to_xml('DOI_extra.csv', 'data/xml/', 'data/yaml/')

# handle_HTML_entities("data/xml/G21.xml")
# add_abstract_to_missing("data/xml/G17.xml", "data/xml/G17.xml")
assign_prj("data/xml/G16.xml", "data/xml/G16.xml", "gwf_data_extract/doi2projects.xlsx")
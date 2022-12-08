import os
import yaml
import pandas as pd
from typing import Any
from typing import Dict
import urllib.parse
import difflib
import re
import requests
import time
import json
import xml.etree.ElementTree as et
from zlib import crc32 
import yaml
import collections
import nltk
from nltk.corpus import stopwords
import numpy as np
import xml.dom.minidom as md
import html

similar_count = 0
no_data_count = 0

def get_doi(publication: str):
    """
    search for the paper's doi form the title
    Arguments:
        publication: title string        
    Returns:
        
    """

    global similar_count
    global no_data_count
    
    paper_url = "https://api.semanticscholar.org/v1/paper/"
    search_url = "https://api.semanticscholar.org/graph/v1/paper/search?"
    headers={'x-api-key':'LPkwK92ydta0i2EY5UB8fgnVhoLPZb72T3p3TCF1'} 

    pub = re.split('[,."]', publication)
    pub = pub[np.argmax(np.array([len(item) for item in pub if all(word not in item for word in ['Proceedings', 'Conference', 'Journal'])]))]

    pub = pub.replace("'", "").replace('"', '').replace(':', '').replace('-', ' ')    
    pub = pub.split()    
    
    query = "+".join(pub).lower()                    
    payload = {'offset': 0, 'limit': 10,'query': query,}

    PARAMS = urllib.parse.urlencode(payload, safe=':+')    
    r = requests.get(url=search_url, params=PARAMS, headers=headers)
    if r.status_code!=200: print("r: " + str(r.content))
    
    try:
        data = r.json()
        score = []
        if data['total'] == 0: no_data_count += 1
        for paper in data["data"]:
            temp = difflib.SequenceMatcher(None, paper["title"], ' '.join(pub))
            score.append(temp.ratio())

        url2 = paper_url + data["data"][score.index(max(score))]["paperId"]
        similarity_score = max(score)
        title = data["data"][score.index(max(score))]["title"]

        if similarity_score<0.5:
            similar_count += 1
            raise

        r2 = requests.get(url=url2, headers=headers)
        if r2.status_code!=200: print("r2: " + str(r2.content))
        data2 = r2.json()
        paper_doi = data2["doi"]
    except:
        # mostly papers without doi or tha paper doesn't exist
        paper_doi = None
        similarity_score = 'exception'
        title = 'exception'
        print("None doi")

    return paper_doi, similarity_score, title, query

def extract_doi(input_file: str, output_file: str = None):
            
    paper_df = pd.read_csv(input_file, header=0).fillna("")

    paper_list = [None] * len(paper_df)
    doi_list = [None] * len(paper_df)
    score = [None] * len(paper_df)
    title = [None] * len(paper_df)
    query = [None] * len(paper_df)
    
    for i in range(len(paper_df)):
        publication = paper_df.loc[i][0]
        pub = re.split("([Dd][Oo][Ii])", publication)
        doi_list[i] = (pub[-1].split()[0].replace('.org/', '') if pub[-1].startswith('.org/') else pub[-1].replace(':', '').split()[0]) if len(pub) >= 3 else None    
        try: 
            doi_list[i] = doi_list[i].strip(",.")
            doi_list[i] = re.sub("([()])", " ", doi_list[i])
            doi_list[i] = doi_list[i].split()[0]
        except: pass
        if doi_list[i]:
            r = requests.get(url='https://api.crossref.org/works/' + doi_list[i])
            if r.status_code != 200:
                print('crossref:' + r.text)
                doi_list[i], score[i], title[i], query[i] = get_doi(pub[0])
        else:
            doi_list[i], score[i], title[i], query[i] = get_doi(pub[0])    

        paper_list[i] = pub[0]
        print(i)

        if i%40 == 39:
            paper_df['doi'] = doi_list            
            paper_df['score'] = score
            paper_df['paper'] = paper_list
            paper_df['title'] = title
            paper_df['query'] = query

            paper_df.to_csv(output_file, index=False)
            paper_df['doi'].dropna().str.lower().drop_duplicates().to_csv('DOI_all.csv', index=False)

    paper_df['doi'] = doi_list    
    paper_df['score'] = score
    paper_df['paper'] = paper_list
    paper_df['title'] = title
    paper_df['query'] = query
    paper_df.to_csv(output_file, index=False)
    paper_df['doi'].dropna().str.lower().drop_duplicates().to_csv('DOI_all.csv', index=False)

def fetch_paper_data(input_file: str, output_file: str = None):
    data_url =('https://api.crossref.org/works/{DOI}')

    all_data_dict = {}

    paper_df = pd.read_csv(input_file, header=0).fillna("")['doi']

    for i in range(len(paper_df)):
        print(i)
        try:
            url = data_url.replace("{DOI}", paper_df[i])
            r = requests.get(url)
            if r.status_code != 200:
                print(r.text)

            data = r.json()
            all_data_dict[data['message']['DOI']] = data['message']
        except: 
            print('exception')
            pass    
        
        if i==100:
            json_object = json.dumps(all_data_dict, indent=4)
            with open(output_file, "w") as outfile:
                outfile.write(json_object)

    json_object = json.dumps(all_data_dict, indent=4)
    with open(output_file, "w") as outfile:
        outfile.write(json_object)     

def get_abstracts(input_file: str, output_file: str = None):
    paper_df = pd.read_csv(input_file, header=0).fillna("")['doi']

    data_url='https://api.openalex.org/works/https://doi.org/{DOI}'
    response_dict = {}
    for idx, item in enumerate(set(paper_df)):    
        r = requests.get(url = data_url.replace("{DOI}", item))
        print(idx)
        if r.status_code != 200:
            print(r.status_code)
        else:
            response = r.json()
            if response['abstract_inverted_index']:   
                abstract = {}         
                for key, indexes in response['abstract_inverted_index'].items():
                    for index in indexes:
                        abstract[index] = key
                
                response_dict[response['doi'].replace('https://doi.org/', '')] = ' '.join(list(collections.OrderedDict(sorted(abstract.items())).values()))

    json_object = json.dumps(response_dict, indent=4)
    with open(output_file, "w") as outfile:
        outfile.write(json_object)            


def create_xml_yaml_files(input_file: str, abstract_file: str):
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

    with open(input_file, 'r') as openfile:     
        json_object = json.load(openfile)

    with open(abstract_file, 'r') as openfile:     
        abstract_dict = json.load(openfile)            

    with_abs, without_abs = 0, 0

    paper_dict = {}
    json_object = {key: item for key, item in json_object.items() if ('author' in item) and (item['title'])} # drop papers without title or author 
    print(len(json_object))
    count = 0
    count1 = 0
    count2 = 0
    for key, item in json_object.items():
        try:
            year = item['published']['date-parts'][0][0]
            count1 += 1
            journal = item['container-title'][0] if item['container-title'] else ' '
            count2 += 1
            volume = item['volume'] if 'volume' in item else ''
            issue = item['issue'] if 'issue' in item else ''
            pub_key = 'journal: '+journal+' volume: '+volume+' issue: '+issue
            if year not in paper_dict: paper_dict[year]={}
            if pub_key not in paper_dict[year]: paper_dict[year][pub_key]={}
            paper_dict[year][pub_key][key] = item     
        except:
            count += 1
            pass
    
    print(count, count1, count2)
    for year, year_dict in paper_dict.items():        
        tag_collection = et.Element("collection")
        tag_collection.set('id', "G"+str(year)[-2:])

        bibkey_list = []

        for index, (volume, item) in enumerate(year_dict.items()):
            tag_vol = et.Element("volume")
            tag_collection.append(tag_vol)
            tag_vol.set('id', str(index+1))

            first_item = list(item.items())[0][1]

            tag_meta = et.Element("meta")
            tag_vol.append(tag_meta)    
            tag_subelement = et.SubElement(tag_meta, "booktitle")
            tag_subelement.text = (first_item['container-title'][0] if first_item['container-title'] else ' ')+((', Volume '+first_item['volume']) if 'volume' in first_item else '')+((', Issue '+first_item['issue']) if 'issue' in first_item else '')
            tag_subelement = et.SubElement(tag_meta, "publisher")
            tag_subelement.text = first_item['publisher']
            tag_subelement = et.SubElement(tag_meta, "address")
            tag_subelement.text = ""
            tag_subelement = et.SubElement(tag_meta, "year")
            tag_subelement.text = str(year)          

            tmep_dict = year_dict[volume]
            for idx, (key, tmep_dict_item) in enumerate(tmep_dict.items()):
                skip_flag = 0
                for author in tmep_dict_item['author']: # skip papers that don't have author name or family
                    if ('given' not in author) or ('family' not in author): skip_flag = 1
                if skip_flag: continue
                
                tag_paper = et.Element("paper")
                tag_vol.append(tag_paper)
                tag_paper.set('id', str(idx+1))
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

        tree = et.ElementTree(tag_collection)
        file_name = "G"+str(year)[-2:]+".xml"
        with open (file_name, "wb") as files :
            tree.write(files, encoding='UTF-8', xml_declaration=True)        
        
        xml_pretty_str = md.parse(file_name)
        xml_pretty_str = xml_pretty_str.toprettyxml(encoding='UTF-8').decode()
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(xml_pretty_str)        

    dict_file = []
    for key in json_object:
        for item in json_object[key]['author']:
            if ('given' in item) and ('family' in item): element = {'canonical' : {'first': (item['given'] if 'given' in item else ''), 'last': (item['family'] if 'family' in item else '')}, 'id':(item['given'] if 'given' in item else '').replace('.', '')+'-'+(item['family'] if 'family' in item else '').replace('.', '')}
            if element not in dict_file: dict_file.append(element)

    with open(r'name_variants.yaml', 'w') as file:
        documents = yaml.dump(dict_file, file, default_flow_style=None)

def handle_HTML_entities(file_name: str):

    tree = et.parse(file_name)
    for element in tree.iter():
        text = element.text
        if text: element.text = html.unescape(text)

    with open (file_name, "wb") as files :
        tree.write(files, encoding='UTF-8', xml_declaration=True, method='xml')


if __name__ == "__main__":    
    # extract_doi('gwf_data_extract/source-01.csv', 'gwf_data_extract/output_all.csv')             # 1st
    # fetch_paper_data('DOI_all.csv', 'result.json')            # 2nd
    # get_abstracts('DOI_all.csv', 'abstract.json')             # 3rd
    # create_xml_yaml_files('result.json', 'abstract.json')     # 4th
    
    handle_HTML_entities("data/xml/G22.xml")

    # paper_df = pd.read_csv('output_all_non.csv', header=0).fillna("").iloc[:,0]
    # for paper in paper_df:
    #     get_doi(re.split("([Dd][Oo][Ii])", paper)[0])
    #     print(similar_count, no_data_count)
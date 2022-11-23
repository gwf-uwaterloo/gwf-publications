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

nltk.download("stopwords")
list_stopwords = list(stopwords.words("english"))
def get_doi(publication: str):
    """
    get doi from the papers title
    """
    string_check = re.compile("[@_!#$%^&*()<>?/\|}{~:-]")
    paper_url = "https://api.semanticscholar.org/v1/paper/"
    search_url = "https://api.semanticscholar.org/graph/v1/paper/search?"

    pub = re.split("[,.:]", publication)
    pub = pub[np.argmax(np.array([len(item) for item in pub]))]

    pub = re.sub("([A-Z][.][,])", "", pub)
    pub = re.sub("([A-Z][.][A-Z][.])", "", pub).replace(".", "").replace('"', "")
    pub = re.sub("([A-Z][.])", "", pub).replace("’", "").replace("'", "")
    pub = re.sub("([(][0-9]{4}[)])", "", pub)

    pub = [i for item in pub.split(",") for i in item.strip().split()]
    pub = [item for item in pub if item.lower() not in list_stopwords and len(item) > 2]

    pub = [
        item
        for item in pub
        if (string_check.search(item) == None) and not bool(re.search(r"\d", item))
    ]

    i = 6
    while True:
        try:
            query = "+".join(pub[:i]).lower()
            break
        except:
            i -= 1
                
    payload = {'offset': 0, 'limit': 50,'query': query}

    PARAMS = urllib.parse.urlencode(payload, safe=':+')
    r = requests.get(url=search_url, params=PARAMS)
    if r.status_code!=200: print("r: " + str(r.content))

    try:
        data = r.json()
        if data["total"] > 1:
            score = []
            for paper in data["data"]:
                temp = difflib.SequenceMatcher(None, paper["title"], ' '.join(pub))
                a = temp.get_matching_blocks()
                score.append(temp.ratio())

            url2 = paper_url + data["data"][score.index(max(score))]["paperId"]
            similarity_score = max(score)
            title = data["data"][score.index(max(score))]["title"]
        else:
            url2 = paper_url + data["data"][0]["paperId"]
            similarity_score = difflib.SequenceMatcher(None, data["data"][0]["title"], ' '.join(pub)).ratio() + 5
            title = data["data"][0]["title"]

        r2 = requests.get(url=url2)
        if r2.status_code!=200: print("r2: " + str(r2.content))
        data2 = r2.json()
        paper_doi = data2["doi"]
    except:        
        paper_doi = None
        similarity_score = 'exception'
        title = 'exception'
        print("None doi")

    return paper_doi, similarity_score, title, query

def _read_input_file(input_file: str):
    """
    Read excel file
    """
    assert os.path.exists(
        input_file
    ), f"[INFO] Input file {input_file} does not exist"
    df = (
        pd.read_excel(input_file, header=0).fillna("")
        if input_file.endswith(".xlsx")
        else pd.read_csv(input_file, header=0, encoding="iso8859_16").fillna("")
    )
    return df

def extract_doi(input_file: str, output_file: str = None):
            
    paper_df = pd.read_excel(input_file, header=0).fillna("")

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
            paper_df['paper'] = paper_list
            paper_df['score'] = score
            paper_df['title'] = title
            paper_df['query'] = query

            paper_df.to_csv(output_file, index=False)
            # pd.DataFrame({'paper':paper_list, 'doi':doi_list}).to_csv(output_file, index=False)
            time.sleep(60*5+10)

    paper_df['doi'] = doi_list
    paper_df['paper'] = paper_list
    paper_df['score'] = score
    paper_df['title'] = title
    paper_df['query'] = query

    paper_df.to_csv(output_file, index=False)

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
    for key, item in json_object.items():
        try:
            year = item['published']['date-parts'][0][0]
            journal = item['container-title'][0]
            volume = item['volume'] if 'volume' in item else ''
            issue = item['issue'] if 'issue' in item else ''
            pub_key = 'journal: '+journal+' volume: '+volume+' issue: '+issue
            if year not in paper_dict: paper_dict[year]={}
            if pub_key not in paper_dict[year]: paper_dict[year][pub_key]={}
            paper_dict[year][pub_key][key] = item     
        except:
            pass

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
            tag_subelement.text = first_item['container-title'][0]+((', Volume '+first_item['volume']) if 'volume' in first_item else '')+((', Issue '+first_item['issue']) if 'issue' in first_item else '')
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
        with open ("G"+str(year)[-2:]+".xml", "wb") as files :
            tree.write(files, encoding='UTF-8', xml_declaration=True)

    dict_file = []
    for key in json_object:
        for item in json_object[key]['author']:
            if ('given' in item) and ('family' in item): element = {'canonical' : {'first': (item['given'] if 'given' in item else ''), 'last': (item['family'] if 'family' in item else '')}, 'id':(item['given'] if 'given' in item else '').replace('.', '')+'-'+(item['family'] if 'family' in item else '').replace('.', '')}
            if element not in dict_file: dict_file.append(element)

    with open(r'name_variants.yaml', 'w') as file:
        documents = yaml.dump(dict_file, file, default_flow_style=None)


if __name__ == "__main__":
    
    # extract_doi('GWF_all.xlsx', 'output_all.csv')
    # fetch_paper_data('DOI_all.csv', 'result.json')
    # get_abstracts('DOI_all.csv', 'abstract.json')
    # create_xml_yaml_files('result.json', 'abstract.json')    
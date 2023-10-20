import pandas as pd
import xml.etree.ElementTree as et
import html

def extract_to_files():
    sheet = pd.DataFrame(columns=["title", "author", "abstract", "url", "pages", "doi", "bibkey"])
    file = 'G23'
    input = 'data/xml/'+ file +'.xml'
    output = 'gwf_data_extract/'+file+'.csv'
    tree = et.parse(input)
    root = tree.getroot()

    for paper in root.iter('paper'):
        paper_dict = {}
        paper_dict["title"] = html.unescape(paper.find("title").text) if paper.find("title").text else paper.find("title").text
        paper_dict["author"] = ""
        for author in paper.findall("author"):
            paper_dict["author"] = paper_dict["author"] + author.find("first").text + " " + author.find("last").text + ", "
            paper_dict["author"] = html.unescape(paper_dict["author"]) if paper_dict["author"] else paper_dict["author"]
        paper_dict["abstract"] = html.unescape(paper.find("abstract").text) if paper.find("abstract").text else paper.find("abstract").text
        paper_dict["url"] = paper.find("url").text
        paper_dict["pages"] = paper.find("pages").text if paper.find("pages") is not None else ""
        paper_dict["doi"] = paper.find("doi").text
        paper_dict["bibkey"] = paper.find("bibkey").text
        
        sheet = pd.concat([sheet, pd.DataFrame([paper_dict.values()], columns=sheet.columns)], ignore_index=True)

    sheet.to_csv(output, index=False)

def extract_to_one_file():
    files = ['G16','G17','G18','G19','G20','G21','G22','G23']
    sheet = pd.DataFrame(columns=["title", "author", "abstract", "url", "pages", "doi", "bibkey"])        
    for file in files:        
        input = 'data/xml/'+ file +'.xml'
        output = 'gwf_data_extract/csv_all.csv'
        tree = et.parse(input)
        root = tree.getroot()

        for paper in root.iter('paper'):
            paper_dict = {}
            paper_dict["title"] = html.unescape(paper.find("title").text) if paper.find("title").text else paper.find("title").text
            paper_dict["author"] = ""
            for author in paper.findall("author"):
                paper_dict["author"] = paper_dict["author"] + author.find("first").text + " " + author.find("last").text + ", "
                paper_dict["author"] = html.unescape(paper_dict["author"]) if paper_dict["author"] else paper_dict["author"]
            paper_dict["abstract"] = html.unescape(paper.find("abstract").text) if paper.find("abstract").text else paper.find("abstract").text
            paper_dict["url"] = paper.find("url").text
            paper_dict["pages"] = paper.find("pages").text if paper.find("pages") is not None else ""
            paper_dict["doi"] = paper.find("doi").text
            paper_dict["bibkey"] = paper.find("bibkey").text
            
            sheet = pd.concat([sheet, pd.DataFrame([paper_dict.values()], columns=sheet.columns)], ignore_index=True)

    
    sheet.to_csv(output, index=False)

extract_to_files()


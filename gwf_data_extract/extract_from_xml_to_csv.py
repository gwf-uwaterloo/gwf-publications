import pandas as pd
import xml.etree.ElementTree as et

sheet = pd.DataFrame(columns=["title", "author", "abstract", "url", "pages", "doi", "bibkey"])
file = 'G16'
tree = et.parse(file+'.xml')
root = tree.getroot()

for paper in root.iter('paper'):
    paper_dict = {}
    paper_dict["title"] = paper.find("title").text
    paper_dict["author"] = ""
    for author in paper.findall("author"):
        paper_dict["author"] = paper_dict["author"] + author.find("first").text + " " + author.find("last").text + ", "
    paper_dict["abstract"] = paper.find("abstract").text
    paper_dict["url"] = paper.find("url").text
    paper_dict["pages"] = paper.find("pages").text if paper.find("pages") is not None else ""
    paper_dict["doi"] = paper.find("doi").text
    paper_dict["bibkey"] = paper.find("bibkey").text
    
    sheet = pd.concat([sheet, pd.DataFrame([paper_dict.values()], columns=sheet.columns)], ignore_index=True)

sheet.to_csv(file+".csv", index=False)
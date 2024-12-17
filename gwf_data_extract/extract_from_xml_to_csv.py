import pandas as pd
import xml.etree.ElementTree as et
import html

def extract_to_files(doi2prj_xlsx):
    # sheet = pd.DataFrame(columns=["title", "author", "abstract", "url", "pages", "doi", "bibkey", "project"])
    # file = 'G24'

    files = ['G16','G17','G18','G19','G20','G21','G22','G23', 'G24']
    for file in files:
        sheet = pd.DataFrame(columns=["title", "author", "abstract", "url", "pages", "doi", "bibkey", "project"])
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
            paper_dict["project"] = paper.find("project").text
            
            sheet = pd.concat([sheet, pd.DataFrame([paper_dict.values()], columns=sheet.columns)], ignore_index=True)

        doi_prj_df = pd.read_excel(doi2prj_xlsx)
        doi_prj_df = doi_prj_df.drop('DOI', axis=1)
        doi_prj_df = doi_prj_df.drop_duplicates()
        doi_prj_df = pd.concat([doi_prj_df, pd.DataFrame([{'Project Name':'Others','prj':'prj46'}])], ignore_index=True)
        sheet['project'] = sheet['project'].map(doi_prj_df.set_index('prj')['Project Name'].to_dict())

        sheet.to_csv(output, index=False)

def extract_to_one_file(doi2prj_xlsx):
    files = ['G16','G17','G18','G19','G20','G21','G22','G23', 'G24']
    sheet = pd.DataFrame(columns=["title", "author", "abstract", "url", "pages", "doi", "bibkey", "project"])        
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
            paper_dict["project"] = paper.find("project").text
            
            sheet = pd.concat([sheet, pd.DataFrame([paper_dict.values()], columns=sheet.columns)], ignore_index=True)    

    doi_prj_df = pd.read_excel(doi2prj_xlsx)
    doi_prj_df = doi_prj_df.drop('DOI', axis=1)
    doi_prj_df = doi_prj_df.drop_duplicates()
    doi_prj_df = pd.concat([doi_prj_df, pd.DataFrame([{'Project Name':'Others','prj':'prj46'}])], ignore_index=True)
    sheet['project'] = sheet['project'].map(doi_prj_df.set_index('prj')['Project Name'].to_dict())
    sheet.to_csv(output, index=False)

# extract_to_files('gwf_data_extract/doi2projects.xlsx')
extract_to_one_file('gwf_data_extract/doi2projects.xlsx')


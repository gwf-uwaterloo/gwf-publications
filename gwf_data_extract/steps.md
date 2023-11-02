# add new DOIs to the website
1- put all your new DOIs in a new csv file
2- from file modify_xml.py run get_new_doi_data() to get the data for these new DOIs
3- from file modify_xml.py run add_doi_to_xml() to add these new papers to xml files
4- we should extract the name_variants.yaml file again by go through get_author_institute.ipynb file

# update the projects
1- update the file doi2projects.xlsx for modifining the project or add a new row for new record
2- use create_projects.ipynb to regenerate the projects' numbers (running this code will update the third column of the same file)
3- after generating the doi2project.xlsx file use assign_prj function from modify_xml.py file to modify the xml files

# Indexing GWF Publications

Use [this](https://github.com/castorini/anserini/blob/master/docs/acl-anthology.md) instruction to make the environment. (both for generating GWF data and pyserini)

Before starting the `Indexing Data` section, navigate to the `build/data` directory and do this steps to correct the yml files.

```bash
pip install ruamel.yaml.cmd
mv volumes.yaml volumes_old.yaml
yaml merge-expand volumes_old.yaml volumes.yaml
mv papers papers_old

# since we renamed the papers dir, it no longer exists
mkdir papers 

for yaml_old in papers_old/*.yaml; do  # this is ~10minutes !
  yaml_new=${yaml_old##*/}
  yaml merge-expand $yaml_old papers/$yaml_new
done
```

Now you should add the `venue` attribute to the yml files. Add this to all the papers in all the files in the `papers/` directory. Add the same attribute to all the volumes in the `volumes.yml` file.

```yml
  venue:
  - GWF
```
Now you can do the `Indexing Data` section from the first link you've opened.
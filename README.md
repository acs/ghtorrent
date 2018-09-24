# ghtorrent

Experimental GitHub project analysis based on GHTorrent.

The goal of this project is to explore the use of GHTorrent to
understand better the life of Open Source software projects.

It is in the initial conception phase so probably only useful
to exchange ideas and early prototypes.

To load the GitHub projects data in Elasticsearch:

* Download [GHTorrent data](http://ghtorrent.org/downloads.html)
* Import in MySQL the projects data using `ght-restore-mysql-projects`
* Import in Elasticsearch the projects data using `ght2es.py`
* Use Kibana to visualize the projects data and start analyzing it

You will need around 4h to complete the above steps.

## Evolution in time of projects

![](images/projects.png?raw=true)


## Evolution in time of non fork projects

![](images/projects-no-fork.png?raw=true)

## Evolution in time of the top 10 languages

![](images/top10-languages.png?raw=true)

The language detection is based on https://github.com/github/linguist

## List with all languages

[CSV data](all_languages.csv)
# Intro

**guifiAnalyzer** is a python project aspiring to be a monitoring/research tool collecting information from guifi.net. 

This information can be either: 
* infrastructure information (based on the [CNML](http://en.wiki.guifi.net/wiki/CNML/en) information of the network) 
* traffic information (based on the information deployed by the already deployed  [SNPservices](https://github.com/guifi/snpservices) services of guifi.net)

# Subprojects

**guifiAnalyzer** is currently consisted from 4 different subprojects. 

* [guifiwrapper](https://github.com/emmdim/guifiAnalyzer/wiki/guifiwrapper) can be considered the main backend, but can be also used to get information. _guifiwrapper_ is a tool to grab CNML information about a guifi.net zone and its subzones. The CNML calls on the guifi.net web server are based on [libcnml](https://github.com/emmdim/guifiAnalyzer/wiki/https://github.com/PabloCastellano/libcnml/). The rest of the subprojects use _guifiwrapper_ to grab whatever infrastructural information is needed.

* [plot](https://github.com/emmdim/guifiAnalyzer/wiki/plot) is a tool that produces certain plots with statistics for guifi.net. It has as a goal to set as an example how to plot using information from _guifiwrapper_.

* [vis](https://github.com/emmdim/guifiAnalyzer/wiki/vis) is an unfinished effort to create visualizations of graphs extracted with _guifiwrapper_ using D3.js.

* [traffic](https://github.com/emmdim/guifiAnalyzer/wiki/traffic) is a tool that extract traffic information for the nodes of a guifi.net zone, asking the responsible graph servers. 


More information on the [wiki](https://github.com/emmdim/guifiAnalyzer/wiki) of the project.


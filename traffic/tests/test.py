import os

from ..lib.sqlitedict.sqlitedict import SqliteDict

db = os.path.join(os.getcwd(),'guifiAnalyzerOut','traffic','8346','data.sqld')
linksTable = SqliteDict(
    filename=db,
    tablename='links',
    # create new db file if not exists and rewrite if exists
    flag='c',
    autocommit=False)
devicesTable = SqliteDict(
    filename=db,
    tablename='devices',
    # r/w table
    flag='c',
    autocommit=False)
graphServersTable = SqliteDict(
    filename=db,
    tablename='graphServers',
    # r/w table
    flag='c',
    autocommit=False)

for key,value in graphServersTable.iteritems():
	print key
	print value
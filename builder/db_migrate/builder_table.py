# -*- coding:utf-8 -*-

import os

from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from urllib import parse
from sqlalchemy.schema import MetaData
from utils.log_info import Logger
from db_migrate.update.databaseUtil import versions, migrate
from utils.my_pymysql_pool import connect_execute_close_db, connect_execute_commit_close_db
import pandas as pd

# 当前程序版本
progressVersion = os.getenv("BUILDERVERSION")
# 上线之前注释掉
progressVersion = 'builder-1.1.5'
Logger.log_info("progressVersion: %s" % progressVersion)

# 连接数据库
ip = os.getenv("RDSHOST")
port = eval(os.getenv("RDSPORT"))
user = os.getenv("RDSUSER")
passwd = str(os.getenv("RDSPASS"))
database = os.getenv("RDSDBNAME")
# ip = '10.2.174.230'
# port = 3306
# user = 'anydata'
# passwd = 'Qwe123!@#'
# database = 'anydata'
sqlalchemy_database_uri = 'mysql+pymysql://{user}:{passwd}@{ip}:{port}/{database}?charset=utf8'.format(
    user=user,
    passwd=parse.quote_plus(passwd),  # 特殊字符@处理
    ip=ip,
    port=port,
    database=database
)
engine = create_engine(sqlalchemy_database_uri,
                       connect_args={'connect_timeout': 3},
                       poolclass=NullPool,
                       echo=False)
meta = MetaData()
meta.reflect(bind=engine)


# 获取数据库版本
@connect_execute_close_db
def getDataBaseVersion(connection, cursor):
    sql = """SELECT builder_version FROM version WHERE id=1;"""
    Logger.log_info(sql)
    df = pd.read_sql(sql, connection)
    df = df.to_dict('records')
    return df


# 插入当前数据库版本
@connect_execute_commit_close_db
def insertDatabaseVersion(progressVersion, connection, cursor):
    sql = '''INSERT INTO version (builder_version) VALUES ("{}")'''.format(progressVersion)
    Logger.log_info(sql)
    cursor.execute(sql)


# 更新当前数据库版本
@connect_execute_commit_close_db
def updateDatabaseVersion(progressVersion, connection, cursor):
    sql = '''UPDATE version SET builder_version="{}" WHERE id=1'''.format(progressVersion)
    Logger.log_info(sql)
    cursor.execute(sql)


Logger.log_info('database tables: %s' % meta.tables.keys())
if 'version' in meta.tables.keys():
    # 数据库版本表存在
    Logger.log_info('database version table exists')
    # 获取数据库版本
    try:
        version = getDataBaseVersion()
    except Exception as e:
        Logger.log_info(e)
        raise e
    Logger.log_info("database builder version: %s" % version)
    if len(version) == 0:
        raise Exception('Database version not found. Upgrade fail.')

    if len(version[0]['builder_version']) == 0:
        Logger.log_info('builder_version not found. Start initialization')
        # 初始化数据库
        migrate(progressVersion, 'initiate')
        # 插入当前数据库版本
        try:
            updateDatabaseVersion(progressVersion)
        except Exception as e:
            Logger.log_info(e)
            raise e
        Logger.log_info("Change database builder version success.")
    else:
        databaseVersion = version[0]['builder_version']  # 数据库版本
        Logger.log_info('builder_version exists. Compare progressversion and databseversion.')

        # 将数据库版本与程序版本做比较
        if databaseVersion == progressVersion:
            Logger.log_info('Program version is identical with database version. Quitting upgrade program.')
        else:
            versionList = list(versions)
            if progressVersion in versionList and databaseVersion in versionList:
                progressVersionIdx = versionList.index(progressVersion)
                databaseVersionIdx = versionList.index(databaseVersion)
            else:
                Logger.log_info('Upgrade scheme not found. Database version：%s, Specifying version：%s' % (
                    databaseVersion, progressVersion))

            # 处理版本差异
            if progressVersionIdx > databaseVersionIdx:
                Logger.log_info('Start upgrading. progressVersionIdx: %s, databaseVersionIdx: %s' % (
                    progressVersionIdx, databaseVersionIdx))
                # 升级
                for i in range(databaseVersionIdx + 1, progressVersionIdx + 1):
                    migrate(versionList[i], 'update')
                # 插入当前数据库版本
                try:
                    updateDatabaseVersion(progressVersion)
                except Exception as e:
                    Logger.log_info(e)
                    raise e
                Logger.log_info("Change database builder version success.")

            elif progressVersionIdx < databaseVersionIdx:
                Logger.log_info('Program version is lower than installed version')
else:
    # 数据库版本表不存在
    # 进行数据库的初始化
    Logger.log_info('Database version table not exist. Start initialization')
    if progressVersion in versions:
        migrate(progressVersion, 'initiate')
        # 插入当前数据库版本
        try:
            insertDatabaseVersion(progressVersion)
        except Exception as e:
            Logger.log_info(e)
            raise e
        Logger.log_info("Change database builder version success.")
    else:
        raise Exception('Upgrade scheme not found.')
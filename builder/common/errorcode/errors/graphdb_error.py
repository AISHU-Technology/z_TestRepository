# -*- coding:utf-8 -*-
from __future__ import (absolute_import, unicode_literals)
from flask_babel import gettext as _l

errDict = {
    'Builder.GraphdbDao.GetPropertiesOrientdb.OrientdbRequestError': {
        "errorcode": "Builder.GraphdbDao.GetPropertiesOrientdb.OrientdbRequestError",
        "description": "[description]",
        "cause": "[cause]",
        "solution": _l("Please check whether the OrientDB request information is correct.")  # 请检查OrientDB请求信息是否正确
    },
    'Builder.GraphdbDao.GetPropertiesNebula.NebulaExecError': {
        "errorcode": "Builder.GraphdbDao.GetPropertiesNebula.NebulaExecError",
        "description": "[description]",
        "cause": "[cause]",
        "solution": _l("Please check whether the Nebula request information is correct.")  # 请检查Nebula请求信息是否正确
    },
    'Builder.GraphdbDao.Count.GraphDBConnectionError': {
        "errorcode": "Builder.GraphdbDao.Count.GraphDBConnectionError",
        "description": "[description]",
        "cause": "[cause]",
        "solution": _l("Please check whether your GraphDB service is running normally.")
    },
    'Builder.GraphdbDao.Count.DBNameNotExitsError': {
        "errorcode": "Builder.GraphdbDao.Count.DBNameNotExitsError",
        "description": "DB name:[db_name], graphdb_address: [graphdb_address], graphdb_port: [graphdb_port], graphdb_type: [graphdb_type]",
        "cause": "DB name:[db_name], graphdb_address: [graphdb_address], graphdb_port: [graphdb_port], graphdb_type: [graphdb_type]",
        "solution": _l("Please check whether your DB name is correct.")
    },
    'Builder.GraphdbDao.CountOrientdb.OrientdbRequestError': {
        "errorcode": "Builder.GraphdbDao.CountOrientdb.OrientdbRequestError",
        "description": "[description]",
        "cause": "[cause]",
        "solution": _l("Please check whether the OrientDB request information is correct.")  # 请检查OrientDB请求信息是否正确
    },
    'Builder.GraphdbDao.CountNebula.NebulaExecError': {
        "errorcode": "Builder.GraphdbDao.CountNebula.NebulaExecError",
        "description": "[description]",
        "cause": "[cause]",
        "solution": _l("Please check whether the Nebula request information is correct.")
    },
    'Builder.GraphdbDao.CheckSchemaNebula.NebulaExecError': {
        "errorcode": "Builder.GraphdbDao.CheckSchemaNebula.NebulaExecError",
        "description": "[description]",
        "cause": "[cause]",
        "solution": _l("Please check whether the Nebula request information is correct.")
    },
}

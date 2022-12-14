# -*-coding:utf-8-*-
# @Time    : 2020/9/7 18:22
# @Author  : Lowe.li
# @Email   : Lowe.li@aishu.cn
import requests
from flask import Blueprint, request, jsonify, send_file, send_from_directory, make_response

from werkzeug.utils import secure_filename
from dao.graph_dao import graph_dao
from dao.otl_dao import otl_dao
from dao.task_dao import task_dao
from dao.other_dao import other_dao
from service.knw_service import knw_service
from third_party_service.permission_manager import Permission
from utils.graph_check_parameters import graphCheckParameters
from utils.Gview import Gview
from utils.common_response_status import CommonResponseStatus
from service.graph_Service import graph_Service
from utils.CommonUtil import commonutil
from utils.ontology_check_params import otl_check_params
from service.Otl_Service import otl_service
import json
import os
from utils.log_info import Logger
from service.task_Service import task_service
from controller.knowledgeNetwork_controller import saveRelation, deleteRelation, updateKnw
from common.errorcode.gview import Gview as Gview2
from common.errorcode import codes
import uuid
from flasgger import swag_from
import yaml
graph_controller_app = Blueprint('graph_controller_app', __name__)

GBUILDER_ROOT_PATH = os.getenv('GBUILDER_ROOT_PATH', os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
with open(os.path.join(GBUILDER_ROOT_PATH, 'docs/swagger_definitions.yaml'), 'r') as f:
    swagger_definitions = yaml.load(f, Loader=yaml.FullLoader)
with open(os.path.join(GBUILDER_ROOT_PATH, 'docs/swagger_old_response.yaml'), 'r') as f:
    swagger_old_response = yaml.load(f, Loader=yaml.FullLoader)
    swagger_old_response.update(swagger_definitions)
with open(os.path.join(GBUILDER_ROOT_PATH, 'docs/swagger_new_response.yaml'), 'r') as f:
    swagger_new_response = yaml.load(f, Loader=yaml.FullLoader)
    swagger_new_response.update(swagger_definitions)

@graph_controller_app.route('', methods=["post"], strict_slashes=False)
@swag_from(swagger_old_response)
def graphopt():
    '''
    add a knowledge graph
    ---
    parameters:
        -   in: 'body'
            name: 'body'
            description: 'request body'
            required: true
            schema:
                $ref: '#/definitions/graph'
    '''
    param_code, params_json, param_message = commonutil.getMethodParam()
    params_json["graph_process"][0]["graph_DBName"] = other_dao.get_random_uuid()
    ret_code, ret_message = knw_service.check_knw_id(params_json)
    if ret_code != 200:
        return Gview.BuFailVreturn(cause=ret_message["des"], code=CommonResponseStatus.INVALID_KNW_ID.value,
                                   message=ret_message["detail"]), CommonResponseStatus.SERVER_ERROR.value
    ret_code, ret_message, graph_id = graph_Service.addgraph(params_json)
    Logger.log_info(ret_message)
    if ret_code != 200:
        Logger.log_error(ret_message)
        return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                   message=ret_message["message"]), ret_code
    # ???????????????????????????
    knw_id = params_json["knw_id"]
    response = saveRelation(knw_id, graph_id)
    if not response:
        graph_dao.delete_record(graph_id)
        return Gview.BuFailVreturn(cause=response["Description"], code=CommonResponseStatus.REQUEST_ERROR.value,
                                   message=response["ErrorDetail"]), CommonResponseStatus.SERVER_ERROR.value
    updateKnw(graph_id)
    return Gview.BuVreturn(message=ret_message.get("res")), CommonResponseStatus.SUCCESS.value


@graph_controller_app.route('/<grapid>', methods=["post"], strict_slashes=False)
@swag_from(swagger_old_response)
def graph(grapid):
    '''
    edit the graph information according to the graph id
    ---
    parameters:
        -   name: 'graphid'
            in: 'path'
            description: 'graph id'
            required: true
            type: 'integer'
        -   in: 'body'
            name: 'body'
            description: 'request body'
            required: true
            schema:
                $ref: '#/definitions/graph'
    '''
    # graphCheckParameters.graphAddPar????????????????????????
    # graph_Service.update????????????
    param_code, params_json, param_message = commonutil.getMethodParam()
    graph_step = params_json["graph_step"]
    graph_process_list = params_json["graph_process"]
    graph_process_dict = graph_process_list[0]
    # ?????????????????????????????????
    run_code, run_message = graph_Service.getrunbygraphid(grapid)
    if run_code == CommonResponseStatus.SERVER_ERROR.value:
        return Gview.BuFailVreturn(cause=run_message["cause"], code=run_message["code"],
                                   message=run_message[
                                       "message"]), CommonResponseStatus.SERVER_ERROR.value
    # ?????????????????????????????????????????????
    res, code = graph_Service.get_upload_id(grapid)
    res = res.to_dict('records')
    if len(res) > 0:
        cause = "graph upload can not edit"
        message = "graph cannot edit,the graph is upload"
        code = CommonResponseStatus.GRAPH_UPLOAD_NOT_EDIT.value
        return Gview.BuFailVreturn(cause=cause, code=code,
                                   message=message), CommonResponseStatus.SERVER_ERROR.value
    # ??????graph_process
    # ??????
    if graph_step == "graph_otl":
        #  ????????????????????????????????? ?????????????????????????????????
        updateoradd = params_json["updateoradd"]
        graph_process_dict["updateoradd"] = updateoradd
        if updateoradd == "add":
            paramscode, message = otl_check_params.valid_params_check("ontology_save", graph_process_dict)
            if paramscode != 0:
                return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                           message=message), CommonResponseStatus.BAD_REQUEST.value
            #  ???????????????????????? ????????????????????? ????????????????????????
            ret_code, ret_message, otl_id = otl_service.ontology_save(graph_process_dict)
            if ret_code == 200:  # ???????????????????????????????????????
                # otl_id = ret_message["res"]["ontology_id"]
                ret_code2, ret_message2 = graph_Service.update(grapid, params_json, otl_id)
                if ret_code2 == CommonResponseStatus.SERVER_ERROR.value:
                    return Gview.BuFailVreturn(cause=ret_message2["cause"], code=ret_message2["code"],
                                               message=ret_message2[
                                                   "message"]), CommonResponseStatus.SERVER_ERROR.value
                return ret_message, CommonResponseStatus.SUCCESS.value
            else:
                return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                           message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value

        elif updateoradd == "update_otl_name" or updateoradd == "update_otl_info":
            #  ??????otl_id ?????? otl id????????????
            paramscode, message = otl_check_params.valid_params_check(updateoradd, graph_process_dict)
            if paramscode != 0:
                return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                           message=message), CommonResponseStatus.BAD_REQUEST.value
            otl_id = graph_process_dict.get("id", None)
            # id ??????????????????????????????????????????????????? ??????
            if otl_id == None or not str(otl_id).isdigit() or otl_id == "0":
                message += " parameters: id must be int, and more than zero"
                return Gview.BuFailVreturn(cause=message, code=400001, message=message), 400
            #  ???????????????????????? ????????????????????? ????????????????????????
            if updateoradd == "update_otl_name":
                ret_code, ret_message = otl_service.update_name(str(otl_id), graph_process_dict, "1")
            elif updateoradd == "update_otl_info":
                ret_code, ret_message = otl_service.update_info(str(otl_id), graph_process_dict, "1", grapid)
            if ret_code == 200:
                # ?????? ??????temp??????
                ret_code2, ret_message2 = graph_Service.update_otl_temp(grapid)
                if ret_code2 == CommonResponseStatus.SERVER_ERROR.value:
                    return Gview.BuFailVreturn(cause=ret_message2["cause"], code=ret_message2["code"],
                                               message=ret_message2[
                                                   "message"]), CommonResponseStatus.SERVER_ERROR.value
                updateKnw(grapid)
                return Gview.BuVreturn(message=ret_message2.get("res")), CommonResponseStatus.SUCCESS.value
            else:
                return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                           message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value
    # ????????????????????????
    elif graph_step == "graph_baseInfo":
        ret_code, ret_message = knw_service.check_knw_id(params_json)
        if ret_code != 200:
            return Gview.BuFailVreturn(cause=ret_message["des"], code=CommonResponseStatus.INVALID_KNW_ID.value,
                                       message=ret_message["detail"]), CommonResponseStatus.SERVER_ERROR.value
        ret_code, ret_message = graph_Service.update(grapid, params_json, "-1")
        if ret_code != 200:
            return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                       message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value
        updateKnw(grapid)
        return Gview.BuVreturn(message=ret_message.get("res")), CommonResponseStatus.SUCCESS.value
    # ?????????????????? -- 144162????????????????????????+???????????????
    elif graph_step == 'graph_InfoExt':
        nums = len(graph_process_list)
        if nums > 100:
            obj = {}
            message = "the number of files and documents cannot be more then 100"
            obj["ErrorCode"] = str(CommonResponseStatus.OUT_OF_LIMIT.value)
            obj["Description"] = message
            obj["Solution"] = "please reduce the numbers of files and document "
            obj["ErrorDetails"] = [str(message)]
            obj["ErrorLink"] = ""
            return Gview.VErrorreturn(obj), CommonResponseStatus.SERVER_ERROR.value
        ret_code, ret_message = graph_Service.update(grapid, params_json, "-1")
        if ret_code == CommonResponseStatus.SERVER_ERROR.value:
            obj = {}
            obj["ErrorCode"] = str(ret_message["code"])
            obj["Description"] = ret_message["cause"]
            obj["Solution"] = "please check your mysql or your parameters"
            obj["ErrorDetails"] = [{str(ret_message["message"])}]
            obj["ErrorLink"] = ""
            return Gview.VErrorreturn(obj), CommonResponseStatus.BAD_REQUEST.value
        updateKnw(grapid)
        return Gview.BuVreturn(message=ret_message.get("res")), CommonResponseStatus.SUCCESS.value


    # ???????????????
    else:
        # ??????????????????????????????
        ret_code, obj = graph_Service.getDsByGraphid(grapid)
        if ret_code != 200:
            return Gview.BuFailVreturn(cause=ret_code["cause"], code=ret_code["code"],
                                       message=ret_code["message"]), CommonResponseStatus.SERVER_ERROR.value
        dsids = obj["ids"]
        print("old_ids: ", dsids)
        if graph_step == "graph_ds":
            # ???????????????????????????RabbitMQ????????????????????????RabbitMQ??????????????????????????????
            if len(params_json.get("graph_process", [])) > 1:
                code, res_df = graph_Service.get_ds_source_by_id(params_json.get("graph_process", []))
                if code == -1:
                    return Gview.BuFailVreturn(cause=res_df["cause"], code=res_df["code"],
                                               message=res_df["message"]), CommonResponseStatus.SERVER_ERROR.value

            # ??????graph_config_table??????rabbitmq_ds?????????0??????rabbitmq???1???rabbitmq
            code1, obj1 = graph_Service.ds_is_rabbitmq(params_json.get("graph_process"))
            if code1 == -1:
                return Gview.BuFailVreturn(cause=obj1["cause"], code=obj1["code"],
                                           message=obj1["message"]), CommonResponseStatus.SERVER_ERROR.value

            params_json["rabbitmq_ds"] = code1
        # ??????
        ret_code, ret_message = graph_Service.update(grapid, params_json, "-1")
        Logger.log_error("parameters:%s invalid" % params_json)
        if ret_code == CommonResponseStatus.SERVER_ERROR.value:
            return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                       message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value
        print('ret_res', ret_message)
        updateKnw(grapid)
        return Gview.BuVreturn(message=ret_message.get("res")), CommonResponseStatus.SUCCESS.value


@graph_controller_app.route('/getgraphdb', methods=["get"], strict_slashes=False)
@swag_from(swagger_old_response)
def getgraphdb():
    '''
    query database connection information
    ?????????????????????????????????
    ---
    '''
    ret_code, ret_message = graph_Service.getGraphDB()
    if ret_code == CommonResponseStatus.SERVER_ERROR.value:
        return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                   message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value
    return ret_message, CommonResponseStatus.SUCCESS.value


@graph_controller_app.route('/getbis', methods=["get"], strict_slashes=False)
@swag_from(swagger_old_response)
def getbis():
    """
    get base info switch
    """
    ret_code, ret_message = graph_Service.getbis()
    if ret_code == CommonResponseStatus.SERVER_ERROR.value:
        return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                   message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value
    return ret_message, CommonResponseStatus.SUCCESS.value


@graph_controller_app.route('/<graphid>', methods=["get"], strict_slashes=False)
@swag_from(swagger_old_response)
def getgraphbyid(graphid):
    '''
    query the graph
    ---
    parameters:
        -   name: 'graphid'
            in: 'path'
            description: 'graph id'
            required: true
            type: 'integer'
    '''
    if not graphid.isdigit():
        message = "The parameter graph id type must be int!"
        return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                   message=message), CommonResponseStatus.BAD_REQUEST.value
    # graph_id?????????
    code, ret = graph_Service.checkById(graphid)
    if code != 0:
        return jsonify(ret), 500
    ret_code, ret_message = graph_Service.getGraphById(graphid)

    if ret_code == CommonResponseStatus.SERVER_ERROR.value:
        return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                   message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value
    return ret_message, CommonResponseStatus.SUCCESS.value


@graph_controller_app.route('/<graph_step>/graphid=<graphid>', methods=["get"], strict_slashes=False,
                            endpoint="graph_step")
@swag_from(swagger_old_response)
def getgraphbystep(graphid, graph_step):
    '''
    get the entity class collection and its property collection in the specific graph configuration step
    ??????id???????????????????????????????????????entity???property
    graphid?????????id
    graph_step:["graph_InfoExt","graph_KMap","graph_KMerge"]
    ---
    parameters:
        -   name: 'graphid'
            in: 'path'
            description: 'graph id'
            required: true
            type: 'integer'
        -   name: 'graph_step'
            in: 'path'
            description: 'graph configuration step'
            required: true
            type: 'string'
            example: 'graph_InfoExt'
    '''
    if not graphid.isdigit():
        message = "The parameter graph id type must be int!"
        return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                   message=message), CommonResponseStatus.BAD_REQUEST.value
    ret_code, ret_message = graph_Service.getGraphById(graphid)
    if ret_code == CommonResponseStatus.SERVER_ERROR.value:
        return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                   message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value
    entity_message = graph_Service.get_entity_property(ret_message, graph_step)

    return entity_message, CommonResponseStatus.SUCCESS.value


@graph_controller_app.route('/infoext_list', methods=["post"], strict_slashes=False)
@swag_from(swagger_old_response)
def getbyinfoext():
    '''
    get the extraction rule according to the extraction file list
    ??????id???????????????????????????????????????????????????
    graphid?????????id
    graph_step:["graph_InfoExt","graph_KMap","graph_KMerge"]
    ---
    parameters:
        -   name: 'graphid'
            in: 'body'
            description: 'graph id'
            required: true
            type: 'integer'
            example: 116
        -   name: 'graph_step'
            in: 'body'
            description: 'graph configuration step'
            required: true
            type: 'string'
            example: 'graph_InfoExt'
        -   name: 'infoext_list'
            in: 'body'
            description: 'extraction file list containing data source name and file source'
            required: true
            type: 'array'
            example: [
              { "ds_name": "????????????1", "file_source": "???????????????fileid???tablename" },
              { "ds_name": "????????????1", "file_source": "???????????????fileid???tablename" }
            ]

    '''
    param_code, params_json, param_message = commonutil.getMethodParam()
    if param_code == 0:
        check_res, message = graphCheckParameters.checkparam_getinfoext(params_json)
        if check_res != 0:
            Logger.log_error("parameters:%s invalid" % params_json)
            return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                       message=message), CommonResponseStatus.BAD_REQUEST.value
        graphid = params_json['graphid']
        graph_step = params_json['graph_step']
        infoext_list = params_json['infoext_list']

        ret_code, ret_message = graph_Service.getGraphById(graphid)
        if ret_code == CommonResponseStatus.SERVER_ERROR.value:
            return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                       message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value
        if len(ret_message["res"][graph_step]) > 0:
            graph_step_info = ret_message["res"][graph_step]
            if len(infoext_list) > 0:
                obj = {}
                infoext_info = [i for i in graph_step_info if
                                {"ds_name": i['ds_name'], "file_source": i['file_source']} in infoext_list]
                obj["res"] = infoext_info
                return obj, CommonResponseStatus.SUCCESS.value
            else:
                ret_message["res"] = "infoext_list can not be []"
                return ret_message, CommonResponseStatus.SUCCESS.value
        else:
            ret_message["res"] = "%s is not exist" % graph_step
            return ret_message, CommonResponseStatus.SUCCESS.value
    else:
        return Gview.BuFailVreturn(cause=param_message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                   message="Incorrect parameter format"), CommonResponseStatus.BAD_REQUEST.value


@graph_controller_app.route('/check_kmapinfo', methods=["post"], strict_slashes=False)
@swag_from(swagger_old_response)
def check_kmapinfo():
    '''
    verify the mapping information
    ??????id???????????????????????????????????????????????????
    ??????????????????????????????check_kmapinfo???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????
    ???????????????3?????????????????????5??????????????????????????????????????????????????????????????????????????????????????????????????????????????????5????????????????????????????????????????????????0????????????1??????????????????????????????2???
    ???????????????4 ???????????????????????????5????????????????????????????????????????????????5???????????????????????????????????????0????????????1??????????????????????????????2???
    ---
    parameters:
        -   name: 'graphid'
            in: 'body'
            description: 'graph id'
            required: true
            type: 'integer'
            example: 116
        -   name: 'graph_KMap'
            in: 'body'
            description: 'details of the graph mapping'
            required: true
            type: 'array'
            example: [{
                  "otls_map": [
                    {
                      "otl_name": "test_json",
                      "entity_type": "test_json",
                      "property_map": [
                        { "otl_prop": "name", "entity_prop": "a1" },
                        { "otl_prop": "a1", "entity_prop": "a1" },
                        { "otl_prop": "a2", "entity_prop": "a2" }
                      ]
                    }
                  ],
                  "relations_map": []
                }]
    '''
    param_code, params_json, param_message = commonutil.getMethodParam()
    if param_code == 0:
        graphid = params_json.get("graphid", None)
        if not graphid or str(graphid) == "True":
            message = "The parameter graphid:%s is invalid!" % graphid
            return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                       message=message), CommonResponseStatus.BAD_REQUEST.value
        if not isinstance(graphid, int) or graphid < 0:
            message = "The parameter graphid:%s type must be int!" % graphid
            return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                       message=message), CommonResponseStatus.BAD_REQUEST.value
        ret_code, ret_message = graph_Service.getGraphById(graphid)
        if ret_code == CommonResponseStatus.SERVER_ERROR.value:
            return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                       message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value

        check_res, message, graph_KMap_check = graphCheckParameters.check_graph_KMap2(params_json, ret_message)
        if check_res != 0:
            Logger.log_info("The parameters:%s is invalid" % params_json)
            return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                       message=message), CommonResponseStatus.BAD_REQUEST.value
        return graph_KMap_check, CommonResponseStatus.SUCCESS.value


@graph_controller_app.route('/savenocheck', methods=["post"], strict_slashes=False)
@swag_from(swagger_old_response)
def savenocheck():
    '''
    save and exit
    ---
    parameters:
        -   name: 'graph_id'
            in: 'body'
            description: 'graph id'
            required: true
            type: 'integer'
            example: 4
        -   name: 'graph_baseInfo'
            in: 'body'
            description: 'graph basic information'
            required: false
            type: 'object'
        -   name: 'graph_ds'
            in: 'body'
            description: 'graph data source information'
            required: false
            type: 'object'
        -   name: 'graph_otl'
            in: 'body'
            description: 'graph ontology information'
            required: false
            type: 'object'
        -   name: 'graph_InfoExt'
            in: 'body'
            description: 'graph extraction information'
            required: false
            type: 'object'
        -   name: 'graph_KMap'
            in: 'body'
            description: 'graph mapping information'
            required: false
            type: 'object'
        -   name: 'graph_KMerge'
            in: 'body'
            description: 'graph merging information'
            required: false
            type: 'object'
    '''
    param_code, params_json, param_message = commonutil.getMethodParam()
    if param_code == 0:
        check_res, message = graphCheckParameters.savenoCheckPar(params_json)
        if check_res != 0:
            Logger.log_error("parameters:%s invalid" % params_json)
            return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                       message=message), CommonResponseStatus.BAD_REQUEST.value
        ret_code, ret_message = graph_Service.savenocheck(params_json)
        if ret_code == CommonResponseStatus.SERVER_ERROR.value:
            return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                       message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value
        return ret_message, CommonResponseStatus.SUCCESS.value

    else:
        return Gview.BuFailVreturn(cause=param_message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                   message="Incorrect parameter format"), CommonResponseStatus.BAD_REQUEST.value


@graph_controller_app.route('/getdsbygraphid', methods=["get"], strict_slashes=False)
@swag_from(swagger_old_response)
def getdsbygraphids():
    '''
    get data source list by graph id
    ????????????id?????????????????????
    ????????????????????????????????????????????????????????????????????????id???1????????????
    ---
    parameters:
        -   name: id
            in: query
            description: graph id
            required: true
            type: integer
            example: 1
        -   name: type
            in: query
            description: ???????????????filter:???????????????????????????????????????unfilter:??????????????????????????????
            type: string
            example: 'filter'
    '''
    param_code, params_json, param_message = commonutil.getMethodParam()
    if param_code == 0:
        check_res, message = graphCheckParameters.getdsbygraphidPar(params_json)

        if check_res != 0:
            Logger.log_error("parameters:%s invalid" % params_json)
            return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                       message=message), CommonResponseStatus.BAD_REQUEST.value
        ret_code, ret_message = graph_Service.getdsbygraphid(params_json)
        if ret_code == CommonResponseStatus.SERVER_ERROR.value:
            return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                       message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value

        return ret_message, CommonResponseStatus.SUCCESS.value
    else:
        return Gview.BuFailVreturn(cause=param_message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                   message="Incorrect parameter format"), CommonResponseStatus.BAD_REQUEST.value


@graph_controller_app.route('/delbyids', methods=["POST"], strict_slashes=False)
@swag_from(swagger_new_response)
def graphDeleteByIds():
    '''
    delete graph by graph ids
    ??????????????????
    ---
    parameters:
        -   name: graphids
            in: body
            description: list of graph ids to be deleted
            required: true
            type: array
            example: [1, 2]
        -   name: knw_id
            in: body
            description: knowledge network id
            required: true
            type: integer
            example: 1
    '''
    runs, noAuthority, noExist, normal = [], [], [], []
    mess = ""
    obj, obj_code = {}, 200
    # ????????????
    param_code, params_json, param_message = commonutil.getMethodParam()
    if param_code != 0:
        error_link = ''
        code = CommonResponseStatus.PARAMETERS_ERROR.value
        detail = 'Incorrect parameter format'
        desc = "Incorrect parameter format"
        solution = 'Please check your parameter format'
        return Gview.TErrorreturn(code, desc, solution, detail,
                                  error_link), CommonResponseStatus.BAD_REQUEST.value
    # ????????????
    check_res, message = graphCheckParameters.graphDelPar(params_json)
    if check_res != 0:
        Logger.log_error("parameters:%s invalid" % params_json)
        solution = "Please check parameters"
        code = CommonResponseStatus.PARAMETERS_ERROR.value
        desc = "parameters error"
        error_link = ""
        return Gview.TErrorreturn(code, desc, solution, message,
                                  error_link), CommonResponseStatus.BAD_REQUEST.value
    ret_code, ret_message = knw_service.check_knw_id(params_json, delete_graph=True)
    if ret_code != 200:
        code = ret_message["code"]
        if code == CommonResponseStatus.GRAPH_NOT_KNW.value:
            code = CommonResponseStatus.GRAPH_NOT_KNW.value
        else:
            code = CommonResponseStatus.INVALID_KNW_ID.value
        return Gview.BuFailVreturn(cause=ret_message["des"], code=code,
                                   message=ret_message["detail"]), CommonResponseStatus.SERVER_ERROR.value
    graphids = params_json["graphids"]
    # ?????????????????????
    res_mess, res_code = graph_Service.getStatusByIds(graphids)
    if res_code != 0:
        return Gview.TErrorreturn(res_mess["code"], res_mess["message"], res_mess["solution"], res_mess["cause"],
                                  ""), CommonResponseStatus.SERVER_ERROR.value
    # ???????????????graphId??????
    runs = res_mess["runs"]

    # ??????????????????id
    res, code = graph_Service.getNoExistIds(graphids)
    if code != 0:
        return Gview.TErrorreturn(res["code"], res["message"], res["solution"], res["cause"],
                                  ""), CommonResponseStatus.SERVER_ERROR.value
    noExist = res["noExist"]
    normal = list(set(graphids) - set(noExist) - set(runs))
    # ????????????
    if len(graphids) == 1:
        # ??????
        if len(normal) == 1:
            mess += "???????????????%s; " % ",".join(map(str, normal))
            obj, obj_code = json.dumps({"state": "sucess"}), CommonResponseStatus.SUCCESS.value
        # ?????????
        if len(noExist) != 0:
            mess += "%s ?????????; " % ",".join(map(str, noExist))
            mess += "???????????????%s; " % ",".join(map(str, normal))
            obj, obj_code = json.dumps({"state": "sucess"}), CommonResponseStatus.SUCCESS.value
        if len(runs) == 1:
            obj, obj_code = {"Cause": "?????????????????????????????????????????????????????????????????????????????????",
                             "Code": CommonResponseStatus.SINGLE_RUNNING.value,
                             "message": "????????????????????????????????????"}, CommonResponseStatus.SERVER_ERROR.value
        if len(noAuthority) == 1:
            obj, obj_code = {"Cause": "????????????????????????????????????????????????",
                             "Code": CommonResponseStatus.SINGLE_PERMISSION.value,
                             "message": "????????????"}, CommonResponseStatus.SERVER_ERROR.value
    # ????????????
    else:
        # ???????????????
        if len(noExist) == len(graphids):
            # mess += "%s ?????????; " % ",".join(map(str, noExist))
            obj, obj_code = {"state": "sucess"}, CommonResponseStatus.SUCCESS.value
        # ????????????
        if len(runs) > 0 and len(noAuthority) == 0 and len(normal) == 0:
            obj, obj_code = {"Cause": "??????????????????????????????????????????????????????????????????????????????",
                             "Code": CommonResponseStatus.ALL_RUNNING.value,
                             "message": "????????????????????????????????????"}, CommonResponseStatus.SERVER_ERROR.value
        # ?????? + ??????
        if len(runs) > 0 and len(noAuthority) == 0 and len(normal) > 0:
            obj, obj_code = {"Cause": "?????????????????????????????????????????????????????????????????????????????????",
                             "Code": CommonResponseStatus.RUNNING_AND_NORMAL.value,
                             "message": "????????????????????????????????????"}, CommonResponseStatus.SERVER_ERROR.value
        # ?????? + ??????
        if len(runs) > 0 and len(noAuthority) > 0 and len(normal) == 0:
            obj, obj_code = {"Cause": "???????????????????????????????????????????????????????????????",
                             "Code": CommonResponseStatus.RUNNING_AND_PERMISSION.value,
                             "message": "????????????????????????????????????, ????????????????????????"}, CommonResponseStatus.SERVER_ERROR.value
        # ?????? + ??????
        if len(runs) == 0 and len(noAuthority) > 0 and len(normal) > 0:
            obj, obj_code = {"Cause": "????????????????????????????????????????????????",
                             "Code": CommonResponseStatus.PERMISSION_AND_NORMAL.value,
                             "message": "????????????????????????"}, CommonResponseStatus.SERVER_ERROR.value
        # ???????????????
        if len(runs) == 0 and len(noAuthority) > 0 and len(normal) == 0:
            obj, obj_code = {"Cause": "?????????????????????????????????????????????",
                             "Code": CommonResponseStatus.ALL_PERMISSION.value,
                             "message": "????????????????????????"}, CommonResponseStatus.SERVER_ERROR.value
        # ?????? + ?????? + ??????
        if len(runs) > 0 and len(noAuthority) > 0 and len(normal) > 0:
            obj, obj_code = {"Cause": "????????????????????????????????????????????????????????????",
                             "Code": CommonResponseStatus.RUNNING_AND_PERMISSION_AND_NORMAL.value,
                             "message": "????????????????????????????????????, ????????????????????????"}, CommonResponseStatus.SERVER_ERROR.value
        # ??????
        if len(runs) == 0 and len(noAuthority) == 0 and len(normal) > 0:
            obj, obj_code = json.dumps({"state": "sucess"}), CommonResponseStatus.SUCCESS.value
    # ????????????????????????
    res, code = graph_Service.get_upload_id(normal)
    if code != 0:
        return Gview.TErrorreturn(res["code"], res["message"], res["solution"], res["cause"],
                                  ""), CommonResponseStatus.SERVER_ERROR.value
    res = res.to_dict('records')
    if len(res) > 0:
        obj_code = 500
        desc = "graph upload can not delete"
        solution = "please wait upload finished"
        cause = "graph upload can not delete"
        return Gview.TErrorreturn(CommonResponseStatus.GRAPH_UPLOAD.value, desc, solution, cause, ""), obj_code
    if len(normal) > 0:
        # ?????????????????????
        res, code = graph_Service.deleteGraphByIds(normal)
        if code != 0:
            return Gview.TErrorreturn(res["code"], res["message"], res["solution"], res["cause"],
                                      ""), CommonResponseStatus.SERVER_ERROR.value
        # ?????????????????????????????????
        knw_id = params_json["knw_id"]
        deleteRelation(knw_id, normal)

    if len(noExist) != 0:
        mess += "%s ?????????; " % ",".join(map(str, noExist))
    if len(runs) != 0:
        mess += "%s ????????????; " % ",".join(map(str, runs))
    if len(normal) > 0:
        mess += "???????????????%s; " % ",".join(map(str, normal))
    Logger.log_info(mess)
    if len(normal) > 0:
        updateKnw(normal[0])
    if obj_code == 200:
        return obj, 200
    solution = "????????????????????????????????????????????????????????????"
    return Gview.TErrorreturn(obj["Code"], obj["message"], solution, obj["Cause"], ""), obj_code


@graph_controller_app.route('/ds/<graphid>', methods=["GET"], strict_slashes=False)
@swag_from(swagger_old_response)
def graphDsList(graphid):
    '''
    get data source list in the graph editing process
    ???????????????????????????????????????
    ---
    parameters:
        -   name: graphid
            in: path
            required: true
            description: graph id
            type: integer
        -   name: page
            in: query
            required: true
            description: page
            type: integer
        -   name: size
            in: query
            required: true
            description: number of display items per page
            type: integer
        -   name: order
            in: query
            required: false
            description: "'ascend'(default) display items in time sequence, new items on the top; else 'descend'"
            type: string
    '''
    if not graphid.isdigit():
        message = "The parameter graph id type must be int!"
        return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                   message=message), CommonResponseStatus.BAD_REQUEST.value
    # ????????????
    param_code, params_json, param_message = commonutil.getMethodParam()
    if param_code != 0:
        return Gview.BuFailVreturn(cause=param_message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                   message="Incorrect parameter format"), CommonResponseStatus.BAD_REQUEST.value
    # ????????????
    check_res, message = graphCheckParameters.getGraphDSList(params_json)
    if check_res != 0:
        Logger.log_error("parameters:%s invalid" % params_json)
        return Gview.BuFailVreturn(cause=message, code=CommonResponseStatus.PARAMETERS_ERROR.value,
                                   message=message), CommonResponseStatus.BAD_REQUEST.value

    ret_code, ret_message = graph_Service.getDsAll(params_json)
    if ret_code == CommonResponseStatus.SERVER_ERROR.value:
        return Gview.BuFailVreturn(cause=ret_message["cause"], code=ret_message["code"],
                                   message=ret_message["message"]), CommonResponseStatus.SERVER_ERROR.value
    return ret_message, CommonResponseStatus.SUCCESS.value


@graph_controller_app.route("/adv-search-config/kglist-conf/<net_id>", methods=["GET"], strict_slashes=False)
@swag_from(swagger_old_response)
def get_adv_search(net_id):
    '''
    get knowledge graph list configuration by network id
    ---
    parameters:
        -   name: net_id
            in: path
            required: true
            description: network id
            type: integer
    '''
    # ????????????????????????????????????
    net_ids = knw_service.get_graph_by_knw_id_s(net_id)
    net_ids = list(net_ids.values())
    config_ids = set(net_ids)

    # ???????????????????????????????????????????????????????????????
    ids = graph_dao.get_IdByConfigId(config_ids)

    # ??????????????????????????????id??????id????????????????????????????????????????????????
    result = graph_Service.get_graph_conf_list(ids)
    forReturen = {"res": result}
    return jsonify(forReturen), 200


@graph_controller_app.route("/output", methods=["POST"], strict_slashes=False)
@swag_from(swagger_new_response)
def graph_config_output():
    '''
    export the knowledge graph
    ---
    parameters:
        -   name: ids
            in: body
            required: true
            description: list of graph ids to be exported. If its length exceeds 1, an error will be reported.
            type: array
            example: ["86"]
    '''
    config_ids = request.json.get("ids")
    if len(config_ids) > 1:
        return Gview.TErrorreturn(
            "Builder.controller.graph_config.ids_length.too_much_id",
            "too much id",
            "please send a signal id",
            "too much id",
            "",
        ), 500
    for config_id in config_ids:
        code, ret = graph_Service.checkById(config_id)
        if code != 0:
            return Gview.TErrorreturn(
                "Builder.controller.graph_controller.check_config_id.config_not_exists",
                ret["cause"], ret["cause"], ret["message"], ""
            ), 500

        if task_dao.check_task_status(config_id, "normal"):
            return Gview.TErrorreturn(
                "Builder.controller.graph_config.task_status.task_running",
                "graph task is not normal or graph status is not finish",
                "Please check graph or task status",
                "graph task is not normal or graph status is not finish",
                "",
            ), 500
        if task_dao.check_storage_type(config_id):
            return Gview.TErrorreturn(
                "Builder.controller.graph_config.check_storage_type.storage_error",
                "storage type is not nebula",
                "you cant output a graph that not nebula",
                "graph not nebula",
                "",
            ), 500
    # ????????????????????????ids????????????????????????
    file_path, file_name = graph_Service.graph_output(config_ids)
    return send_from_directory(file_path, file_name, as_attachment=True)


@graph_controller_app.route("/input", methods=["POST"], strict_slashes=False)
@swag_from(swagger_new_response)
def graph_config_input():
    '''
    import the knowledge graph
    ---
    parameters:
        -   name: knw_id
            in: body
            required: true
            description: knowledge network id
            type: integer
        -   name: file
            in: body
            required: true
            description: data file to be uploaded
            type: file
        -   name: graph_id
            in: body
            required: true
            description: graph id
            type: integer
        -   name: method
            in: body
            required: true
            description: '0: skip when graph id exists; 1: update when graph id exists'
            type: integer
    consumes:
        -   application/x-www-form-urlencoded
    '''
    # ??????form???????????????????????????id?????????id
    graph_id = request.form.get("graph_id")
    method = request.form.get("method")
    knw_id = request.form.get("knw_id", None)
    if knw_id:
        # ?????????????????????????????????
        if not knw_service.check_exists_by_knw_id(knw_id):
            return Gview.TErrorreturn(
                "Builder.controller.graph_config.check_knw.knw_not_exists",
                "knw is not found",
                "please use a useful knw id",
                "knw is not found",
                "",
            ), 500

    # ??????graph_id??????????????????????????????????????????
    df = graph_dao.getGraphDBbyId(graph_id)
    res = df.to_dict("records")
    if len(res) == 0:
        return Gview.TErrorreturn(
            "Builder.controller.graph_config.check_graph_db.graph_db_not_exists",
            "graph_id is not found",
            "please use a useful graph",
            "graph_id is not found",
            "",
        ), 500
    db_type = res[0]['type']
    if db_type != 'nebula':
        return Gview.TErrorreturn(
            "Builder.controller.graph_config.check_graph_db.graph_db_type_error",
            "graph db type error",
            "please choose nebula type",
            "import only supports nebula",
            "",
        ), 500
    # ????????????
    file_name = secure_filename("{0}_input".format(str(uuid.uuid1())))
    if os.path.exists(file_name):
        os.remove(file_name)
    else:
        os.mknod(file_name)
    try:
        # ???????????????????????????????????????
        files = request.files.getlist("file")
    except Exception as e:
        return Gview.TErrorreturn(
            "Builder.controller.graph_config.get_file.unexpect_error",
            "get file error",
            "send a file",
            e.__str__(),
            "",
        ), 500
    try:
        for file in files:
            file.save(file_name)
            ret, status = graph_Service.graph_input(knw_id, graph_id, file_name, method)
            if status != 200:
                return ret, 500
            os.remove(file_name)
    except Exception as e:
        return Gview.TErrorreturn(
            "Builder.controller.graph_config.unexception.unexpect_error",
            "unexception error",
            "get more infomation in details",
            e.__str__(),
            "",
        ), 500

    return "True", 200


@graph_controller_app.route('/info/basic', methods=["get"], strict_slashes=False)
@swag_from(swagger_new_response)
def get_graph_info_basic():
    '''
    get the graph information
    ---
    parameters:
        -   name: graph_id
            in: query
            required: true
            description: graph id
            type: integer
        -   name: is_all
            in: query
            required: false
            description: 'True??????????????????????????????key????????????; False?????????????????????key?????????????????????'
            type: boolean
        -   name: 'key'
            in: query
            required: false
            description: ?????????????????????????????????
            # type: array
    '''
    try:
        graph_id = request.args.get('graph_id')
        is_all = request.args.get('is_all', 'False')
        key = request.args.get('key')
        # ????????????
        # graph_id
        if not graph_id or not graph_id.isdigit():
            code = codes.Builder_GraphController_GetGraphInfoBasic_ParamError
            return Gview2.TErrorreturn(code,
                                      arg='graph_id',
                                      description='?????????graph_id????????????graph_id????????????'), 400
        # is_all
        if is_all.lower() == 'true':
            is_all = True
        elif is_all.lower() == 'false':
            is_all = False
        else:
            code = codes.Builder_GraphController_GetGraphInfoBasic_ParamError
            return Gview2.TErrorreturn(code,
                                      arg='is_all',
                                      description='is_all?????????True?????????False???'), 400
        # key????????????
        if key:
            try:
                key = eval(key)
                if not isinstance(key, list):
                    code = codes.Builder_GraphController_GetGraphInfoBasic_KeyTypeError
                    data = Gview2.TErrorreturn(code)
                    return data, 400
            except Exception:
                code = codes.Builder_GraphController_GetGraphInfoBasic_KeyTypeError
                data = Gview2.TErrorreturn(code)
                return data, 400
        # ????????????
        code, data = graph_Service.get_graph_info_basic(graph_id, is_all, key)
        if code != codes.successCode:
            return data, 400
        return data, 200
    except Exception as e:
        code = codes.Builder_GraphController_GetGraphInfoBasic_UnknownError
        return Gview2.TErrorreturn(code,
                                   cause=str(e),
                                   description=str(e)), 400

@graph_controller_app.route('/info/onto', methods=["get"], strict_slashes=False)
@swag_from(swagger_new_response)
def get_graph_info_onto():
    '''
    get the ontology of the graph
    ---
    parameters:
        -   name: graph_id
            in: query
            required: true
            description: graph id
            type: integer
    '''
    try:
        graph_id = request.args.get('graph_id')
        if not graph_id or not graph_id.isdigit():
            code = codes.Builder_GraphController_GetGraphInfoOnto_ParamError
            return Gview2.TErrorreturn(code,
                                       arg='graph_id',
                                       description='?????????graph_id????????????graph_id????????????'), 400
        code, data = graph_Service.get_graph_info_onto(graph_id)
        if code != codes.successCode:
            return data, 400
        return data, 200
    except Exception as e:
        code = codes.Builder_GraphController_GetGraphInfoOnto_UnknownError
        return Gview2.TErrorreturn(code,
                                   cause=str(e),
                                   description=str(e)), 400

@graph_controller_app.route('/info/count', methods=["get"], strict_slashes=False)
@swag_from(swagger_new_response)
def get_graph_info_count():
    '''
    get the count of the graph
    ---
    parameters:
        -   name: graph_id
            in: query
            required: true
            description: graph id
            type: integer
    '''
    try:
        graph_id = request.args.get('graph_id')
        if not graph_id or not graph_id.isdigit():
            code = codes.Builder_GraphController_GetGraphInfoCount_ParamError
            return Gview2.TErrorreturn(code,
                                       arg='graph_id',
                                       description='?????????graph_id????????????graph_id????????????'), 400
        code, data = graph_Service.get_graph_info_count(graph_id)
        if code != codes.successCode:
            return data, 400
        return data, 200
    except Exception as e:
        code = codes.Builder_GraphController_GetGraphInfoCount_UnknownError
        return Gview2.TErrorreturn(code,
                                   cause=str(e),
                                   description=str(e)), 400

@graph_controller_app.route('/info/detail', methods=["get"], strict_slashes=False)
@swag_from(swagger_new_response)
def get_graph_info_detail():
    '''
    get the configuration details of entities or edges in the graph
    ---
    parameters:
        -   name: graph_id
            in: query
            required: true
            description: graph id
            type: integer
        -   name: type
            in: query
            required: true
            description: entity or edge
            type: string
        -   name: name
            in: query
            required: true
            description: name of the entity or the edge
            type: string
    '''
    try:
        graph_id = request.args.get('graph_id')
        otl_type = request.args.get('type')
        name = request.args.get('name')
        if not graph_id or not graph_id.isdigit():
            code = codes.Builder_GraphController_GetGraphInfoDetail_ParamError
            return Gview2.TErrorreturn(code,
                                       arg='graph_id',
                                       description='?????????graph_id????????????graph_id????????????'), 400
        if not otl_type:
            code = codes.Builder_GraphController_GetGraphInfoDetail_ParamError
            return Gview2.TErrorreturn(code,
                                       arg='type',
                                       description='?????????type??????'), 400
        if otl_type not in ['entity', 'edge']:
            code = code = codes.Builder_GraphController_GetGraphInfoDetail_ParamError
            return Gview2.TErrorreturn(code,
                                       arg='type',
                                       description='type??????entity???edge, ??????type???{}'.format(otl_type)), 400
        if not name:
            code = codes.Builder_GraphController_GetGraphInfoDetail_ParamError
            return Gview2.TErrorreturn(code,
                                       arg='name',
                                       description='?????????name??????'), 400
        code, data = graph_Service.get_graph_info_detail(graph_id, otl_type, name)
        if code != codes.successCode:
            return data, 400
        return data, 200
    except Exception as e:
        code = codes.Builder_GraphController_GetGraphInfoDetail_UnknownError
        return Gview2.TErrorreturn(code,
                                   cause=str(e),
                                   description=str(e)), 400

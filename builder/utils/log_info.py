#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2021/3/17 14:26
# @Author  : yuan.qi
# @Email   : yuan.qi@aishu.cn
# @File    : log_info.py

import logging
import json
import datetime
import math

REMOVE_ATTR = ["process", "processName", "threadName", "thread", "funcName", "lineno", "pathname", "levelno", "name",
               "filename", "module", "exc_text", "stack_info", "created", "msecs", "relativeCreated",
               "exc_info", "msg", "args"]


class JSONFormatter(logging.Formatter):
    def format(self, record):
        extra = self.build_record(record)
        self.set_format_time(extra)  # set time
        self.set_attrs(extra)
        self.set_resources(extra)
        self.set_others(extra)
        if isinstance(record.msg, dict):
            if not record.msg.get("Body"):
                raise Exception("if pass a dict,key `Body` is needed")
            if record.msg.get("Attributes"):
                extra["Attributes"] = record.msg.get("Attributes")
            if record.msg.get("SpanId"):
                extra["SpanId"] = record.msg.get("SpanId")
            if record.msg.get("TraceId"):
                extra["TraceId"] = record.msg.get("TraceId")
            if record.msg.get("Body"):
                extra['Body'] = record.msg.get("Body")
            else:
                extra['Body'] = record.msg  # set message
        else:
            if record.args:
                extra['Body'] = "'" + record.msg + "'," + str(record.args).strip('()')
            else:
                extra['Body'] = record.msg
        extra["Severity"] = extra["levelname"]
        del extra["levelname"]
        if self._fmt == 'pretty':
            return json.dumps(extra, indent=1, ensure_ascii=False)
        else:
            return json.dumps(extra, ensure_ascii=False)

    @classmethod
    def build_record(cls, record):
        return {
            attr_name: record.__dict__[attr_name]
            for attr_name in record.__dict__
            if attr_name not in REMOVE_ATTR
        }

    @classmethod
    def set_format_time(cls, extra):
        now = math.floor(datetime.datetime.now().timestamp())
        extra['Timestamp'] = now
        return now

    @classmethod
    def set_attrs(cls, extra):
        extra["Attributes"] = {}
        return None

    @classmethod
    def set_resources(cls, extra):
        extra["Resource"] = {}
        return None

    @classmethod
    def set_others(cls, extra):
        extra["TraceId"] = ""
        extra["SpanId"] = ""
        return None


class LogModel(dict):
    @property
    def attr(self):
        return self["Attributes"]

    @attr.setter
    def attr(self, value):
        self["Attributes"] = value

    @property
    def span_id(self):
        return self["SpanId"]

    @span_id.setter
    def span_id(self, value):
        self["SpanId"] = value

    @property
    def trace_id(self):
        return self["TraceId"]

    @trace_id.setter
    def trace_id(self, value):
        self["TraceId"] = value

    @property
    def body(self):
        return self["Body"]

    @body.setter
    def body(self, value):
        self["Body"] = value


def _set_log_model(body, span_id="", trace_id="", attributes={}) -> LogModel:
    if not body:
        raise Exception("body can not be null")
    model = LogModel()
    model.trace_id = trace_id
    model.span_id = span_id
    model.attr = attributes
    model.body = body
    return model


class Log:
    def __init__(self):
        # ---------------------?????????-------------------------------------------------
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)  # ???????????????????????????DEBUG
        # write log to file
        handler = logging.FileHandler("/var/log/logging.txt")  # ?????????????????????????????????????????????
        handler.setLevel(logging.INFO)  # ????????????????????????????????????????????????????????????????????????????????????????????????????????????
        handler.setFormatter(JSONFormatter())  # ?????????????????????????????????????????????
        self.logger.addHandler(handler)  # ??????????????????handler
        # write log to console
        handler_console = logging.StreamHandler()  # ?????????????????????????????????
        handler_console.setLevel(logging.INFO)  # ??????????????????????????????????????????
        self.logger.addHandler(handler_console)  # ?????????????????????handler
        # handler_console.setFormatter(JSONFormatter("pretty"))  # ???????????????????????????????????????????????????json??????????????????????????????pretty????????????????????????????????????

    def log_info(self, body):
        self.logger.info(str(body))

    def log_error(self, err):
        self.logger.error(str(err))

    def set_log_model(self, body, span_id="", trace_id="", attributes={}) -> LogModel:
        if not body:
            raise Exception("body can not be null")
        model = LogModel()
        model.trace_id = trace_id
        model.span_id = span_id
        model.attr = attributes
        model.body = body
        return model


Logger = Log()

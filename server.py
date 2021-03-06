from  flask import Flask,send_file,jsonify,request,redirect

import datetime
import logging
from tornado.wsgi import WSGIContainer
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
import prepare
import stock_sql
import trainning
import  evaluate
import data_show
from flask_cors import *
import json

def after_request(resp):
    resp.headers["Access-Control-Allow-Origin"]='*'
    resp.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE,OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = "Referer,Accept,Origin,User-Agent,x-requested-with,content-type"
    return resp

app = Flask(__name__)
CORS(app, supports_credentials=True)
#app.after_request(after_request)

def logger_config():
    file_name="".join(["log/flask_log/",datetime.datetime.now().strftime("%Y%m%d"),".log"])
    log_level = logging.DEBUG
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
    #输出到文件
    file_handler= logging.FileHandler(file_name,encoding="utf-8")
    file_handler.setLevel( log_level)
    file_handler.setFormatter(log_format)
    #输出到控制台
    console_handler =logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_format)
    #获取logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers.clear()
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

logger = logger_config()


@app.route("/getList",methods=['GET'])
def getList():
    print("getList called")
    data = stock_sql.getStockFrame()
    return data.to_json(orient='records',force_ascii=False)



@app.route("/getPredictData",methods=['POST'])
def getPredictData():
    data=request.json
    stock_info=data["stock"]
    preTrainData=prepare.getPredictTrainnData(stock_info)
    header= data_show.getHeader()
    column_x ,_=prepare.columnSplit()
    res={
        "index":column_x,
        "data":preTrainData.tolist(),
        "header":header
    }
    return res


@app.route("/getTestData",methods=['POST'])
def getTrainData():
    data = request.json
    stock_info = data["stock"]
    realData,predictData =trainning.testing(stock_info)
    xAxis = data_show.getDateTime(stock_info).astype(str)
    xAxis=xAxis.reshape(xAxis.shape[0]).tolist()
    res = {
        "realData":  realData.reshape(realData.shape[0]).tolist(),
        "predictData":predictData.reshape(predictData.shape[0]).tolist(),
        "xAxis" :  [n[2:] for n in xAxis]  # 舍去日期前两位
    }
    return res

@app.route('/getRate',methods=["POST"])
def getRate():
    data = request.json
    stock_info = data["stock"]
    realData, predictData = trainning.testing(stock_info)
    res={
        "explained" :evaluate.explained_variance_score(realData,predictData),
        "mean":evaluate.mean_squared_error(realData,predictData),
        "r2": evaluate.r2_socre(realData,predictData),
    }
    return  res

@app.route('/getUpDown',methods=["POST"])
def getUpDown():
    data = request.json
    stock_info = data["stock"]
    realData, predictData = trainning.testing(stock_info)
    closeColnum = prepare.getTrianColnum(stock_info)
    real_up, pred_up, count, total =evaluate.upDownfit(closeColnum,realData,predictData)
    xAxis = data_show.getDateTime(stock_info).astype(str)
    xAxis = xAxis.reshape(xAxis.shape[0]).tolist()
    res={
        "real_up" : real_up.reshape(real_up.shape[0]).tolist(),
        "pred_up":pred_up.reshape(pred_up.shape[0]).tolist(),
        "fit_count":count,
        "total_count":total,
        "xAxis": [n[2:] for n in xAxis]  # 舍去日期前两位
    }
    return  res

@ app.route("/getStockInfo",methods=["POST"])
def getStockInfo():
    data = request.json
    stock_info = data["stock"]
    df = stock_sql.getStockInfo(stock_info)
    return df.to_json(orient='records', force_ascii=False)

if __name__ == '__main__':
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(8080)
    IOLoop.current().start()
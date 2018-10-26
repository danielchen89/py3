# encoding: utf-8
import hashlib, urllib, base64, time, requests, os,sys, smtplib
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

#list = [
#    ['smokingTest', 'fanyuyu', 'secrets'],
#]


class CrsUser(dict):
    def __init__(self, userDict):
        self._appKey = userDict["appKey"]
        self._appSecret = userDict["appSecret"]
        self._searcherUrl = userDict["searcherUrl"]
        self._targetUrl = userDict["targetUrl"]
        self._type = userDict["type"]

    def getAppKey(self):
        return self._appKey

    def getAppSecret(self):
        return self._appSecret

    def getSearcherUrl(self):
        return self._searcherUrl

    def getTargetUrl(self):
        return self._targetUrl

    def getType(self):
        return self._type

# 签名 new
class Auth(object):
    AUTH_ERROR_MISSING_PARAMS = -1
    AUTH_ERROR_KEY_MISMATCH = -2
    AUTH_ERROR_INVALID_SIGNATURE = -3
    _timestamp = ''

    def __init__(self, key, secret):
        self._key = key
        self._secret = secret

    def _genSign(self, params):
        paramsStr = ''.join(['%s%s' % (key, params[key]) for key in sorted(params.keys())]) + self._secret
        return hashlib.sha256(paramsStr.encode("utf8")).hexdigest()

    def genTimeStamp(self):
        self._timestamp = str(int(time.time() * 1000))

    def getTimeStamp(self):
        return self._timestamp

    def signParams(self, params):
        res = dict(params)
        res['timestamp'] = self._timestamp
        res['appKey'] = self._key
        res['signature'] = self._genSign(res)
        return res

    def checkSign(self, params):
        copy = dict(params)
        for key in ['timestamp', 'appKey', 'signature']:
            if key not in copy:
                return False, Auth.AUTH_ERROR_MISSING_PARAMS
        if copy['appKey'] != self._key:
            return False, Auth.AUTH_ERROR_KEY_MISMATCH
        sign = copy['signature']
        del copy['signature']
        if sign != self._genSign(copy):
            return False, Auth.AUTH_ERROR_INVALID_SIGNATURE
        return True, None


# 签名 old
class AuthOld(object):
    AuthOld_ERROR_MISSING_PARAMS = -1
    AuthOld_ERROR_KEY_MISMATCH = -2
    AuthOld_ERROR_INVALID_SIGNATURE = -3

    def __init__(self, key, secret):
        self._key = key
        self._secret = secret

    def _genSign(self, params):
        paramsStr = ''.join(['%s%s' % (key, params[key]) for key in sorted(params.keys())]) + self._secret
        return hashlib.sha1(paramsStr.encode('utf-8')).hexdigest()

    def signParams(self, params, date=None):
        if date == None:
            date = datetime.utcnow()
        if not isinstance(date, str):
            date = date.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        res = dict(params)
        res['date'] = date
        res['appKey'] = self._key
        res['signature'] = self._genSign(res)
        return res

    def checkSign(self, params):
        copy = dict(params)
        for key in ['date', 'appKey', 'signature']:
            if key not in copy:
                return False, AuthOld.AuthOld_ERROR_MISSING_PARAMS
        if copy['appKey'] != self._key:
            return False, AuthOld.AuthOld_ERROR_KEY_MISMATCH
        sign = copy['signature']
        del copy['signature']
        if sign != self._genSign(copy):
            return False, AuthOld.AuthOld_ERROR_INVALID_SIGNATURE
        return True, None


# def sendMail(text):
#     ret = True
#     try:
#         msg = MIMEMultipart('alternative')
#         # msg['Subject'] = "AliveTest"
#         part1 = MIMEText(text, 'plain')
#         msg.attach(part1)
#         msg['From'] = formataddr(["crs-smoke-tester", my_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
#         msg['To'] = formataddr(["devops-crs", my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
#         msg['Subject'] = "CRS Smoking Test Failed"  # 邮件的主题
#         server = smtplib.SMTP_SSL("smtp.exmail.qq.com", 465)  # qq企业邮箱
#         server.login(my_sender, my_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
#         server.sendmail(my_sender, [my_user, 'fanyuyu@sightp.com'],
#                         msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
#         server.quit()  # 关闭连接
#     except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
#         ret = False
#     return ret


def getImage(imagename = ""):
    test_path = os.path.normpath(os.path.dirname(__file__) + '/TestData/' + imagename)
    return test_path

def assemble_crs_test_request(url,userObject, params):
    if userObject.getType() == "old":
        auth = AuthOld(userObject.getAppKey(), userObject.getAppSecret())
        date = auth.signParams(params)['date']
        signature = auth.signParams(params)['signature']
        params["date"] = date
        param_url = urllib.parse.urlencode(params)
        request_params = param_url + "&appKey=" + userObject.getAppKey() + "&signature=" + signature

    else:
        param_url = urllib.parse.urlencode(params)
        auth = Auth(userObject.getAppKey(), userObject.getAppSecret())
        auth.genTimeStamp()
        timestamp = auth.getTimeStamp()
        signature = auth.signParams(params)['signature']
        request_params = "appKey=" + userObject.getAppKey() + "&signature=" + signature + \
                         "&" + param_url + "&timestamp=" + timestamp
    url = url + request_params
    return url


def post_assemble_crs_test_request(url, userObject,params):
    if userObject.getType() == "old":
        auth = AuthOld(userObject.getAppKey(), userObject.getAppSecret())
        date = auth.signParams(params)['date']
        params["date"] = date
    else:
        auth = Auth(userObject.getAppKey(), userObject.getAppSecret())
        auth.genTimeStamp()
        timestamp = auth.getTimeStamp()
        params["timestamp"] = timestamp

    signature = auth.signParams(params)['signature']
    params["appKey"] = userObject.getAppKey()
    params["signature"] = signature
    return url

# target API

def _testCRSTargetsList(userObject,last="", limit=1):
    api_url = userObject.getTargetUrl()+"/targets/?"
    print(api_url)
    params = dict()
    if not last == "":
        params['last'] = last
    else:
        last = str(int(time.time() * 1000))
    params['limit'] = limit
    assemble_url = assemble_crs_test_request(api_url,userObject,params)
    # print(assemble_url)
    with requests.get(assemble_url) as response:
        try:
            print("_testCRSTargetsList OK")
            return response.json()
        except:
            print(response)
            print("targetList 返回值异常")

def _testCRSTargetsAdd(userObject,image, active="1", name="trackTest", size="20", type="ImageTarget",allowSimilar="0",meta = "test"):
    api_url = userObject.getTargetUrl()+"/targets/"
    print(api_url)
    params = dict()
    params['image'] = image
    params['active'] = active
    params['name'] = name
    params['size'] = size
    params['meta'] = meta
    params['type'] = type
    params['allowSimilar'] = allowSimilar
    assemble_url = post_assemble_crs_test_request(api_url, userObject,params)
    with requests.post(url=assemble_url, json=params) as response:
        try:
            if response.status_code == 200:
                try:
                    return (response.json()["result"]["targetId"])
                except:
                    return response.json()
            else:
                print(response.json())
                return "error"
        except:
            print("返回值异常")
            return "error"

def _testCRSTargetsDelete(userObject,targetId):
    api_url = userObject.getTargetUrl()+"/target/" + str(targetId) + "?"
    params = dict()
    assemble_url = assemble_crs_test_request(api_url,userObject,params)
    with requests.delete(assemble_url) as response:
        try:
            #print(response.json())
            return (response.json()["statusCode"])
        except:
            print("返回值异常")

def _testCRSTargetsGet(userObject,targetId):
    api_url = userObject.getTargetUrl()+"/target/"+ str(targetId) + "?"
    params = dict()
    assemble_url = assemble_crs_test_request(api_url, userObject,params)
    with requests.get(assemble_url) as response:
        try:
            return response.json()["result"]['targetId']
        except:
            return  "error"
            print("返回值异常")

def _testCRSGradeDetail(userObject,image):
    api_url = userObject.getTargetUrl()+"/grade/detail/"
    params = dict()
    params['image'] = image
    assemble_url = post_assemble_crs_test_request(api_url, userObject,params)
    with requests.post(url=assemble_url,json = params) as response:
        try:
            if response.status_code == 200:
                print(response.json())
                return response.json()["statusCode"]
            else:
                return "error"
                print(response.json())
        except:
            return "error"
            print("返回值异常")

def _testCRSSimilar(userObject,image):
    api_url = userObject.getTargetUrl()+"/similar/"
    params = dict()
    params['image'] = image
    assemble_url = post_assemble_crs_test_request(api_url, userObject,params)
    with requests.post(url=assemble_url,json = params) as response:
        try:
            if response.status_code == 200:
                return(response.json()["result"]["results"][0]["targetId"])
            elif response.status_code == 404:
                return "notarget"
            else:
                print("similar 返回其它值")
                return "error"
        except:
            return "error"
            print("返回值异常")

def _testCRSTargetsUpdate(userObject,targetId,image, active="1", name="trackTest", size="20", meta="test",type = "ImageTarget",allowSimilar = "0"):
    api_url = userObject.getTargetUrl()+"/target/"+ str(targetId)
    params = dict()
    params['image'] = image
    params['active'] = active
    params['name'] = name
    params['size'] = size
    params['meta'] = meta
    params['type'] = type
    params['allowSimilar'] = allowSimilar
    assemble_url = post_assemble_crs_test_request(api_url,userObject, params)
    with requests.put(url=assemble_url,json = params) as response:
        try:
            if response.status_code == 200:
                return response.json()
                return response.json()["statusCode"]
            else:
                print(response.json())
                return "error"
        except:
            print("返回值异常")
            return "error"

# search API
def _testCRSSearch(userObject,image):
    api_url = userObject.getSearcherUrl()+"/search/"
    params = dict()
    params['image'] = image
    assemble_url = post_assemble_crs_test_request(api_url, userObject,params)
    with requests.post(url=assemble_url, json=params) as response:
        try:
            if response.status_code == 200:
                print("_testSearch OK")
                return response.json()['result']["target"]["targetId"]
            elif response.status_code == 404:
                return "notarget"
            else:
                print("search 返回其它值")
                return "error"

        except:
            print("search 返回值异常")
            return "error"

# download API
def _test_target_DownloadTarget(url, imageName):
    if (imageName + ".png") in os.listdir(os.path.normpath(getImage())):
        print("图片已存在")
        return True
    with requests.get(url) as response:
        if response.status_code == 200:
            print(os.path.normpath(getImage()+"/" + imageName + ".png"))
            with open(os.path.normpath(getImage()+"/" + imageName + ".png"), 'wb') as fd:
                for chunk in response.iter_content(chunk_size=128):
                    fd.write(chunk)
        else:
            print('DOWNLOAD image Failed!')
        if (imageName + ".png") in os.listdir(os.path.normpath(getImage()+"/")):
            print("File Downloaded!")
            return True
        else:
            print('File not exists!')
    return False

def deco(func):
    def wrapper(*args, **kwargs):
        startTime = time.time()
        func(*args, **kwargs)
        endTime = time.time()
        msecs = (endTime - startTime)*1000
        print(func(*args, **kwargs)[0])
        print("time is %d ms" %msecs)
    return wrapper

# search testCase

def searchTest(user,targetsList,Failed):
    testResult = ""
    targetId0 = targetsList["result"]["targets"][0]
    testResult = testResult + "TargetsList接口正常" + "\n"
    trackingImageUrl = targetId0["trackingImage"]
    if _test_target_DownloadTarget(trackingImageUrl, "download"):
        testResult = testResult + "图片下载正常" + "\n"
    else:
        testResult = testResult + "图片下载异常" + "\n"
    with open((os.path.normpath(getImage() + '/' + "download" + ".png")), 'rb') as f:
        image_64_encode = str(base64.b64encode(f.read()))[2:-1]
    searchResult = _testCRSSearch(user, image_64_encode)
    if searchResult == "error":
        testResult = testResult + "sercher error" + "\n"
    elif searchResult == "notarget":
        testResult = testResult + "识别不了\n"
        with open((os.path.normpath(getImage() + '/Base64_Test.jpg')), 'rb') as f:
            image_64_encode = str(base64.b64encode(f.read()))[2:-1]
        try:
            addedID = ""
            if _testCRSSearch(user, image_64_encode) == "notarget":
                addedID = (_testCRSTargetsAdd(user, image_64_encode))
        except:
            searchResult = "error"
            testResult = testResult + "trackImage上传失败\n"
            return [searchResult, testResult, Failed]
        searchResult = _testCRSSearch(user, image_64_encode)
        if not addedID == "":
            _testCRSTargetsDelete(user, _testCRSSearch(user, image_64_encode))
        if searchResult == "error":
            testResult = testResult + "sercher error" + "\n"
        elif searchResult == "notarget":
            testResult = testResult + "trackImage也识别不了\n"
        else:
            testResult = testResult + "识别测试图正常\n"
            print("识别测试图正常")
            Failed = False
    else:
        testResult = testResult + "识别用户图正常" + targetId0["targetId"] + "\n"
        Failed = False
    return [searchResult,testResult,Failed]

# target testCase

def targetSmokingTest(user,Failed):
    testResult = ""
    with open((os.path.normpath(getImage() + '/Base64_Test.jpg')), 'rb') as f:
        image_64_encode = str(base64.b64encode(f.read()))[2:-1]
    searchResult = _testCRSSearch(user, image_64_encode)
    if searchResult == "error":
        testResult = testResult + "sercher error" + "\n"
        return [testResult, Failed]
    elif not searchResult == "notarget":
        _testCRSTargetsDelete(user,searchResult)
    #target add test
    test_target_id = _testCRSTargetsAdd(user,image_64_encode)
    if test_target_id == "error":
        testResult = testResult + "add error" + "\n"
        return [testResult, Failed]
    else:
        testResult = testResult + "add pass" + "\n"
    #target similar test
    if not test_target_id == _testCRSSimilar(user, image_64_encode):
        testResult = testResult + "similar error" + "\n"
        return [testResult, Failed]
    else:
        testResult = testResult + "similar pass" + "\n"
    #target search test
    if not test_target_id == _testCRSSearch(user,image_64_encode):
        testResult = testResult + "search error" + "\n"
        return [testResult, Failed]
    else:
        testResult = testResult + "search pass" + "\n"
    #target get test
    if _testCRSTargetsGet(user,test_target_id) =="error":
        testResult = testResult + "get error" + "\n"
        return [testResult, Failed]
    else:
        testResult = testResult + "get pass" + "\n"
    #target GradeDetail test
    if _testCRSGradeDetail(user,image_64_encode) == "error":
        testResult = testResult + "GradeDetail error" + "\n"
        return [testResult, Failed]
    else:
        testResult = testResult + "GradeDetail pass" + "\n"
    #target update test
    with open((os.path.normpath(getImage() + '/update.jpg')), 'rb') as f:
        update_encode = str(base64.b64encode(f.read()))[2:-1]
    updateResult = _testCRSTargetsUpdate(user,test_target_id,update_encode)
    if not updateResult == "error":
        update_search_id = _testCRSSearch(user, update_encode)
        if update_search_id == test_target_id:
            testResult = testResult + "update pass" + "\n"
            Failed = False
            return [testResult, Failed]
        else:
            testResult = testResult + "update error" + "\n"
            return [testResult, Failed]
    else:
        testResult = testResult + "update error" + "\n"
        return [testResult, Failed]


if __name__ == '__main__':
    # sendMsg = ""
    testResult = ""
    # uuid = "2a41d9e23390bad8748a76838e441907"
    uuid = sys.argv[0]

    test_dic = {
        "appKey": "2c1898c3935541e1968ae5320581b84d",
        "appSecret": "WsPwoH9Oq0nyJs8zGjA86fvIuG1kFTzTtA5Qa1M5Gx8Cmake9VwUIexNrqGppcBoohbjEFwGDvEN4dOpzqQrdNhb8Vpm3xXEYTPUBxtZX90Mtm13Qzmmfc2WYiaRFPxV",
        "searcherUrl": "http://cn1.crs.easyar.com:8080",
        "targetUrl": "http://cn1.crs.easyar.com:8888",
        "type": "new"
    }

    myTestDic = CrsUser(test_dic)
    testResult = testResult + "uuid:" + uuid + "\n"
    Failed = True
    print("UUID: " + uuid)
    userList = [myTestDic]
    for user in userList:
        targetsList = _testCRSTargetsList(user,"",100)
        print(targetsList)
        #delete all
        flag = True
        if flag:
            if len(targetsList["result"]["targets"]) > 0:
                for i in targetsList["result"]["targets"]:
                    print(i["targetId"])
                    print(_testCRSTargetsDelete(user, i["targetId"]))
            else:
                pass
        if flag:
            with open((os.path.normpath(getImage() + '/Base64_Test.jpg')), 'rb') as f:
                image_64_encode = str(base64.b64encode(f.read()))[2:-1]
                test_target_id = _testCRSTargetsAdd(user, image_64_encode)

            with open((os.path.normpath(getImage() + '/update.jpg')), 'rb') as f:
                update_encode = str(base64.b64encode(f.read()))[2:-1]
                updateResult = _testCRSTargetsUpdate(user,test_target_id,update_encode)

            _testCRSTargetsDelete(user,test_target_id)



    for i in range(10):
        for user in userList:
            try:
                targetsList = _testCRSTargetsList(user, "", 10)
                if len(targetsList["result"]["targets"]) > 0:
                    for i in targetsList["result"]["targets"]:
                        print(i["targetId"])
                        print(_testCRSTargetsDelete(user, i["targetId"]))
                else:
                    pass

                def test(i):
                    for j in range(0, 10):
                        no = str(10000 + j)[1:]
                        imagePath = os.path.normpath(getImage() + "\\" + str(i) + no + ".jpg")
                        with open(imagePath, 'rb') as f:
                            image_64_encode = str(base64.b64encode(f.read()))[2:-1]
                            targetId = (_testCRSTargetsAdd(user, image_64_encode, "1", str(str(i) + no)))
                            print(targetId)


                # test(10)

                targetsList = _testCRSTargetsList(user, "", 10)
                if len(targetsList["result"]["targets"]) > 0:
                    for i in targetsList["result"]["targets"]:
                        print(i["targetId"])
                        print(_testCRSTargetsDelete(user, i["targetId"]))
                else:
                    pass


                targetsList = _testCRSTargetsList(user)

                # target Test:
                ret = targetSmokingTest(user, Failed)
                testResult = testResult + ret[0]
                print(testResult)
                Failed = ret[1]
                if Failed == True:
                    break

                targetsList = _testCRSTargetsList(user)

                # search Test:
                if len(targetsList["result"]["targets"]) > 0:
                    pass
                elif len(targetsList["result"]["targets"]) == 0:
                    print("list = 0")
                    with open((os.path.normpath(getImage() + '/Base64_Test.jpg')), 'rb') as f:
                        image_64_encode = str(base64.b64encode(f.read()))[2:-1]
                        _testCRSTargetsAdd(user, image_64_encode)
                    targetsList = _testCRSTargetsList(user)
                    testResult = testResult + "TargetsList接口返回值为空,add默认图片" + "\n"
                else:
                    testResult = testResult + "TargetsList异常,余下测试跳过" + "\n"
                    sendMsg = sendMsg + testResult + "\n\n"
                    break
                ret = searchTest(user, targetsList, Failed)
                searchResult = ret[0]
                testResult = testResult + ret[1]
                print(testResult)
                Failed = ret[2]

            except:
                import traceback

                tracebackInfo = traceback.format_exc()
                print(testResult)
                testResult = testResult + tracebackInfo + "\n"

        #     if Failed:
        #         sendMsg = sendMsg + testResult + "\n\n"
        #         print("-----------SmokingTest Failed----------")
        #         break
        #     else:
        #         print("----------SmokingTest Pass----------")
        #
        # if not sendMsg == "":
        #     sendMail(sendMsg)
        #     print(i)
        #     break


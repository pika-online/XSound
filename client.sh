

url="https://funsound.cn/xsound"

# 注册账号
curl -X POST $url/register/ -F "account=coolephemeroptera@gmail.com" -F "account_type=email" -F "password=123456" 
# 返回结果示例：
# {"status":"error","msg":"Account existed","result":{},"completed":null,"stream":false}
# {"status":"success","msg":"Please enter the verification code","result":{},"completed":null,"stream":false}

# 上传验证码
curl -X POST $url/register/ -F "account=coolephemeroptera@gmail.com" -F "account_type=email" -F "password=123456" -F "code=4140"
# 返回结果示例：
# {"status":"error","msg":"Verification code is invalid","result":{},"completed":null,"stream":false}
# {"status":"success","msg":"Registration successfully","result":{},"completed":null,"stream":false}


curl -X POST $url/change-password/ -F "account=coolephemeroptera@gmail.com"  -F "old_password=123456" -F "new_password=12345678" 
# 返回结果示例：
# {"status":"success","msg":"Password updated successfully","result":{},"completed":null,"stream":false}


# 登录获取uid
curl -X POST $url/login/ -F "account=coolephemeroptera@gmail.com"  -F "password=12345678" 
# 返回结果示例：
# {"status":"error","msg":"Password is incorrect","result":{},"completed":null,"stream":false}
# {"status":"success","msg":"254JVMnWdh","result":{},"completed":null,"stream":false}
uid=254JVMnWdh



# 查询余额
curl -X GET $url/get_account/?uid=${uid}
# 返回结果示例：
# {"status":"error","msg":"非法uid","result":{},"completed":null,"stream":false}
# {"status":"success","msg":"","result":{"account":"coolephemeroptera@gmail.com","vip":false,"quota":7200},"completed":null,"stream":false}


# 查询支持语言
curl -X GET $url/get_languages/?uid=${uid}
# 返回结果示例：
# {"status":"error","msg":"","result":["Afrikaans","Amharic","Arabic","English"],"completed":null,"stream":false}


# 修改余额 (root方法)
# curl -X POST $url/quota_change/ -F "secret=wei.0418" -F "uid=${uid}" -F "vol=-300"
# curl -X GET $url/get_account/?uid=${uid}

# 修改vip (root方法)
# curl -X POST $url/vip_change/ -F "secret=wei.0418" -F "uid=${uid}" -F "vip=false"
# curl -X GET $url/get_account/?uid=${uid}


# 语音日志转写 (流式返回)
# [use_sv, trans_language] 是可选项，可不填
curl -X POST $url/diarization/ \
-F "uid=${uid}" \
-F "file=@examples/test.wav" \
-F "hotwords=[\"阿里巴巴\",\"心森招聘\"]"
-F "engine=funasr" \
-F "use_sv=true" \
-F "trans_language=English" 
# 返回结果示例：
# {"status": "success", "msg": "diarization", "result": ["sentence", {"id": "0_s0ZNK", "text": "嗯,", "start": "5.410", "end": "5.710", "progress": 0.072}], "completed": null, "stream": true}
# {"status": "success", "msg": "diarization", "result": ["sentence", {"id": "1_FVCHI", "text": "那么今天我们就简单的进行一下那个新生招聘的嗯讨论吧,", "start": "5.710", "end": "12.010", "progress": 0.152}], "completed": null, "stream": true}
# (实时翻译){"status": "success", "msg": "diarization", "result": ["trans", {"0_s0ZNK": "Well,", "1_FVCHI": "today we'll briefly discuss the recruitment of new members,", "2_RbIbK": "since the new students will be arriving soon,", "3_H8ye8": "and our club needs to recruit some new members,", "4_Sh1Vu": "so let's discuss how we're going to conduct the recruitment today,"}], "completed": null, "stream": true}
# ...
# {"status": "success", "msg": "diarization", "result": ["sentence", {"id": "31_fs5Bo", "text": "我们可以在演播厅底下,", "start": "69.950", "end": "72.350", "progress": 0.916}], "completed": null, "stream": true}
# (最后角色识别){"status": "success", "msg": "diarization", "result": ["roles", {"0_s0ZNK": 2, "1_FVCHI": 0, "2_RbIbK": 0, "3_H8ye8": 0, "4_Sh1Vu": 0, "5_XfrAR": 2,...}], "completed": null, "stream": true}
# {"status": "success", "msg": "bill", "result": {"audio_seconds": 79, "infer_cost_seconds": 9.283, "infer_speed": 8.51, "balance_before": 7200, "balance_now": 6924, "fee_base": 79, "fee_sv": 39, "fee_trans": 158, "fee_all": 276}, "completed": true, "stream": true}



# 🎧 XSound 接口文档

Base URL: `https://funsound.cn/xsound`

---

## 📌 注册账号

**接口地址：**

```
POST /register/
```

**参数：**

| 参数名           | 类型     | 说明            |
| ------------- | ------ | ------------- |
| account       | string | 邮箱地址          |
| account\_type | string | 账号类型（如：email） |
| password      | string | 密码            |
| code *(可选)*   | string | 邮箱验证码         |

**示例命令：**

```bash
curl -X POST https://funsound.cn/xsound/register/ \
  -F "account=coolephemeroptera@gmail.com" \
  -F "account_type=email" \
  -F "password=123456"
```

**返回示例：**

```json
{"status":"error","msg":"Account existed","result":{},"completed":null,"stream":false}
```

```json
{"status":"success","msg":"Please enter the verification code","result":{},"completed":null,"stream":false}
```

**提交验证码示例：**

```bash
curl -X POST https://funsound.cn/xsound/register/ \
  -F "account=coolephemeroptera@gmail.com" \
  -F "account_type=email" \
  -F "password=123456" \
  -F "code=4140"
```

**返回示例：**

```json
{"status":"error","msg":"Verification code is invalid","result":{},"completed":null,"stream":false}
```

```json
{"status":"success","msg":"Registration successfully","result":{},"completed":null,"stream":false}
```

---

## 🔐 修改密码

**接口地址：**

```
POST /change-password/
```

**参数：**

| 参数名           | 类型     | 说明   |
| ------------- | ------ | ---- |
| account       | string | 注册邮箱 |
| old\_password | string | 原密码  |
| new\_password | string | 新密码  |

**示例：**

```bash
curl -X POST https://funsound.cn/xsound/change-password/ \
  -F "account=coolephemeroptera@gmail.com" \
  -F "old_password=123456" \
  -F "new_password=12345678"
```

**返回示例：**

```json
{"status":"success","msg":"Password updated successfully","result":{},"completed":null,"stream":false}
```

---

## 🔓 登录获取 UID

**接口地址：**

```
POST /login/
```

**参数：**

| 参数名      | 类型     | 说明 |
| -------- | ------ | -- |
| account  | string | 邮箱 |
| password | string | 密码 |

**示例：**

```bash
curl -X POST https://funsound.cn/xsound/login/ \
  -F "account=coolephemeroptera@gmail.com" \
  -F "password=12345678"
```

**返回示例：**

```json
{"status":"success","msg":"254JVMnWdh","result":{},"completed":null,"stream":false}
```

---

## 💰 查询账户余额

**接口地址：**

```
GET /get_account/?uid={uid}
```

**参数：**

| 参数名 | 类型     | 说明   |
| --- | ------ | ---- |
| uid | string | 登录获取 |

**返回示例：**

```json
{"status":"success","msg":"","result":{"account":"coolephemeroptera@gmail.com","vip":false,"quota":7200},"completed":null,"stream":false}
```

---

## 🌍 查询支持语言

**接口地址：**

```
GET /get_languages/?uid={uid}
```

**返回示例：**

```json
{"status":"success","msg":"","result":["Afrikaans","Amharic","Arabic","English"],"completed":null,"stream":false}
```

---

## 🎙️ 音频转写 + 角色识别 + 翻译（流式）

**接口地址：**

```
POST /diarization/
```

**参数：**

| 参数名             | 类型      | 说明                  |
| --------------- | ------- | ------------------- |
| file            | file    | 音频文件（例如 .wav）       |
| uid             | string  | 登录后获取的 UID          |
| engine          | string  | 使用的语音识别引擎（如 funasr） |
| use\_sv         | boolean | 是否进行说话人识别           |
| trans\_language | string  | 翻译目标语言（如 English）   |

**示例：**

```bash
curl -X POST https://funsound.cn/xsound/diarization/ \
  -F "file=@examples/test.wav" \
  -F "uid=254JVMnWdh" \
  -F "engine=funasr" \
  -F "use_sv=true" \
  -F "trans_language=English"
```

**返回示例（流式）：**

```json
{"status":"success","msg":"diarization","result":["sentence",{"id":"1_FVCHI","text":"那么今天我们就简单的进行一下那个新生招聘的嗯讨论吧,","start":"5.710","end":"12.010","progress":0.152}],"completed":null,"stream":true}
```

```json
{"status":"success","msg":"diarization","result":["trans",{"1_FVCHI":"today we'll briefly discuss the recruitment of new members,"}],"completed":null,"stream":true}
```

```json
{"status":"success","msg":"diarization","result":["roles",{"1_FVCHI":0}],"completed":null,"stream":true}
```

```json
{"status":"success","msg":"bill","result":{"audio_seconds":79,"infer_cost_seconds":9.283,"infer_speed":8.51,"balance_before":7200,"balance_now":6924,"fee_base":79,"fee_sv":39,"fee_trans":158,"fee_all":276},"completed":true,"stream":true}
```

---

## 🛠️ 管理员权限（root）

> 需 `secret=wei.0418` 作为管理员密钥。

### 修改配额（quota）

```bash
curl -X POST https://funsound.cn/xsound/quota_change/ \
  -F "secret=xxxxx" \
  -F "uid=254JVMnWdh" \
  -F "vol=-300"
```

### 修改 VIP 状态

```bash
curl -X POST https://funsound.cn/xsound/vip_change/ \
  -F "secret=xxxxx" \
  -F "uid=254JVMnWdh" \
  -F "vip=false"
```


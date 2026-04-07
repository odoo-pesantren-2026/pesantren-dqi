import requests
import json

class Nobox:
    def __init__(self, Key=""):
        self.baseUrl = "https://id.nobox.ai/"
        # self.baseUrl = "https://localhost:5001/"
        self.key = Key
        self.bodyType = [
            {
                "value": 1,
                "text": "Text"
            },
            {
                "value": 2,
                "text": "Audio"
            },
            {
                "value": 3,
                "text": "Image"
            },
            {
                "value": 7,
                "text": "Sticker"
            },
            {
                "value": 4,
                "text": "Video"
            },
            {
                "value": 5,
                "text": "File"
            },
            {
                "value": 9,
                "text": "Location"
            },
            {
                "value": 10,
                "text": "Order"
            },
            {
                "value": 11,
                "text": "Product"
            },
            {
                "value": 12,
                "text": "VCARD"
            },
            {
                "value": 13,
                "text": "VCARD_MULTI"
            }
        ]

    def setToken(self, Key):
        self.key = Key

    def generateToken(self, username, password):
        try:
            response = requests.post(
                self.baseUrl + 'AccountAPI/GenerateToken',
                headers={
                    'Content-Type': 'application/json'
                },
                data=json.dumps({
                    'username': username,
                    'password': password
                })
            )

            if not response.ok:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': None,
                    'Error': response
                }

            data = response.json()
            print(data, "dataaoke")
            return {
                'IsErrror': False,
                'Code': response.status_code,
                'Data': data['token'],
                'Error': None
            }

        except Exception as error:
            print('Error:', error)
            return {
                'IsErrror': True,
                'Code': 500,
                'Data': None,
                'Error': str(error)
            }

    def fetchChannelList(self):
        try:
            response = requests.post(
                self.baseUrl + 'Services/Master/Channel/List',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.key}'
                },
                data=json.dumps({
                    'IncludeColumns': ["Id", "Nm"],
                    'ColumnSelection': 1
                })
            )

            if not response.ok:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': None,
                    'Error': response
                }

            data = response.json()
            if data['Error'] is None:
                return {
                    'IsErrror': False,
                    'Code': response.status_code,
                    'Data': data['Entities'],
                    'Error': None
                }
            else:
                return {
                    'IsErrror': False,
                    'Code': response.status_code,
                    'Data': data['Entities'],
                    'Error': data['Error']
                }

        except Exception as error:
            print('Error:', error)
            return {
                'IsErrror': True,
                'Code': 500,
                'Data': None,
                'Error': str(error)
            }

    def fetchAccountList(self):
        try:
            response = requests.post(
                self.baseUrl + 'Services/Nobox/Account/List',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.key}'
                },
                data=json.dumps({
                    'IncludeColumns': ["Id", "Name", "Channel"],
                    'ColumnSelection': 1
                })
            )

            if not response.ok:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': None,
                    'Error': response
                }

            data = response.json()
            if data['Error'] is None:
                return {
                    'IsErrror': False,
                    'Code': response.status_code,
                    'Data': data['Entities'],
                    'Error': None
                }
            else:
                return {
                    'IsErrror': False,
                    'Code': response.status_code,
                    'Data': data['Entities'],
                    'Error': data['Error']
                }

        except Exception as error:
            print('Error:', error)
            return {
                'IsErrror': True,
                'Code': 500,
                'Data': None,
                'Error': str(error)
            }

    def fetchLinkList(self, channelId=None, contactId=None):
        try:
            request = {
                'IncludeColumns': ["Id", "Name", "IdExt"],
                'ColumnSelection': 1
            }
            if channelId is not None or contactId is not None:
                request['EqualityFilter'] = {}
                if contactId is not None:
                    request['EqualityFilter']['CtId'] = contactId
                if channelId is not None:
                    request['EqualityFilter']['ChId'] = channelId

            response = requests.post(
                self.baseUrl + 'Services/Chat/Chatlinkcontacts/List',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.key}'
                },
                data=json.dumps(request)
            )

            if not response.ok:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': None,
                    'Error': response
                }

            data = response.json()
            if data['Error'] is None:
                return {
                    'IsErrror': False,
                    'Code': response.status_code,
                    'Data': data['Entities'],
                    'Error': None
                }
            else:
                return {
                    'IsErrror': False,
                    'Code': response.status_code,
                    'Data': data['Entities'],
                    'Error': data['Error']
                }

        except Exception as error:
            print('Error:', error)
            return {
                'IsErrror': True,
                'Code': 500,
                'Data': None,
                'Error': str(error)
            }

    def bodyTypeList(self):
        return self.bodyType

    def sendMessage(self, linkId, channelId, accountIds, bodyType, body, attachment):
        try:
            response = requests.post(
                self.baseUrl + 'Inbox/Send',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.key}'
                },
                data=json.dumps({
                    'LinkId': linkId,
                    'ChannelId': channelId,
                    'AccountIds': accountIds,
                    'BodyType': bodyType,
                    'Body': body,
                    'Attachment': attachment
                })
            )

            if not response.ok:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': None,
                    'Error': response
                }

            data = response.json()
            if data['Error'] is not None:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': data['Data'],
                    'Error': data['Error']
                }
            else:
                return {
                    'IsErrror': False,
                    'Code': response.status_code,
                    'Data': data['Data'],
                    'Error': data['Error']
                }

        except Exception as error:
            print('Error:', error)
            return {
                'IsErrror': True,
                'Code': 500,
                'Data': None,
                'Error': str(error)
            }

    def sendMessageExt(self, extId, channelId, accountIds, bodyType, body, attachment):
        try:
            response = requests.post(
                self.baseUrl + 'Inbox/Send',
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.key}'
                },
                data=json.dumps({
                    'ExtId': extId,
                    'ChannelId': channelId,
                    'AccountIds': accountIds,
                    'BodyType': bodyType,
                    'Body': body,
                    'Attachment': attachment
                })
            )

            if not response.ok:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': None,
                    'Error': response
                }

            data = response.json()
            if data['Error'] is not None:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': data['Data'],
                    'Error': data['Error']
                }
            else:
                return {
                    'IsErrror': False,
                    'Code': response.status_code,
                    'Data': data['Data'],
                    'Error': data['Error']
                }

        except Exception as error:
            print('Error:', error)
            return {
                'IsErrror': True,
                'Code': 500,
                'Data': None,
                'Error': str(error)
            }

    def uploadFile(self, file):
        try:
            url = self.baseUrl + 'Inbox/UploadFile/UploadFile'

            response = requests.post(
                url,
                headers={
                    'Authorization': f'Bearer {self.key}'
                },
                files={'file': file}
            )

            if not response.ok:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': None,
                    'Error': response
                }

            data = response.json()
            if data['Error'] is not None:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': data['Data'],
                    'Error': data['Error']
                }
            else:
                return {
                    'IsErrror': False,
                    'Code': response.status_code,
                    'Data': data['Data'],
                    'Error': data['Error']
                }

        except Exception as error:
            print('Error:', error)
            return {
                'IsErrror': True,
                'Code': 500,
                'Data': None,
                'Error': str(error)
            }

    def uploadBase64(self, filename, mimetype, base64):
        try:
            url = self.baseUrl + 'Inbox/UploadFile/UploadBase64'

            response = requests.post(
                url,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.key}'
                },
                data=json.dumps({
                    'filename': filename,
                    'mimetype': mimetype,
                    'data': base64
                })
            )

            if not response.ok:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': None,
                    'Error': response
                }

            data = response.json()
            if data['Error'] is not None:
                return {
                    'IsErrror': True,
                    'Code': response.status_code,
                    'Data': data['Data'],
                    'Error': data['Error']
                }
            else:
                return {
                    'IsErrror': False,
                    'Code': response.status_code,
                    'Data': data['Data'],
                    'Error': data['Error']
                }

        except Exception as error:
            print('Error:', error)
            return {
                'IsErrror': True,
                'Code': 500,
                'Data': None,
                'Error': str(error)
            }
# Testing file
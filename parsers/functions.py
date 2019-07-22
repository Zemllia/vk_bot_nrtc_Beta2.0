from requests import post
from json import loads

from vk_api import VkApi

import config


vk = VkApi(token=config.vk_token).get_api()


# Загрузка картинки на сервер вк
def photo_upload(picture):
    # Подготавливаем картинку и запрашиваем сылку для загрузки
    img = {'photo': ('Schedule.jpg', picture)}
    address = vk.photos.getMessagesUploadServer()['upload_url']

    # Загружаем картинку и пролуаем сылку на неё
    result = post(address, files=img)
    result = loads(result.text)
    result = vk.photos.saveMessagesPhoto(photo=result['photo'], server=result['server'], hash=result['hash'])
    return 'photo%i_%i' % (result[0]['owner_id'], result[0]['id'])


def averaged_parameter(class_, parameter):
    parameter = parameter.lower().replace(" ", "").replace("\r", "").replace("\n", "")
    if class_ == 'teacher':
        parameter = parameter.replace(".", "").replace(",", "")
    else:
        parameter = parameter.replace("-", "")
    return parameter
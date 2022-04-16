from difflib import get_close_matches
from typing import Union, List
from base64 import b64decode
import re

import cv2
import numpy
from PIL import Image
from config import Config
from pydantic import BaseModel
from paddleocr import PaddleOCR
from fastapi import APIRouter, Query

conf = Config()
router = APIRouter(prefix='/scanner')
ocr = PaddleOCR(lang="ch", **conf.ocr)
pos_type = '生之花/死之羽/时之计/空之杯/礼之冠'.split('/')
attrs = '生命值/暴击伤害/暴击率/元素精通/元素充能效率/治疗加成/攻击力/防御力'.split('/') \
             + [f'{i}元素伤害加成' for i in '风草岩冰雷火水']


async def bytes2array(b: bytes) -> numpy.ndarray:
    array_ = numpy.frombuffer(b, numpy.uint8)
    return cv2.imdecode(array_, cv2.IMREAD_GRAYSCALE)


async def b642array(base64: str) -> numpy.ndarray:
    b = b64decode(base64)
    return await bytes2array(b)


async def scan(im: Union[str, bytes, Image.Image]):
    if isinstance(im, str):
        return ocr.ocr(await b642array(im), cls=True)
    if isinstance(im, bytes):
        return ocr.ocr(await bytes2array(im))
    return ocr.ocr(await bytes2array(bytes(Image.core)), cls=True)


def get_value(v_: str, p2f: bool = False) -> Union[float, int, str, None]:
    value = v_.replace(',', '').replace('.', '').replace('，', '')
    if '%' in v_:
        value_ = value.replace('%', '')
        try:
            value_ = round(float(value_) / 10, ndigits=1)
        except ValueError:
            return
        if p2f:
            return round(value_ / 100, ndigits=3)
        return f'{value_}%'
    else:
        if value.isdigit():
            return int(value)
        return


def nom_float_list(box_pos: list) -> list:
    return [float(i) for i in box_pos]


def result2tuple(result: tuple) -> tuple:
    return result[0], float(result[1])


def sub_attr_matcher(r: str, p2f: bool = False):
    reg_ = re.search("[+·`\-：:]*?([\u4e00-\u9fa5]+)[+\-十](\d+([.:：]\d){0,2}(%|0/0)?)", r, re.M)
    if not reg_:
        return
    return {
        "attr": get_close_matches(reg_.group(1), attrs)[0],
        "value": get_value(reg_.group(2), p2f=p2f),
        "raw": r
    }


def term_matcher(r: str) -> Union[tuple, None]:
    pos = get_close_matches(r, pos_type)
    if pos:
        return pos[0], 'pos'
    attr = get_close_matches(r, attrs)
    if attr:
        return attr[0], 'attr'
    return


def level_matcher(lvl: str) -> Union[int, None]:
    lvl_r = re.search('.?(\d{1,2})', lvl)
    if not lvl_r:
        return
    return int(lvl_r.group(1))


def result_parser(result: list, convert_percentage=False):
    main_attr_founded = False
    data_ = {
        "raw": [],
        "data": {
            "name": "",
            "main": {},
            "level": None,
            "position": "",
            "sub": []
        }
    }
    for pos, r_ in enumerate(result):
        box, r = r_
        if main_attr_founded:
            pass
        else:
            term = term_matcher(r[0])
            if not term:
                pass
            elif term[1] == 'pos':
                print('trigger position')
                data_["data"]["position"] = term[0]
                data_["data"]["level"] = level_matcher(result[pos + 3][1][0])
                data_["data"]["name"] = result[pos - 1][1][0]
                data_["data"]["main"].update({
                    "attr": result[pos + 1][1][0],
                    "value": get_value(result[pos + 2][1][0], p2f=convert_percentage)
                })
                main_attr_founded = True
            else:
                print('trigger attributions')
                data_["data"]["position"] = result[pos - 1][1][0]
                data_["data"]["level"] = level_matcher(result[pos + 2][1][0])
                data_["data"]["name"] = result[pos - 2][1][0]
                data_["data"]["main"].update({
                    "attr": term[0],
                    "value": get_value(result[pos + 1][1][0], p2f=convert_percentage)
                })
                main_attr_founded = True
        sub_attr = sub_attr_matcher(r[0], p2f=convert_percentage)
        if sub_attr:
            data_["data"]["sub"].append(sub_attr)
        data_["raw"].append([[nom_float_list(i) for i in box], result2tuple(r)])
    return data_


def pre_filter(result: list) -> list:
    return list(filter(lambda x: not re.search("^\+\d{1,2}", x[1][0]) and x[1][1] >= 0.7, result))


class UploadBody(BaseModel):
    images: Union[str, List[str]]


@router.post('', summary="Artifact Scanner",
             description="Scan the picture of the relic and return the original data and the parsed data")
async def scanner_(
        data: UploadBody,
        convert: bool = Query(False, description="Whether to convert a string percentage to a floating point number")
):
    if isinstance(data.images, str):
        result = pre_filter(await scan(data.images))
        return result_parser(result, convert_percentage=convert)

    (result := {}).update(
        {
            "result": [result_parser(pre_filter(await scan(im)), convert_percentage=convert) for im in data.images]
        }
    )
    return result

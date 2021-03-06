#!/usr/bin/env python3

import sqlite3
import sys
from biplist import *
import os
import argparse
from urllib.parse import urlparse
import traceback

parser = argparse.ArgumentParser()
parser.add_argument("file")
args = parser.parse_args()

HTTP_STATUS_CODES = {
	'200' : 'OK',
        '201' : 'Created',
        '202' : 'Accepted',
        '203' : 'Non-Authoritative Information',
        '204' : 'No Content',
        '205' : 'Reset Content',
        '206' : 'Partial Content',
        '300' : 'Multiple Choices',
        '301' : 'Moved Permanently',
        '302' : 'Found',
        '303' : 'See Other',
        '304' : 'Not Modified',
        '305' : 'Use Proxy',
        '307' : 'Temporary Redirect',
        '400' : 'Bad Request',
        '401' : 'Unauthorized',
        '402' : 'Payment Required',
        '403' : 'Forbidden',
        '404' : 'Not Found',
        '405' : 'Method Not Allowed',
        '406' : 'Not Acceptable',
        '407' : 'Proxy Authentication Required',
        '408' : 'Request Timeout',
        '409' : 'Conflict',
        '410' : 'Gone',
        '411' : 'Length Required',
        '412' : 'Precondition Failed',
        '413' : 'Request Entity Too Large',
        '414' : 'Request-URI Too Long',
        '415' : 'Unsupported Media Type',
        '416' : 'Requested Range Not Satisfiable',
        '417' : 'Expectation Failed',
        '500' : 'Internal Server Error',
        '501' : 'Not Implemented',
        '502' : 'Bad Gateway',
        '503' : 'Service Unavailable',
        '504' : 'Gateway Timeout',
        '505' : 'HTTP Version Not Supported'
}

extensions = {
	"application/epub+zip": "epub",
	"application/java-archive": "jar",
	"application/javascript": "js",
	"application/json": "json",
	"application/msword": "doc",
	"application/octet-stream": "bin",
	"application/ogg": "ogx",
	"application/pdf": "pdf",
	"application/rtf": "rtf",
	"application/typescript": "ts",
	"application/vnd.amazon.ebook": "azw",
	"application/vnd.apple.installer+xml": "mpkg",
	"application/vnd.mozilla.xul+xml": "xul",
	"application/vnd.ms-excel": "xls",
	"application/vnd.ms-fontobject": "eot",
	"application/vnd.ms-powerpoint": "ppt",
	"application/vnd.oasis.opendocument.presentation": "odp",
	"application/vnd.oasis.opendocument.spreadsheet": "ods",
	"application/vnd.oasis.opendocument.text": "odt",
	"application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
	"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
	"application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
	"application/vnd.visio": "vsd",
	"application/x-7z-compressed": "7z",
	"application/x-abiword": "abw",
	"application/x-bzip": "bz",
	"application/x-bzip2": "bz2",
	"application/x-csh": "csh",
	"application/x-rar-compressed": "rar",
	"application/x-sh": "sh",
	"application/x-shockwave-flash": "swf",
	"application/x-tar": "tar",
	"application/xhtml+xml": "xhtml",
	"application/xml": "xml",
	"application/zip": "zip",
	"audio/aac": "aac",
	"audio/midi": "midi",
	"audio/ogg": "oga",
	"audio/webm": "weba",
	"audio/x-wav": "wav",
	"font/otf": "otf",
	"font/ttf": "ttf",
	"font/woff": "woff",
	"font/woff2": "woff2",
	"image/gif": "gif",
	"image/jpeg": "jpg",
	"image/png": "png",
	"image/svg+xml": "svg",
	"image/tiff": "tiff",
	"image/webp": "webp",
	"image/x-icon": "ico",
	"text/calendar": "ics",
	"text/css": "css",
	"text/csv": "csv",
	"text/html": "html",
	"video/3gpp": "3gp",
	"video/3gpp2": "3g2",
	"video/mpeg": "mpeg",
	"video/ogg": "ogv",
	"video/webm": "webm",
	"video/x-msvideo": "avi"
}

try:
    os.mkdir("dump")
    conn = sqlite3.connect(args.file)
    c = conn.cursor()
    for row in c.execute("select request_object, response_object, receiver_data, isDataOnFS, cfurl_cache_blob_data.entry_ID, time_stamp from cfurl_cache_blob_data join cfurl_cache_receiver_data on cfurl_cache_blob_data.entry_ID = cfurl_cache_receiver_data.entry_ID join cfurl_cache_response on cfurl_cache_response.entry_ID = cfurl_cache_receiver_data.entry_ID"):
        request = readPlistFromString(row[0])
        response = readPlistFromString(row[1])
        entry = {}
        entry["entryID"] = row[4]
        postDataArray = request["Array"][21]
        entry["postData"] = ""
        if (isinstance(postDataArray, list)):
            entry["postData"] = postDataArray[0]

        url = urlparse(request["Array"][1]["_CFURLString"])
        requestString = "%s %s HTTP/1.1" % (request["Array"][18], request["Array"][1]["_CFURLString"])
        entry["requestLine"] = requestString
        requestString += "\nHost: %s" % url.hostname

        for k in request["Array"][19]:
            if k != "__hhaa__":
                requestString += "\n%s: %s" % (k, request["Array"][19][k])
        entry["requestString"] = "%s\n\n" % requestString
        entry["requestObject"] = request

        responseString = "HTTP/1.1 %s %s" % (response["Array"][3], HTTP_STATUS_CODES[str(response["Array"][3])])
        entry["statusLine"] = responseString
        for k in response["Array"][4]:
            if k != "__hhaa__":
                responseString += "\n%s: %s" % (k, response["Array"][4][k])

        entry["responseString"] = responseString
        entry["responseObject"] = response
        entry["responseData"] = row[2]
        entry["hasFile"] = (row[3] == 0)
        entry["contentType"] = response["Array"][6]

        with open("dump/%s.txt" % entry["entryID"], 'wb') as f:
            f.write(entry["requestString"].encode())
            f.write(entry["postData"])
            if (entry["postData"] != ""):
                f.write('\n\n'.encode())
            f.write(entry["responseString"].encode())
            f.write('\n\n'.encode())
            if (not entry["hasFile"]):
                f.write("Response data in fsCachedData/%s" % entry["responseData"])
            elif (entry["contentType"].startswith("text/") or entry["contentType"].endswith("javascript") or entry["contentType"].endswith("json")):
                f.write(entry["responseData"])
            else:
                with open("dump/%s.%s" % (entry["entryID"], extensions[entry["contentType"]]), 'wb') as r:
                    r.write(entry["responseData"])
            f.write('\n\n'.encode())

    print("Done!")
except Exception as e:
    traceback.print_exc()

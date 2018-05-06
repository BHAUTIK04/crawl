# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
import json
from django.views.decorators.csrf import csrf_exempt
import urllib
from BeautifulSoup import BeautifulSoup
import logging
logger = logging.getLogger(__name__)

def index(request):
    logger.info("User came!!")
    return render(request, "index.html")

def fetchData(url, base_url=None):
    '''Fetch data for the requested url and other pages in website.'''
    if not url.startswith("http") and base_url:
        url=base_url+"/"+url
    data = urllib.urlopen(url)
    if data.code == 200:
    	try:
            soup = BeautifulSoup(data)
            link = []
            images = []
            try:
                for i in soup.findAll('img'):
                    if i.get('src', ''):
                        images.append(i['src'])
            except Exception as e:
                logger.error("Error in getting image {}".format(e))
            try:
                for j in soup.findAll("a"):
                    if j.get("href", "").startswith("http") or j["href"].endswith(".html"):
                        link.append(j["href"])
            except Exception as e:
                logger.error("Error in getting urls {}".format(e))
            link = list(set(link))
            images = list(set(images))
            return (link, images)

        except Exception as e:
            logger.error("Error in beautify data {}".format(e))
            return None
    else:
        logger.error("Error in getting page data {}".format(data.code))
        return None


@csrf_exempt
def crawlUrl(request):
    '''
        @parameter seedurl: valid baseurl
        @parameter depth: depth of the pages to visit
        @method POST
        This api will take this two parameter as json in body.
        Response: seedurl/baseurl, list of visited pages, list of images
    '''
    if request.method == "POST":
        try:
            d =request.body
            data = json.loads(d)
            logger.info("Requested data {}".format(d))
            _url = data.get("seedurl","")
            _depth = data.get("depth", 0)
            logger.info("Request for url {}".format(_url))
            logger.info("Request for depth {}".format(_depth))
            if _url and _depth:
                if _url.startswith("http://") or _url.startswith("https://"):
                    modified_url = _url
                elif _url.startswith("ww"):
                    modified_url = "https://"+_url
                elif not _url.startswith("www") or not _url.startswith("https://") or not _url.startswith("http://"):
                    logger.error("Format is not matching with "+_url)
                    return HttpResponse(json.dumps({"status_msg":"error","response_msg":"Incorrect url."}))
                logger.info("Current url after modification "+modified_url)

                visited_url = [modified_url]
                rejected_url = []
                depth_wise_url={0:[modified_url]}
                images = []
                current_depth = 0
                base_url = modified_url
                while current_depth <= int(_depth):
                    logger.info("modified url is {}".format(modified_url))
                    url_list = []
                    if current_depth == 0 and modified_url:
                        ret_link, ret_images = fetchData(modified_url)
                        images += ret_images
                        current_depth += 1
                        depth_wise_url[current_depth] = ret_link
                    else:
                        _temp_links = []
                        for url in depth_wise_url[current_depth]:
                            if url in visited_url or url in rejected_url:
                                pass
                            else:
                                _resp = fetchData(url, base_url)
                                if _resp:
                                    ret_link, ret_images =_resp
                                    if ret_link is not None and ret_images is not None:
                                        visited_url.append(url)
                                    _temp_links += ret_link
                                    images += ret_images
                                else:
                                    rejected_url.append(url)
                        _temp_links = list(set(_temp_links) - set(depth_wise_url[current_depth]))
                        current_depth+=1
                        depth_wise_url[current_depth] = _temp_links
                visited_url.remove(modified_url)
                response_data = {"status_msg":"success", "seedurl":modified_url,"urls":list(set(visited_url)),"images":list(set(images))}
                logger.info("Crawled data is {}".format(response_data))
                return HttpResponse(json.dumps(response_data))
            else:
                response_data = {"status_msg":"error", "response_msg":"Please enter valid url"}
                return HttpResponse(json.dumps(response_data))
        except Exception as e:
            response_data = {"status_msg":"error", "response_msg":"Not able to serve your request. Please Try later"}
            logger.info("Crawled data is {}".format(e))
            return HttpResponse(json.dumps(response_data))
    else:
        logger.error("Get request which is not allowed")
        return HttpResponse(json.dumps({"status_msg":"error", "response_msg":"Get request is not allowed"}))

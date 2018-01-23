# coding=utf-8

try:
    import requests
except ImportError:
    print("ERROR: You need to install requests module.")
    exit()

try:
    from bs4 import *
except ImportError:
    print("ERROR: You need to install bs4 module.")
    exit()

import urllib.parse
import math
import argparse
import re
import signal
import sys
from collections import deque
import threading
from time import sleep
from random import randint


class BaiduUrlThread(threading.Thread):
    """
    Thread class for getting real URL from Baidu redirection URL
    """
    def __init__(self, title, redirect_url, item_results):
        threading.Thread.__init__(self)
        self.title = title
        self.redirect_url = redirect_url
        self.item_results = item_results

    def run(self):
        try:
            loc_res = requests.head(self.redirect_url, allow_redirects=True, timeout=5)
        except Exception:
            return None
        self.item_results.append((self.title, loc_res.url))


class InfoDork(object):
    """
         _______. __  .___________. _______  _______   ______   .______       __  ___
        /       ||  | |           ||   ____||       \ /  __  \  |   _  \     |  |/  /
       |   (----`|  | `---|  |----`|  |__   |  .--.  |  |  |  | |  |_)  |    |  '  /
        \   \    |  |     |  |     |   __|  |  |  |  |  |  |  | |      /     |    <
    .----)   |   |  |     |  |     |  |____ |  '--'  |  `--'  | |  |\  \----.|  .  \\
    |_______/    |__|     |__|     |_______||_______/ \______/  | _| `._____||__|\__\\


    Author: repoog
    Version: v1.0
    Create Date: 2018.1.21
    Python Version: v3.6.4
    """
    GOOGLE_DORK = {"subdomain": "site:{}",
                  "install": "site:{} inurl:readme OR inurl:license OR inurl:install OR inurl:setup",
                  "redirect": "site:{} inurl:redir OR inurl:url OR inurl:redirect OR inurl:return OR inurl:src=http",
                  "sensitive": "site:{} ext:bak OR ext:sql OR ext:rar OR ext:zip OR ext:log",
                  "document": "site:{} ext:doc OR ext:docx OR ext:csv OR ext:pdf OR ext:txt",
                  "extension": "site:{} ext:cgi OR ext:php OR ext:aspx OR ext:jsp OR ext:swf OR ext:fla OR ext:xml"
                  }
    GOOGLE_MAX_PAGE = 100   # Max results per page of Google
    BAIDU_DORK = {"subdomain": "site:{}",
                  "install": "inurl:setup site:{}",
                  "redirect": "inurl:redirect site:{}",
                  "sensitive": "filetype:log site:{}",
                  "document": "filetype:txt site:{}",
                  "extension": "filetype:php site:{}"
                  }
    BAIDU_MAX_PAGE = 50   # Max results per page of Baidu
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"
    OUTPUT_PATH = "output/"

    def __init__(self, domain, limit):
        self.domain = domain
        self.limit = limit

    def dork_search(self):
        """
        Searching domains,files and emails with Google and Baidu.
        :return:
        """
        for doc, value in InfoDork.GOOGLE_DORK.items():
            print("[-] Executing to Google [%s]" % doc)
            query = urllib.parse.quote_plus(value[0].format(self.domain))
            self.google_search(doc, query)

        for doc, value in InfoDork.BAIDU_DORK.items():
            print("[-] Executing to Baidu [%s]" % doc)
            query = urllib.parse.quote_plus(value[1].format(self.domain))
            self.baidu_search(doc, query)

    def get_query_pages(self, max_page_result):
        """
        Get page count for searching and result count per page.
        :param max_page_result: max results per page.
        :return:
        """
        if self.limit > max_page_result:
            pages = int(math.ceil(self.limit / float(max_page_result)))
            result_page = max_page_result
        else:
            pages = 1
            result_page = self.limit
        return pages, result_page

    def google_search(self, doc, query):
        """
        Google title and url with query string.
        :param doc: document name
        :param query: query string
        :return: None
        """
        search_results = []
        output_file = InfoDork.OUTPUT_PATH + 'g-' + doc + '.txt'
        main_url = "https://www.google.com/search?filter=0&start={0}&q={1}&num={2}"
        header = {'user-agent': InfoDork.USER_AGENT, 'accept-language': 'en-US,en;q=0.5'}
        pages, result_page = self.get_query_pages(InfoDork.GOOGLE_MAX_PAGE)
        result_count = None     # All results count.

        for page in range(pages):
            try:
                result_html = requests.get(main_url.format(page, query, result_page), headers=header, timeout=10)
                parse_html = BeautifulSoup(result_html.text, 'lxml')
            except Exception as err:
                print(err)
                continue
            # Sleep for random seconds.
            sleep(randint(15, 30))
            if result_count is None:
                try:
                    count_text = parse_html.select("#resultStats")[0].children.__next__()
                except Exception as err:
                    print(err)
                    break
                result_count = int(re.search(r'([0-9\'\,]+)', count_text).group(1).replace(',', ''))
            # Print progress line.
            progress = int((page + 1) / float(pages) * 100)
            sys.stdout.write("|" + ">" * progress + "|" + str(progress) + "%\r")
            if progress != 100:
                sys.stdout.flush()
            results = self.google_result_parse(parse_html.select("h3.r a"))
            if len(search_results) + len(results) > self.limit:
                del results[self.limit - len(search_results):]
            search_results += results
        is_subdomain = re.search(r'^site[^\+]*$', query)    # Check searching subdomain.
        if not is_subdomain:
            self.output_file(output_file, search_results)
        else:
            self.output_subdomain(output_file, search_results)

    @staticmethod
    def google_result_parse(results):
        """
        Extract url from searching results.
        :param results: title and whole url list
        :return: title and url list
        """
        item_results = []
        for result in results:
            title = result.get_text()
            domain = result.attrs['href'].split('&sa=')[0][7:]
            item_results.append((title, domain))
        return item_results

    def baidu_search(self, doc, query):
        """
        Baidu title and url with query string.
        :param doc: document type
        :param query: query string
        :return: None
        """
        search_results = []
        output_file = InfoDork.OUTPUT_PATH + 'b-' + doc + '.txt'
        main_url = "https://www.baidu.com/s?ie=utf-8&cl=0&pn={0}&wd={1}&rn={2}"
        header = {'user-agent': InfoDork.USER_AGENT, 'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8'}
        pages, result_page = self.get_query_pages(InfoDork.BAIDU_MAX_PAGE)
        result_count = None     # All results count.

        for page in range(pages):
            try:
                result_html = requests.get(main_url.format(page * result_page, query, result_page), headers=header, timeout=10)
                parse_html = BeautifulSoup(result_html.text, 'lxml')
            except TimeoutError:
                continue
            if result_count is None:
                count_text = parse_html.select(".nums")[0].get_text()
                result_count = int(re.search(r'([0-9\'\,]+)', count_text).group(1).replace(',', ''))
                if result_count == 0:
                    break
            # Print progress line.
            progress = int((page + 1) / float(pages) * 100)
            sys.stdout.write("|" + ">" * progress + "|" + str(progress) + "%\r")
            sys.stdout.flush() if progress != 100 else print('\n')
            # Sleep for random seconds.
            sleep(randint(5, 10))
            results = self.baidu_result_parse(parse_html.select(".t > a"))
            if len(search_results) + len(results) > self.limit:
                del results[self.limit - len(search_results):]
            search_results += results
        is_subdomain = re.search(r'^site[^\+]*$', query)    # Check searching subdomain.
        if not is_subdomain:
            self.output_file(output_file, search_results)
        else:
            self.output_subdomain(output_file, search_results)

    @staticmethod
    def baidu_result_parse(results):
        """
        Extract url from searching results.
        :param results: title and whole url list
        :return: title and url list
        """
        fetcher_threads = deque([])
        item_results = []
        for result in results:
            title = result.get_text()
            redirect_url = result.attrs['href']
            while 1:
                running = 0
                for thread in fetcher_threads:
                    if thread.is_alive():
                        running += 1
                if running < InfoDork.BAIDU_MAX_PAGE:
                    break
            true_url_thread = BaiduUrlThread(title, redirect_url, item_results)
            true_url_thread.start()
            fetcher_threads.append(true_url_thread)
        for thread in fetcher_threads:
            thread.join()
        return item_results

    @staticmethod
    def output_file(file_name, results):
        """
        Output to document with doc name.
        :param file_name: document name
        :param results: searched results.
        :return: None
        """
        with open(file_name, "+a") as f:
            for item in results:
                f.write(item[0] + "\n" + item[1] + "\n\n")

    def output_subdomain(self, file_name, results):
        """
        Output subdomains to document.
        :param file_name: document name
        :param results: searched results
        :return: None
        """
        subdomain_list = []
        for item in results:
            try:
                subdomain = re.search(r'([a-zA-Z\d\-]{1,}\.){2,}[a-zA-Z]{2,}', item[1])
                subdomain_list.append(subdomain.group(0))
            except Exception as err:
                print(err)
        subdomain_list = list(set(subdomain_list))
        with open(file_name, "+a") as f:
            for subdomain in subdomain_list:
                f.write(subdomain + "\n")


def sigint_handler(signum, frame):
    print('You pressed the Ctrl+C.')
    sys.exit(0)


def domain_valid(domain):
    """
    Valid domain function for argument parser.
    :param domain: domain name
    :return: domain name
    """
    is_valid = re.match(r'^[a-zA-Z\d\-]*\.[a-zA-Z\d]*$', domain)
    if not is_valid:
        error_msg = '%s is not a valid domain.' % domain
        raise argparse.ArgumentTypeError(error_msg)
    return domain


if __name__ == '__main__':
    print(InfoDork.__doc__)
    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser(description="Information Dork tool for searching domains,files and emails.")
    parser.add_argument('-l', '--limit', type=int, metavar='limit', default=100,
                        help='results of searching limit(default:%(default)s)')
    parser.add_argument('-d', '--domain', type=domain_valid, metavar='domain', required=True,
                        help='domain name for searching')
    args = parser.parse_args()

    # search information with Google and Baidu.
    engine = InfoDork(args.domain, args.limit)
    engine.dork_search()

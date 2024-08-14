import time
from typing import List, Dict
from urllib.parse import urlparse
from difflib import SequenceMatcher
import requests
from bs4 import BeautifulSoup
import random
from url_checker import check_url_vadidity
import threading
import sys

REQUEST_SLEEP:float = .2

filtered_urls = []

class URL:
    scheme: str
    page: str
    path: str
    parent = None

    def __init__(self, scheme:str, page:str, path:str, parent) -> None:
        self.scheme = scheme
        self.page = page
        self.path = path
        self.parent = parent

    def __repr__(self) -> str:
        return f"{self.scheme}://{self.page}{self.path}"
    
    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        if not isinstance(other, URL):
            # only equality tests to other `structure` instances are supported
            return NotImplemented
        return self.__repr__() == other.__repr__()

tested_urls:List[URL] = []
to_test_urls:List[URL] = []

START = URL("https", "discord.com", "", None)
END = URL("https", "google.com", "", None)


def href_to_url(baseURL:URL, href:str) -> URL:
    if href is None: return None
    if href.startswith("#"): return None
    scheme = baseURL.scheme
    page = baseURL.page
    parsed_href = urlparse(href)
    path = parsed_href.path
    if parsed_href.scheme != "": scheme = parsed_href.scheme
    if parsed_href.netloc != "": page = parsed_href.netloc

    return URL(scheme, page, path, baseURL)

class TimeoutException(Exception):
    pass

def timeout_handler():
    raise TimeoutException()

def find_all_sublinks(url:URL) -> List[URL]:
    global filtered_urls
    #TODO: Wenn Content Type kein html ist oder es generell failt, muss zurück gegeben werden, dass es fehlgeschlgen ist, damit es nicht als bereits gecheckt gilt
    
    try:
        timer = threading.Timer(3, timeout_handler)
        timer.start()
        response = requests.get(url, timeout=3)
        timer.cancel()
    except TimeoutException:
        print(f"Warning Request to {url} had to be terminated because of payload size...")
        return []
    except requests.exceptions.Timeout:
        print(f"Warning Request to {url} timed out...")
        return []
    except:
        print(f"ERROR: Request to {url} crashed")
        return []
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a')
    hrefs = [link.get('href') for link in links]
    urls = [href_to_url(url, href) for href in hrefs if href_to_url(url, href) is not None]

    invalid_urls = list(filter(lambda curl: (not check_url_vadidity(str(curl))) or ("." in curl.path.split("/")[-1] and not curl.path.endswith(".html") and not curl.path.endswith(".php")), urls))
    urls = list(set(urls) - set(invalid_urls))

    filtered_urls += invalid_urls
    while len(filtered_urls)>10:
        filtered_urls.pop(0)
        
    if not url.page in page_sublink_qualities.keys():
        page_sublink_qualities[url.page] = [0, 0]

    page_sublink_qualities[url.page][0] += len([curl for curl in urls if curl.page != url.page])
    page_sublink_qualities[url.page][1] += 1

    return urls

def scanned_domains() -> List[str]:
    return list(set([tested.page for tested in tested_urls]))

def string_similarity(a:str, b:str) -> float:
    s = SequenceMatcher(None, a, b)
    return s.quick_ratio()

pinpoint_mode = False

page_sublink_qualities:Dict[str, List[int]] = {} #page -> [sum, count]

def get_average_sublink_quality(page:str) -> float:
    global page_sublink_qualities
    if page not in page_sublink_qualities.keys():
        return 0
    return page_sublink_qualities[page][0] / page_sublink_qualities[page][1]

def pick_next_page() -> URL:
    global to_test_urls
    already_detected_domains = scanned_domains()
    next = to_test_urls[0]
    
    options = {}
    random.shuffle(to_test_urls)
    for current_url in to_test_urls:
        if current_url.page not in already_detected_domains and current_url.page not in options.keys():
            options[current_url.page] = current_url
    
    if pinpoint_mode:
        best = None
        best_similarity = 0
        
        for page, current_url in options.items():
            similarity = string_similarity(page, str(END))
            if similarity>best_similarity:
                best = current_url
                best_similarity = similarity
        return best
    else:
        if random.random() < 0.7:
            sortd = {k: v for k, v in sorted(page_sublink_qualities.items(), key=lambda item: item[1][0]/item[1][1], reverse=True)}

            if len(sortd) == 0:
                next = random.choice(to_test_urls)
            else:
                page = random.choice(list(sortd.keys())[:3])
                for current_url in to_test_urls:
                    if current_url.page == page:
                        next = current_url
        else:
            ranks = {}
            for page, current_url in options.items():
                total_diff = 0
                for detected_domain in already_detected_domains:
                    current_difference = 1-string_similarity(page, detected_domain)
                    total_diff += current_difference
                ranks[current_url] = total_diff

            most_diff = max(ranks, key=ranks.get)
            next = most_diff
            # x = 0
            # while next.page in already_detected_domains:
            #     next = random.choice(to_test_urls)
            #     x += 1
            #     if x > 100:
            #         break
        to_test_urls.remove(next)
        return next

def scan_page():
    global to_test_urls, tested_urls
    target_url:URL = pick_next_page()
    tested_urls.append(target_url)

    #print(f"(Scanned Domains: {scanned_domains()})")
    #print(f" --- checking {target_url}...")

    detected:List[URL] = find_all_sublinks(target_url)

    new_found:List[URL] = list(set(detected) - set(to_test_urls + tested_urls))

    for cnf in new_found:
        if cnf.page == END.page:
            path = []
            while cnf.parent is not None:
                path.append(cnf)
                cnf = cnf.parent
            path.append(START)
            print(" ### FINISHED ### ")
            print(f"Path: \n{path}")
            sys.exit(0)


    # print(f"detected: {len(detected)}")
    # print(f"new: {len(new_found)}")
    #print(f"toTest: {len(to_test_urls)}")
    to_test_urls += new_found


counter = 0
def run():
    global counter, pinpoint_mode
    while True:
        counter += 1
        if pinpoint_mode and counter>30:
            pinpoint_mode = False
            counter = 0
        elif counter>50:
            pinpoint_mode = True
            counter = 0

        #print(f"{counter} / {pinpoint_mode}")

        scan_page()
        time.sleep(REQUEST_SLEEP)

def start_from(page:URL):
    to_test_urls.append(page)
    run()

if __name__ == "__main__":
    start_from(START)

#!/usr/bin/env python3
from  optparse import OptionParser
import json
from lxml.html.clean import Cleaner
from lxml import html
from urllib.parse import urlparse
import sys
import time
import traceback
import parser_features

def saveErrors(error_file, errors):
    if len(errors) > 0:
        with open(error_file, 'w', encoding="utf-8") as outfile:
            json.dump(errors, outfile, ensure_ascii = False, indent=0)

def main():
    errors = []
    usage = "Использование: %prog [опции] арг"
    parser = OptionParser(usage)
    parser.add_option("-c", "--config",default='in.json', dest="in_file",
                      help="Относительный путь к файлу. in.json По умолчанию: in.json")
    parser.add_option("-o", "--output ",default='out.json', dest="out_file",
                      help="Относительный путь к файлу. out.json По умолчанию: out.json")
    parser.add_option("-e", "--errors ",default='error.json', dest="error_file",
                      help="Относительный путь к файлу. error.json По умолчанию: error.json")

    (options, args) = parser.parse_args()
    try:
        with open(options.in_file, encoding="utf8") as json_file:
            conf = json.load(json_file)

        url = conf['url']
        block_xpaths = conf['selectors']['block']
        category_xpath = conf['selectors']['category']
        link_xpaths = conf['selectors']['link']
        vacancy_title_xpath= conf['selectors']['title']
        tags_selector_path = conf['selectors']['tags']
        text_selector_path = conf['selectors']['text']

    except Exception as e:
        errors.append(str(traceback.format_exc()))
        saveErrors(options.error_file, errors)
        print('Error in in.json')
        exit(0)

    parsed_uri = urlparse(url)
    url_domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)

    driver = parser_features.driver_init()
    links = []
    if (parser_features.open_site(driver,url,block_xpaths)):
        category_tree = html.fromstring(driver.page_source)
        elements = category_tree.xpath(category_xpath)
        if (elements):
            for element in elements:
                try:
                    try:
                        category_href = url_domain + element.attrib['href']
                    except Exception as e:
                        continue
                    parser_features.open_site(driver,category_href,link_xpaths)

                    tree = html.fromstring(driver.page_source)
                    vacancy_hrefs=tree.xpath(link_xpaths)
                    for vacancy_href in vacancy_hrefs:
                        links.append(url_domain + vacancy_href.attrib['href'])

                except Exception as e:
                    errors.append(str(traceback.format_exc()))

    print('Find %i vacancy'%len(links))

    if len(links) == 0:
        errors.append("Ни один урл не найден")

    answers=[]
    for link in links:
        print('Parse link: ',link)
        answer, errors = parse_vacancy(errors,
                                       driver,
                                       link,
                                       vacancy_title_xpath,
                                       tags_selector_path,
                                       text_selector_path)
        if(answer):
            answers.append(answer)

    print('Parse %i vacancy'%len(links))
    parser_features.driver_close(driver)
    with open(options.out_file, 'w', encoding="utf-8") as outfile:
        json.dump(answers, outfile, ensure_ascii = False, indent=0)

    saveErrors(options.error_file, errors)

def parse_vacancy(errors,
                  driver,
                  link,
                  vacancy_title_xpath,
                  tags_selector_path,
                  text_selector_path):

    if (parser_features.open_site(driver,link,vacancy_title_xpath)):
        vacancy_info = html.fromstring(driver.page_source)

        cleaner = Cleaner()
        cleaner.remove_tags = ['span']
        vacancy_info = cleaner.clean_html(vacancy_info)
        for p in vacancy_info.xpath("//p"):
            p.tail = "\n" + p.tail if p.tail else "\n"
        for br in vacancy_info.xpath("*//br"):
            br.tail = "\n" + br.tail if br.tail else "\n"
        for li in vacancy_info.xpath("*//li"):
            if li.text:
                for i,x in enumerate(li.text):
                    if x.isalpha():
                        li.text = li.text[i:]
                        break
                li.text = "-  " + li.text.capitalize() if li.text else ""
            else:
                if li.getchildren():
                    p = li.getchildren()[0]
                    p.text = "-  " + p.text.capitalize() if p.text else ""
            li.tail = "\n" + li.tail if li.tail else "\n"

        try:
            vacancy_title = vacancy_info.xpath(vacancy_title_xpath)[0].text_content().strip()
        except Exception as e:
            errors.append(link + " Error: " + str(traceback.format_exc()))
            return None, errors

        vacancy_tags = ''
        for elem in vacancy_info.xpath(tags_selector_path):
            if vacancy_tags:
                vacancy_tags += ', '
            vacancy_tags += elem.text_content().strip()

        text_dicts=[]
        requirements_dicts=[]

        try:
            for sel in text_selector_path:
                titles = []
                if sel.get('title'):
                    titles = vacancy_info.xpath(sel['title'])
                texts = vacancy_info.xpath(sel['text'])
                for i in range(0, len(texts)):
                    elem = texts[i]
                    text = elem.text_content().strip()
                    title = ''
                    if i < len(titles):
                        title = titles[i].text_content().strip()
                    if not text:
                        continue
                    sub_title = ''
                    if sel.get('sub_title'):
                        t = elem.xpath(sel['sub_title'])
                        if t:
                            sub_title = t[0].text_content().strip()
                        if text.startswith(sub_title):
                            text = text[len(sub_title):]
                    if not title and sub_title:
                        title = sub_title
                    title_requirements = [
                        'подходите',
                        'приветству',
                        'обязательн',
                        'желательн',
                        'требования',
                        'плюс',
                        'ожидаем',
                        'ждем',
                        'ждём',
                        'понадобятся'
                    ]
                    title = title.strip()
                    text = text.strip()
                    for t in title_requirements:
                        if title.lower().find(t) != -1:
                            requirements_dicts.append({"title": title,"text":text})
                            break
                    if not requirements_dicts:
                        text_dicts.append({"title":title,"text":text})
        except Exception as e:
            errors.append(link + " Error: " + str(traceback.format_exc()))

        return(
            {"Link": link,
             "Title": vacancy_title,
             "Tags": vacancy_tags,
             "Requiremens": requirements_dicts,
             "Text": text_dicts}, errors
            )




if __name__ == '__main__':
    main()

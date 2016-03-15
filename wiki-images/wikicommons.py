#!/usr/bin/env python

"""Get all images of a wikipedia commons category."""

import urllib  # images
import urllib2  # text

import json
import logging
import sys
import xmltodict
import os

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s',
                    level=logging.DEBUG,
                    stream=sys.stdout)


def create_filelist(category):
    """
    Create a list of files in a category.

    Parameters
    ----------
    category : string

    Returns
    -------
    list

    Examples
    --------
    >> wikicommons.create_filelist('Category:Unidentified Convolvulaceae')
    """
    filelist = []
    cats_to_explore = [category]

    catsub = len("Category:")

    while len(cats_to_explore) > 0:
        sub_cat = cats_to_explore.pop()  # Get next category
        sub_filelist = get_direct_files(sub_cat)  # Get direct members
        for el in sub_filelist:
            entry = {'filename': el['filename'],
                     'category': os.path.join(category[catsub:],
                                              el['category'][catsub:])}
            filelist.append(entry)
        # get subcategories
        sub_categories = get_subcategories(sub_cat)
        for el in sub_categories:
            cats_to_explore.append(el)
        logging.info("Done with sub_category '%s' (%i files)",
                     sub_cat,
                     len(sub_filelist))
    return filelist


def get_direct_files(category):
    """Get a list of all files in category."""
    filelist = []
    has_continue = True
    data = {}
    while has_continue:
        base_url = "https://commons.wikimedia.org/w/api.php"
        url = ("{base_url}?action=query&list=categorymembers&cmtype=file"
               "&format=json"
               "&cmtitle={category}"
               .format(base_url=base_url,
                       category=urllib.quote_plus(category.encode('utf-8'))))
        if 'continue' in data:
            url += "&cmcontinue=%s" % data['continue']['cmcontinue']
        response = urllib2.urlopen(url)
        jsondata = response.read()
        data = json.loads(jsondata)
        for el in data['query']['categorymembers']:
            filename = el['title'][len("File:"):]
            filelist.append({'filename': filename,
                             'category': category})
        has_continue = 'continue' in data

    return filelist


def get_image(commons_name, pixels, local_filename):
    """
    Get a single image from Wikipedia Commons.

    Parameters
    ----------
    commons_name : str
    pixels : int
        Maximum dimension for both width and height
    local_filename : str
        Path where the image gets saved.

    Returns
    -------
    None

    Examples
    --------
    >>> get_image('Aurelia-aurita-3.jpg', 250, 'local_name.jpg')
    >>> get_image('Aurelia-aurita-3.jpg', 500, 'local_name_500.jpg')
    """
    base_url = "https://tools.wmflabs.org/magnus-toolserver/commonsapi.php"
    url = ("{base_url}?image={image}&thumbwidth={pixels}&thumbheight={pixels}"
           .format(base_url=base_url,
                   image=urllib.quote_plus(commons_name.encode('utf-8')),
                   pixels=pixels))
    response = urllib2.urlopen(url)
    xmldata = response.read()
    xmldict = xmltodict.parse(xmldata)
    img_url = xmldict['response']['file']['urls']['thumbnail']
    urllib.urlretrieve(img_url, local_filename)


def download_complete_category(category, pixels, local_folder='.'):
    """
    Download all files of a category (recursive).

    Parameters
    ----------
    category : string
    pixels : int
        Maximum size of dimensions of image

    Examples
    --------
    >>> download_complete_category("Category:Ipomoea", 128)
    """
    directory = category[len("Category:"):]
    store_here = os.path.join(local_folder, directory)
    if not os.path.exists(store_here):
        os.makedirs(store_here)
    download_category_files(category, pixels, store_here)
    sub_categories = get_subcategories(category)
    for sub_cat in sub_categories:
        download_complete_category(sub_cat, pixels, store_here)


def download_category_files(category, pixels, local_folder='.'):
    """
    Download all files of a category (non-recursive).

    Parameters
    ----------
    category : string
    pixels : int
        Maximum size of dimensions of image
    local_folder : string
        Put files here.

    Examples
    --------
    >> download_category_files("Category:Close-ups of Ipomoea flowers", 128)
    """
    base_url = "https://commons.wikimedia.org/w/api.php"
    url = ("{base_url}?action=query&list=categorymembers&cmtype=file"
           "&format=json"
           "&cmtitle={category}"
           .format(base_url=base_url,
                   category=urllib.quote_plus(category.encode('utf-8'))))
    response = urllib2.urlopen(url)
    jsondata = response.read()
    data = json.loads(jsondata)
    for el in data['query']['categorymembers']:
        filename = el['title'][len("File:"):]
        logging.info(filename)
        get_image(filename, pixels, os.path.join(local_folder, filename))


def get_subcategories(category):
    """
    Get names of subcategories.

    Parameters
    ----------
    category : string

    Returns
    -------
    list
        Titles of all subcategories.

    Examples
    --------
    >>> get_subcategories("Category:Ipomoea")[0]
    u'Category:Close-ups of Ipomoea flowers'
    """
    base_url = "https://commons.wikimedia.org/w/api.php"
    url = ("{base_url}?action=query&list=categorymembers&cmtype=subcat"
           "&format=json"
           "&cmtitle={category}"
           .format(base_url=base_url,
                   category=urllib.quote_plus(category.encode('utf-8'))))
    response = urllib2.urlopen(url)
    jsondata = response.read()
    data = json.loads(jsondata)
    cats = [el['title'] for el in data['query']['categorymembers']]
    return cats


if __name__ == '__main__':
    import doctest
    doctest.testmod()

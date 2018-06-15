import re
import csv
import requests
import argparse as arg
from bs4 import BeautifulSoup

def get_search_url(city, state, zip_code, beds, baths, min_price, max_price):
    """
    Combines arguments with apartments.com domain to obtain the search url
    for apartment listings with the specified parameters.

    Arguments:
        city: city to search in
        state: state that city is located in
        zip_code: zip code to help narrow down specific areas of a city
        beds: number of bedrooms 
        baths: number of bathrooms
        max_price: maximum price of the apartments
        min_price: minimum price of the apartments
    """
    city_fmt = city.replace(" ", "-")
    domain = "https://www.apartments.com/"

    location = "{0}-{1}-{2}/".format(city_fmt, state, zip_code)
    price_range = "{0}-{1}/"
    
    # format the price_range portion of url based on search parameters
    if min_price:
        price_range = price_range.format(min_price + '-to', max_price)

    elif max_price is None and min_price:
        price_range = price_range.format("over", min_price)
   
    else:
        price_range = price_range.format("under", max_price)

    rooms = "{0}{1}"
    
    # format the rooms portion of the url based on search parameters
    # TODO: passing string parameters to beds and baths results in
    #       TypeError: can only concatenate list (not "str") to list
    if beds and baths:
        if beds == "studios":
            rooms = rooms.format(beds + "-", baths + "-bathrooms-")
        else:
            rooms = rooms.format(beds + "-bedrooms-", baths + "-bathrooms-")

    elif beds is None:
        if baths:
            rooms = rooms.format(_, baths + "-bathrooms-")
        else:
            rooms = rooms.format()

    else:
        if beds == "studios":
            rooms = rooms.format(beds + "-")
        else:
            rooms = rooms.format(beds + "-bedrooms-")

    url = domain + location + rooms + price_range
    return url

def get_soup(url):
    """
    Requests the html of the provided url and returns a BeautifulSoup object
    to be read through later on.

    Arguments:
        url: valid apartments.com search url obtained by get_search_url()
    """
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    return soup

def get_paginated_urls(soup, urls):
    """
    Recursive function that if the search returns paginated results
    it returns all of the search urls, else None.

    Arguments:
        soup: BeautifulSoup object generated from get_soup()
        urls: list of urls to be populated by function
    """
    div_class = "paging"

    try:
        if soup.find('div', class_=div_class):
            url = soup.find('a', class_='next').get('href')
            new_soup = get_soup(url)
            urls.append(url)
            return get_paginated_urls(new_soup, urls)
        else:
            raise ValueError
    except ValueError:
        return urls

def get_div_apartments(soup):
    """
    Takes soup and finds all divs with class propertyInfo that are listed in the
    paginated placards section.

    Arguments:
        soup: the BeautifulSoup object generated from get_soup()

    TODO:
        Deal with pagination...
    """
    url_list = []
    div_class = "propertyInfo"

    div_apartments_list = [soup.find_all("div", class_=div_class)]
    
    if get_paginated_urls(soup, url_list):
        for url in url_list:
            new_soup = get_soup(url)
            div_apartments_list.append(
                new_soup.find_all("div", class_=div_class)
            )
    
    return div_apartments_list

def get_apartment_urls(div_apartments_list):
    """
    Takes ResultSet(s) in div_apartments_list and obtains the urls for each of the
    apartment divs in the ResultSet(s).

    Arguments:
        div_apartments_list: List of ResultSet(s) containing the apartment
            listings that resulted from the apartments.com search.  
    """
    apartment_urls = []
    a_class_regex = "placardTitle js-placardTitle"

    for result in div_apartments_list:
        for div in result:
            try:
                apartment_urls.append(
                    div.find('a', class_=re.compile(a_class_regex)).get('href')
                )
            except AttributeError:
                pass

    return apartment_urls

def get_availability(url):
    """
    Function to handle scraping the availability section information
    from an apartment listing url.

    Arguments:
        url: apartment listing url gathered from get_apartment_urls
    """
    units = []
    section_class_available = "availabilitySection"
    tr_class_row = "rentalGridRow"

    # get units table from apartment url
    soup = get_soup(url)
    availability = soup.find('section', class_=section_class_available)

    # iterate through units table, collecting each unit's data
    for row in availability.find_all('tr', class_=tr_class_row):
        unit_dict = {
            col.get('class')[0]: col.get_text().strip() for col in row.find_all('td')
        }
        units.append(unit_dict)
    return units

def scrape_apartments(apartment_urls):
    """
    Takes apartment urls gathered from main search page soup, gets soup
    for each of those pages and scrapes the table data with listing
    information.

    Arguments:
        apartment_urls: list of apartment listing urls gathered from 
            get_apartment_urls()
    """
    
    section_class_description = "descriptionSection"
    section_class_amenities = "amenitiesSection"
    section_class_contact = "contactSection"




def main():
    parser = arg.ArgumentParser(
                description='Apartment hunter, curates a list of apartment ' \
                            'listings from Apartments.com'
            )
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
        help='Enables debugging output and extra verbosity')
    parser.add_argument('--city', type=str, nargs=1, default='los angeles')
    parser.add_argument('--state', type=str, nargs=1, default='ca')
    parser.add_argument('--zip_code', type=str, nargs=1, default='90034')
    parser.add_argument('--beds', type=str, nargs=1, default='2') 
    parser.add_argument('--baths', type=str, nargs=1, default='2')
    parser.add_argument('--min_price', type=str, nargs=1, default=None)
    parser.add_argument('--max_price', type=str, nargs=1, default='2500')
    args = parser.parse_args()
    
    url = get_search_url(
            args.city,
            args.state,
            args.zip_code,
            args.beds,
            args.baths,
            args.min_price,
            args.max_price
        )

    if args.verbose:
        for key, item in vars(args).items():
            print('===== {0}: {1} ====='.format(key, item))
        print(url)   

    soup = get_soup(url)
    apartments = get_div_apartments(soup)
    apartment_urls = get_apartment_urls(apartments)
    units = get_availability('https://www.apartments.com/the-woodmere-los-angeles-ca/s98phx5/')
    for unit in units:
        print(unit, '\n' * 2)
    print(len(units))


if __name__ == "__main__":
    main()
    
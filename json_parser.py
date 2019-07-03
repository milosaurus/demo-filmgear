"""
A Simple JSON parsing module for demonstration to FilmGear
"""
import math
import sys
import getopt
import json

from decimal import Decimal
from datetime import datetime

# External Imports
import requests


_POUNDS_TO_KG = 2.205

class ShopifyProduct(json.JSONEncoder):
    """
    The Shopify Product definition
    """

    # ParseHUB -> Shopify field map
    __PRODUCT_KEY_MAP = {
        'vendor': 'vendor',
        'title': 'title',
        'body_html': 'body_html',
    }

    def __init__(
        self,
        product_dict):
        """
        Initialisation code for a Shopify Product
        """
        keys = self.__PRODUCT_KEY_MAP.keys()

        # Automatically pulled fields
        for key in keys:

            # Check whether value is in the product data
            if key in product_dict:
                setattr(
                    self,
                    self.__PRODUCT_KEY_MAP.get(key),
                    product_dict[key])

        # Manually set fields
        if 'breadcrumbs' in product_dict.keys():
            setattr(self, 'product_type', self.__get_product_type(product_dict['breadcrumbs']))
            setattr(self, 'tags', self.__get_tag_list(product_dict['breadcrumbs']))

        # setattr(self, 'handle', self.__title_to_handle(getattr(self, 'title')))
        setattr(self, 'published_scope', 'global')
        setattr(self, 'template_suffix', '')

        # TODO?
        # updated_at?
        # published_at?

        # Set variants
        variants = []
        variants.append(self.__set_product_variants(product_dict))
        setattr(self, 'variants', variants)

        # Set Options
        setattr(self, 'options', self.__set_product_options(product_dict))

        # Set Images
        product_images = self.__set_product_images(product_dict)

        if product_images is not None:
            # Set Images
            setattr(self, 'images', product_images)

            # Set Image
            setattr(self, 'image', product_images[0])

    def __get_product_type(self, breadcrumbs):
        """
        Get product type from Breadcrumbs
        """
        print(breadcrumbs)
        return breadcrumbs[len(breadcrumbs) - 2]['breadcrumb']


    __EXCLUDED_BREADCRUMBS = [
        'Home'
    ]

    def __get_tag_list(self, breadcrumbs):
        """
        Get tags from Breadcrumbs
        """
        tags = ''

        for breadcrumb in breadcrumbs:
            if breadcrumb['breadcrumb'] not in self.__EXCLUDED_BREADCRUMBS:
                tags = tags + breadcrumb['breadcrumb'] + ', '

        return tags[:-2]

    def __title_to_handle(self, title):
        """
        Helper method to convert title to handle
        """
        handle = title.replace('"', '')
        handle = handle.replace('\\', '')
        handle = handle.replace(' ', '-')
        return handle.lower()

    __MASTER_DEALER_LIST = [
        'avenger',
        'smallhd',
        'wooden camera',
        'teradek',
        'paralinx',
        'atomos',
        'oconnor',
        'vinten',
        'sacthler',
        'litepanels',
        'offhollywood',
        'anton bauer',
        'core swx',
        'autocue',
        'autoscript',
        'manfrotto'
    ]

    def __set_product_variants(self, product_dict):
        """
        Sets the variants in the shopify product
        """
        product_variants = {}
        product_variants['title'] = 'Default Title'

        if 'sku' in product_dict.keys():
            product_variants['sku'] = product_dict['sku']

        if 'barcode' in product_dict.keys():
            product_variants['barcode'] = product_dict['barcode']

        # Options
        product_variants['option1'] = 'Default Title'
        product_variants['option2']: None
        product_variants['option3']: None

        # Taxable Setting
        # TODO: True -> true serialization
        product_variants['taxable'] = True

        if 'barcode' in product_dict.keys() and \
                product_dict['vendor'].lower() in self.__MASTER_DEALER_LIST:
            product_variants['fulfillment_service'] = 'master_dealer'

        product_variants['inventory_management'] = 'shopify'

        # Initialisation
        product_weight = 0

        # Weight conversion
        if 'weight' in product_dict.keys():
            # Do weight conversion and add it to the product

            if product_dict['weight'] != "":
                product_weight = self.__weight_conversion(product_dict['weight'], product_dict['unit'])
                product_variants['grams'] = int(product_weight * 1000)
                product_variants['weight'] = product_weight
                product_variants['weight_unit'] = 'kg'

        # created_at? Shopify fields
        # updated_at?
        product_variants['requires_shipping'] = True
        product_variants['inventory_quantity'] = 0 # Set to 0 or 1
        product_variants['old_inventory_quantity'] = 0 # Set to 0 or 1
        product_variants['inventory_policy'] = 'continue'

        # Price calculation:
        if 'price' in product_dict.keys():
            product_variants['price'] = self.__calculate_price(product_dict['price'], product_weight)

        return product_variants

    def __weight_conversion(self, weight, unit):
        """
        Helper method to convert weight from pounds to
        """
        product_weight = Decimal(str(weight))
        converted_weight = None

        if unit == 'lb':
            converted_weight = product_weight / Decimal(str(_POUNDS_TO_KG))
        else:
            converted_weight = product_weight

        # Convert weight to float and round to 3 decimal places
        return round(float(converted_weight), 3)

    def __calculate_price(self, price, weight):
        """
        Helper method for calculating the price of a product
        """
        fedex_rate = self.__calcluate_fedex_rate(weight)
        # Add in fees/duties?
        total_price = float(price.replace(',','').replace('$','')) + float(fedex_rate)

        query_params = {
            'a' : total_price,
            'symbols' : 'ZAR',
            'base': 'USD'
        }

        r = requests.get(url='http://api.fixer.io/latest', params=query_params)
        data = r.json()

        currency_conversion_rate = float(data['rates']['ZAR'])
        converted_price = total_price * currency_conversion_rate

        return round(converted_price, 2)

    __FEDEX_CONVERSION_CHART = {
        0.0 : {
            0.0  : 0.0,
            0.5  : 31.88736,
            1.0  : 62.91456,
            1.5  : 91.60704,
            2.0  : 123.43296,
            2.5  : 141.49632,
            3.0  : 152.24832,
            3.5  : 163.00032,
            4.0  : 173.75232,
            4.5  : 184.50432,
            5.0  : 195.25632,
            5.5  : 201.5232,
            6.0  : 207.79008,
            6.5  : 214.05696,
            7.0  : 220.32384,
            7.5  : 226.59072,
            8.0  : 232.8576,
            8.5  : 239.12448,
            9.0  : 245.39136,
            9.5  : 251.65824
        },
        10.0 : {
            10.0 : 257.92512,
            0.5: 5.89824
        },
        21.0 : {
            21.0: 388.17792,
            0.5: 6.38976
        },
        45.0 : {
            45.0 : 695.25504,
            0.5: 6.7584
        },
        70.5 : {
            70.5: 1039.93344,
            1.0: 14.7456
        }
    }
    def __calcluate_fedex_rate(self, weight):
        """
        Helper method to calculate the fedex rate for a given product's weight
        """
        rounded_weight = math.ceil(weight * 2.0) / 2.0
        weight_keys = self.__FEDEX_CONVERSION_CHART.keys()

        index = 0.0

        # Get the FEDEX Weight diff
        for weight_index in weight_keys:
            if rounded_weight > weight_index:
                index = weight_index
            else:
                break

        dollar_amount = 0.0

        if index == 0.0:
            # If the weight is between 0 and 10 we get the straight amount from the dict
            dollar_amount = self.__FEDEX_CONVERSION_CHART[index][rounded_weight]
        else:
            initial_amount = self.__FEDEX_CONVERSION_CHART[index][index]
            # Get remaining weight diff:
            remaining_weight = rounded_weight - index

            # need to get this from the keys
            weight_diff = 0.5

            weight_multiplier = remaining_weight / weight_diff

            dollar_amount = initial_amount + \
                            (weight_multiplier * self.__FEDEX_CONVERSION_CHART[index][weight_diff])

        return dollar_amount

    def __set_product_options(self, product_dict):
        """
        Sets the options in the shopify product
        """
        options = {}
        options['name'] = 'Title'
        options['position'] = 1
        options['values'] = ['Default Title']

        return options

    def __set_product_images(self, product_dict):
        """
        Sets the images in the shopify product
        """
        shopify_images = []

        if 'images' not in product_dict:
            return None

        images = product_dict['images']

        position = 1

        for image in images:
            shopify_image = {}
            shopify_image['position'] = position

            # TODO: get these properly
            shopify_image['width'] = 500
            shopify_image['height'] = 500

            # TODO:
            # Updated At
            # Created At?

            shopify_image['src'] = image['src']
            shopify_image['variant_ids'] = []

            # Add it to the list of shopify images
            shopify_images.append(shopify_image)

            # Increment position
            position+=1

        return shopify_images

def main(argv):
    """
    A basic method to showcase JSON parsing functionality
    """

    inputfile = ''

    try:
        opts, args = getopt.getopt(argv, "hi:")
    except getopt.GetoptError:
        print('json_parser.py -i <inputfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <inputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg

    print('[DEBUG] Input file is "', inputfile)

    data = ''

    print('[INFO] Time Started: ' + str(datetime.now()))

    with open(inputfile) as data_file:
        data = json.load(data_file)

    shopify_products = []

    # Iterate through each URL in the file
    for url in data['urls']:
        for product in url['products']:
            shop_product = ShopifyProduct(product)
            shopify_products.append(shop_product)

    # shop_product = ShopifyProduct(data['urls'][0]['products'][0])
    # shopify_products.append(shop_product)

    jsonstring = '{\"products\": ['
    for product in shopify_products:
        jsonstring = jsonstring + json.dumps(product.__dict__) + ','
    jsonstring = jsonstring[:-1] + ']}'

    filename = 'shopify_' + datetime.now().strftime("%Y-%m-%d_%H%M%S") + '.json'

    outfile = open(filename, 'w')
    outfile.write(json.dumps(json.loads(jsonstring), indent=4, sort_keys=True))
    outfile.close()

    print('[INFO] Time Ended: ' + str(datetime.now()))
    print('[DEBUG] File parsing complete')

if __name__ == "__main__":
    main(sys.argv[1:])

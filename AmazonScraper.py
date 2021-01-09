from bs4 import BeautifulSoup
from seleniumwire import webdriver
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd

url = "https://www.amazon.de/gp/bestsellers/ref=zg_bs_unv_0_boost_1"

API_KEY = "CkcNsk8r6BcCWfta"

http_proxy = f"http://suli:{API_KEY}@proxy.packetstream.io:31112"
https_proxy = f"http://suli:{API_KEY}@proxy.packetstream.io:31112"

options = {
    'proxy': {
        'http': http_proxy,
        'https':https_proxy, 
        'no_proxy': 'localhost,127.0.0.1' # excludes
    }
    }

count_limit = 10000

categories_to_scrape = ["Auto & Motorrad", "Baby", "Games"]

proxy_interval = 5

def initialize_driver():

	option = webdriver.ChromeOptions()
	chrome_prefs = {}
	option.experimental_options["prefs"] = chrome_prefs
	chrome_prefs["profile.default_content_settings"] = {"images": 2}
	chrome_prefs["profile.managed_default_content_settings"] = {"images": 2}
	driver = webdriver.Chrome(options=option, seleniumwire_options=options)
	# driver.get("https://ipv4.icanhazip.com/")
	# time.sleep(2)
	# driver.get("https://ipv4.icanhazip.com/")
	# print("Proxy: ", driver.find_element_by_tag_name("body").text)
	return driver

driver = initialize_driver()

index = 0
count = 0

limit_reached = False

def scrape_data(url, df, depth = 0, broadest_category = None):

	global index
	global count
	global limit_reached
	global driver

	driver.get(url)

	nav = driver.find_element_by_id("zg_browseRoot")

	lis = nav.find_element_by_tag_name("ul")
	for i in range(0, depth):
		try:
			lis = lis.find_element_by_tag_name("ul")
		except:
			return df

	new_lis = lis.find_elements_by_tag_name("li")

	while True:
		try:
			li_links = [li.find_element_by_tag_name("a").get_attribute("href") for li in new_lis]
			li_names = [li.find_element_by_tag_name("a").text for li in new_lis]
			break
		except:
			try:
				lis = lis.find_element_by_tag_name("ul")
				new_lis = lis.find_elements_by_tag_name("li")
			except:
				return df


	for link, name in zip(li_links, li_names):


		if depth == 0:
			if name not in categories_to_scrape:
				continue
			broadest_category = name

		driver.get(link)

		ol = driver.find_element_by_id("zg-ordered-list").find_elements_by_tag_name("li")

		ol_links = []
		for box in ol:
			try:
				ol_links.append(box.find_element_by_tag_name("a").get_attribute("href"))
			except:
				pass

		next_page_link = driver.find_element_by_class_name("a-pagination").find_element_by_class_name("a-last").find_element_by_tag_name("a").get_attribute("href")

		driver.get(next_page_link)


		for box in ol:
			try:
				ol_links.append(box.find_element_by_tag_name("a").get_attribute("href"))
			except:
				pass

		for ol_link in ol_links:

			if count % proxy_interval == 0 and count != 0:
				driver.quit()
				driver = initialize_driver()

			driver.get(ol_link)

			try:
				rank = 0
				rows = driver.find_element_by_id("productDetails_detailBullets_sections1").find_elements_by_tag_name("tr")
				for row in rows:
					if "Bestseller" in row.text:
						rank = int(row.find_element_by_tag_name("td").text.split("in")[0].split("Nr.")[1].strip().replace(",", ""))
						break

				if rank == 0:
					raise IndexError
			except:
				try:
					uls = driver.find_element_by_id("detailBulletsWrapper_feature_div").find_elements_by_tag_name("ul")
					for ul in uls:
						if "Bestseller" in ul.text:
							rank = int(ul.text.split("in")[0].split("Nr.")[1].strip().replace(",", ""))
							break
				except:
					rank = 0
				
			count += 1



			if count > count_limit:
				limit_reached = True
				return df
		

			if rank > 1000:
				print("Rank " + str(rank) + " is greater than 1000")
				continue

			try:
				description = driver.find_element_by_id("productTitle").text
			except:
				description = driver.title

			try:
				price = driver.find_element_by_id("price_inside_buybox").text
			except:
				try:
					price = driver.find_element_by_id("buyNew_noncbb").text.strip()
				except:
					price = "No Price"

			try:
				sold_by = driver.find_element_by_id("bylineInfo").text
			except:
				sold_by = "None"

			try:
				merchant = driver.find_element_by_id("merchant-info").text
			except:
				try:
					merchant = driver.find_element_by_id("sellerProfileTriggerId").text
				except:
					merchant = "None"

			try:
				asin = driver.find_element_by_id("productDetails_detailBullets_sections1").find_elements_by_tag_name("tr")[0].find_element_by_tag_name("td").text
			except:
				try:
					lis = driver.find_element_by_id("detailBulletsWrapper_feature_div").find_elements_by_tag_name("li")
					for li in lis:
						if "ASIN" in li.text:
							asin = li.text.split(":")[1]
							break
				except:
					asin = None

			try:
				reviews_count = driver.find_element_by_id("acrCustomerReviewText").text.split()[0]
			except:
				reviews_count = "None"

			df.loc[index, "Product Link"] = ol_link
			df.loc[index, "Product Title"] = description
			df.loc[index, "Sold by"] = sold_by
			df.loc[index, "Merchant"] = merchant
			df.loc[index, "Price"] = price
			df.loc[index, "ASIN"] = asin
			df.loc[index, "Review Count"] = reviews_count
			df.loc[index, "BSR in broadest_category"] = rank
			df.loc[index, "Broadest Category"] = broadest_category

			index += 1

		df =  scrape_data(link, df, depth + 1, broadest_category)

		if limit_reached:
			return df

	return df




df = pd.DataFrame()


df = scrape_data(url, df)

df.to_excel("results.xlsx", index = False)

driver.quit()








from dataclasses import dataclass, field
import re
from realestate_com_au.utils import delete_nulls


@dataclass
class Listing:
    id: str
    listing_type: str
    raw: dict
    url: str
    suburb: str
    state: str
    postcode: str
    short_address: str
    full_address: str
    property_type: str
    prices: dict
    bedrooms: int
    bathrooms: int
    parking_spaces: int
    building_size: int
    building_size_unit: str
    land_size: int
    land_size_unit: str
    listing_company_id: str
    listing_company_name: str
    listing_company_phone: str
    auction_date: str
    sold_date: str
    description: str
    listers: list = field(default_factory=list)


@dataclass
class Lister:
    id: str
    name: str
    agent_id: str
    job_title: str
    url: str
    phone: str
    email: str


def parse_price_text(price_display_text):
    regex = r".*\$([0-9\,\.]+(?:k|m)*).*"
    price_groups = re.search(regex, price_display_text)
    price_text = (
        price_groups.groups()[0] if price_groups and price_groups.groups() else None
    )
    if price_text is None:
        return None

    price = None
    if price_text[-1] == "k":
        price = float(price_text[:-1].replace(",", ""))

        price *= 1000
    elif price_text[-1] == "m":
        price = float(price_text[:-1].replace(",", ""))
        price *= 1000000
    else:
        price = float(price_text.replace(",", "").split('.')[0])

    return int(price)


def parse_phone(phone):
    if not phone:
        return None
    return phone.replace(" ", "")


def parse_description(description):
    if not description:
        return None
    # return description.replace("<br/>", "\n")
    return description

def parse_prices(listing):
    prices = {
        "BuyPrice": {"text": "", "value": None},
        "SoldPrice": {"text": "", "value": None},
    }
    price_text = listing.get("price", {}).get("display", "")
    prices[listing["price"]["__typename"]] = {
        "text": price_text,
        "value": parse_price_text(price_text),
    }
    return prices

def get_lister(lister):
    lister = delete_nulls(lister)
    lister_id = lister.get("id")
    name = lister.get("name")
    agent_id = lister.get("agentId")
    job_title = lister.get("jobTitle")
    url = lister.get("_links", {}).get("canonical", {}).get("href")
    phone = parse_phone(lister.get("preferredPhoneNumber"))
    email = lister.get("email")  # TODO untested, need to confirm
    return Lister(
        id=lister_id,
        name=name,
        agent_id=agent_id,
        job_title=job_title,
        url=url,
        phone=phone,
        email=email,
    )


def get_listing(listing):
    listing = delete_nulls(listing)
    # delete null keys for convenience

    property_id = listing.get("id")
    listing_type = listing.get("raw", {}).get("__typename", "")
    url = listing.get("_links", {}).get("canonical", {}).get("href")
    address = listing.get("address", {})
    suburb = address.get("suburb")
    state = address.get("state")
    postcode = address.get("postcode")
    short_address = address.get("display", {}).get("shortAddress")
    full_address = address.get("display", {}).get("fullAddress")
    property_type = listing.get("propertyType", {}).get("id")
    listing_company = listing.get("listingCompany", {})
    listing_company_id = listing_company.get("id")
    listing_company_name = listing_company.get("name")
    listing_company_phone = parse_phone(listing_company.get("businessPhone"))
    features = listing.get("generalFeatures", {})
    bedrooms = features.get("bedrooms", {}).get("value")
    bathrooms = features.get("bathrooms", {}).get("value")
    parking_spaces = features.get("parkingSpaces", {}).get("value")
    property_sizes = listing.get("propertySizes", {})
    building_size = property_sizes.get("building", {}).get("displayValue")
    building_size_unit = property_sizes.get("building", {}).get("sizeUnit", {}).get("displayValue")
    land_size = property_sizes.get("land", {}).get("displayValue")
    land_size_unit = property_sizes.get("land", {}).get("sizeUnit", {}).get("displayValue")
    prices = parse_prices(listing)
    sold_date = listing.get("dateSold", {}).get("display")
    auction = listing.get("auction", {}) or {}
    auction_date = auction.get("dateTime", {}).get("value")
    description = parse_description(listing.get("description"))
    listers = [get_lister(lister) for lister in listing.get("listers", [])]

    return Listing(
        id=property_id,
        listing_type=listing_type,
        raw=listing,
        url=url,
        suburb=suburb,
        state=state,
        postcode=postcode,
        short_address=short_address,
        full_address=full_address,
        property_type=property_type,
        listing_company_id=listing_company_id,
        listing_company_name=listing_company_name,
        listing_company_phone=listing_company_phone,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        parking_spaces=parking_spaces,
        building_size=building_size,
        building_size_unit=building_size_unit,
        land_size=land_size,
        land_size_unit=land_size_unit,
        prices=prices,
        auction_date=auction_date,
        sold_date=sold_date,
        description=description,
        listers=listers,
    )

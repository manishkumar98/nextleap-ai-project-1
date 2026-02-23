import math

from phase1_data_ingestion.cleaning import (
    parse_rating,
    parse_cost_for_two,
    normalize_bool,
    normalize_cuisines,
    clean_record,
)


def test_parse_rating_valid_and_invalid():
    assert parse_rating("4.1/5") == 4.1
    assert parse_rating("3.5") == 3.5
    assert parse_rating("NEW") is None
    assert parse_rating("-") is None
    assert parse_rating("") is None
    assert parse_rating(None) is None


def test_parse_cost_for_two_variants():
    assert parse_cost_for_two("800") == 800
    assert parse_cost_for_two("1,200") == 1200
    assert parse_cost_for_two("") is None
    assert parse_cost_for_two(None) is None
    assert parse_cost_for_two("abc") is None


def test_normalize_bool_variants():
    assert normalize_bool("Yes") is True
    assert normalize_bool("no") is False
    assert normalize_bool("Y") is True
    assert normalize_bool("N") is False
    assert normalize_bool("") is None
    assert normalize_bool(None) is None
    assert normalize_bool("maybe") is None


def test_normalize_cuisines_deduplicates_and_trims():
    value = normalize_cuisines("North Indian, Chinese, north indian ,  Chinese ")
    # Order should preserve first occurrences
    assert value == "North Indian, Chinese"


def test_clean_record_maps_fields_and_parses_values():
    raw = {
        "name": "Test Restaurant",
        "url": "http://example.com",
        "address": "123 Street",
        "location": "Banashankari",
        "listed_in(city)": "Banashankari",
        "listed_in(type)": "Buffet",
        "rest_type": "Casual Dining",
        "online_order": "Yes",
        "book_table": "No",
        "rate": "4.2/5",
        "votes": 100,
        "approx_cost(for two people)": "1,000",
        "cuisines": "North Indian, Chinese",
        "dish_liked": "Paneer Tikka",
        "reviews_list": "[]",
        "menu_item": "[]",
        "phone": "1234567890",
    }

    cleaned = clean_record(raw)
    assert cleaned["name"] == "Test Restaurant"
    assert cleaned["location"] == "Banashankari"
    assert cleaned["listed_in_city"] == "Banashankari"
    assert cleaned["listed_in_type"] == "Buffet"
    assert cleaned["online_order"] is True
    assert cleaned["book_table"] is False
    assert math.isclose(cleaned["rating"], 4.2)
    assert cleaned["votes"] == 100
    assert cleaned["approx_cost_for_two"] == 1000
    assert cleaned["cuisines"] == "North Indian, Chinese"


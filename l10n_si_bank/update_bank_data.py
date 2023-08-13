import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests

URL = "https://www.bsi.si/ckfinder/connector?command=Proxy&type=Files&currentFolder=%2FPla%C4%8Dilni%20sistemi%2FSeznam%20identifikacijskih%20oznak%20PPS%2F&fileName=Seznam-identifikacijskih-oznak-PPS.txt"
OUTPUT_FILE = Path(__file__).parent / "data" / "res_bank_data.xml"


@dataclass
class Bank:
    id: str
    name: str
    bic: str
    address: str
    city: str
    zip: str


def get_data():
    resp = requests.get(URL)
    resp.raise_for_status()
    resp.encoding = "windows-1250"
    reader = csv.DictReader(resp.text.splitlines(), delimiter=";")

    # Keep only the first row for each BIC, the rest are branches
    bics = set()

    banks = []
    for row in reader:
        if row["BIC11"] in bics:
            continue
        bics.add(row["BIC11"])

        banks.append(
            Bank(
                id=row["NACIONALNA IDENTIFIKACIJSKA OZNAKA"],
                name=row["NAZIV"],
                address=row["NASLOV"],
                city=row["KRAJ"],
                zip=row["POŠTNA STEVILKA"],
                bic=row["BIC11"],
            )
        )

    return banks


def banks_to_xml(banks: list[Bank]):
    banks_xml = ""
    for bank in banks:
        bank_xml = f"""
    <record id="res_bank_{bank.bic}" model="res.bank">
        <field name="country" ref="base.si" />
        <field name="bic">{bank.bic}</field>
        <field name="name">{bank.name}</field>
        <field name="zip">{bank.zip}</field>
        <field name="city">{bank.city}</field>
        <field name="street">{bank.address}</field>
    </record>"""
        banks_xml += bank_xml

    today = date.today().strftime("%d. %m. %Y")
    return f"""\
<?xml version="1.0" encoding="utf-8" ?>
<!--
Last update: {today}
-->
<odoo>\
{banks_xml}
</odoo>
"""


if __name__ == "__main__":
    banks = get_data()
    xml = banks_to_xml(banks)
    with OUTPUT_FILE.open("w") as f:
        f.write(xml)

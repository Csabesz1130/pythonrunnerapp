import logging
import re

def validate_company_data(data):
    logging.info(f"Validating company data: {data}")
    errors = []

    # Company Name validation
    if not data.get("CompanyName"):
        errors.append("Company Name is required.")
        logging.warning("Company Name is missing")
    elif len(data["CompanyName"]) < 2:
        errors.append("Company Name must be at least 2 characters long.")
        logging.warning(f"Company Name too short: {data['CompanyName']}")

    # Program Name validation
    if not data.get("ProgramName"):
        errors.append("Program Name is required.")
        logging.warning("Program Name is missing")

    # Quantity validation
    if "quantity" in data:
        try:
            quantity = int(data["quantity"])
            if quantity < 0:
                errors.append("Quantity must be a non-negative integer.")
                logging.warning(f"Invalid quantity: {quantity}")
        except ValueError:
            errors.append("Quantity must be a valid integer.")
            logging.warning(f"Non-integer quantity: {data['quantity']}")

    # Felderítés validation
    valid_felderites = ["TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"]
    if data.get("1") not in valid_felderites:
        errors.append(f"Felderítés must be one of: {', '.join(valid_felderites)}")
        logging.warning(f"Invalid Felderítés value: {data.get('1')}")

    # Telepítés validation
    valid_telepites = ["KIADVA", "KIHELYEZESRE_VAR", "KIRAKVA", "HELYSZINEN_TESZTELVE", "STATUSZ_NELKUL"]
    if data.get("2") not in valid_telepites:
        errors.append(f"Telepítés must be one of: {', '.join(valid_telepites)}")
        logging.warning(f"Invalid Telepítés value: {data.get('2')}")

    # Boolean fields validation
    boolean_fields = ["3", "4", "5", "6", "7", "8", "9"]
    for field in boolean_fields:
        if field in data and not isinstance(data[field], bool):
            errors.append(f"Field {field} must be a boolean value.")
            logging.warning(f"Non-boolean value for field {field}: {data[field]}")

    logging.info(f"Validation complete. Errors: {errors}")
    return errors

def validate_bulk_edit(field, value):
    logging.info(f"Validating bulk edit - Field: {field}, Value: {value}")
    errors = []

    if not field:
        errors.append("Field to edit is required.")
        logging.warning("Field to edit is missing")
    if value is None or value == "":
        errors.append("New value is required.")
        logging.warning("New value is missing")

    # Field-specific validations
    if field == "CompanyName":
        if len(value) < 2:
            errors.append("Company Name must be at least 2 characters long.")
            logging.warning(f"Invalid Company Name for bulk edit: {value}")
    elif field == "quantity":
        try:
            quantity = int(value)
            if quantity < 0:
                errors.append("Quantity must be a non-negative integer.")
                logging.warning(f"Invalid quantity for bulk edit: {quantity}")
        except ValueError:
            errors.append("Quantity must be a valid integer.")
            logging.warning(f"Non-integer quantity for bulk edit: {value}")
    elif field == "1":  # Felderítés
        valid_felderites = ["TELEPÍTHETŐ", "KIRAKHATÓ", "NEM KIRAKHATÓ"]
        if value not in valid_felderites:
            errors.append(f"Felderítés must be one of: {', '.join(valid_felderites)}")
            logging.warning(f"Invalid Felderítés value for bulk edit: {value}")
    elif field == "2":  # Telepítés
        valid_telepites = ["KIADVA", "KIHELYEZESRE_VAR", "KIRAKVA", "HELYSZINEN_TESZTELVE", "STATUSZ_NELKUL"]
        if value not in valid_telepites:
            errors.append(f"Telepítés must be one of: {', '.join(valid_telepites)}")
            logging.warning(f"Invalid Telepítés value for bulk edit: {value}")
    elif field in ["3", "4", "5", "6", "7", "8", "9"]:  # Boolean fields
        if value.lower() not in ["true", "false", "0", "1"]:
            errors.append(f"{field} must be a boolean value (True/False or 0/1).")
            logging.warning(f"Invalid boolean value for field {field} in bulk edit: {value}")

    logging.info(f"Bulk edit validation complete. Errors: {errors}")
    return errors
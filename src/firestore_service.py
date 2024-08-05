import time
import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging

from google.api_core import retry
from google.cloud.exceptions import NotFound
from google.cloud.firestore_v1.transforms import DELETE_FIELD

class FirestoreService:
    def __init__(self, credentials_path=None):
        if credentials_path is None:
            credentials_path = r"C:\Users\Balogh Csaba\pythonrunnerapp\resources\runnerapp-232cc-firebase-adminsdk-2csiq-331f965683.json"

        if not os.path.exists(credentials_path):
            logging.error(f"Firebase credentials file not found at: {credentials_path}")
            raise FileNotFoundError(f"Firebase credentials file not found at: {credentials_path}")

        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()
        self.company_cache = {}
        logging.info("FirestoreService initialized successfully")

    def get_festivals(self):
        logging.info("Fetching festivals")
        try:
            festivals = self.db.collection('Programs').get()
            result = [festival.to_dict().get('ProgramName', 'Unknown Festival') for festival in festivals]
            logging.info(f"Successfully fetched {len(result)} festivals")
            return result
        except Exception as e:
            logging.error(f"Error fetching festivals: {e}", exc_info=True)
            return []

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def get_companies(self, collection, festival=None):
        cache_key = f"{collection}_{festival}"
        if cache_key in self.company_cache:
            logging.info(f"Returning cached companies for {cache_key}")
            return self.company_cache[cache_key]

        logging.info(f"Fetching companies from Firestore: {collection}, festival: {festival}")
        try:
            companies_ref = self.db.collection(collection)
            if festival and festival != "All Festivals":
                companies_ref = companies_ref.where('ProgramName', '==', festival)

            companies = list(companies_ref.get())

            if not companies:
                logging.warning(f"No companies found in collection: {collection}, festival: {festival}")
                return []

            result = []
            for company in companies:
                try:
                    company_data = company.to_dict()
                    company_data['firestore_id'] = company.id
                    sn_count = self.get_sn_count(collection, company.id)
                    company_data['sn_count'] = sn_count
                    result.append(company_data)
                    logging.debug(f"Processed company: ID={company_data.get('Id', 'N/A')}, Name={company_data.get('CompanyName', 'N/A')}, SN Count={sn_count}")
                except Exception as e:
                    logging.error(f"Error processing company document {company.id}: {e}", exc_info=True)
                    continue

            self.company_cache[cache_key] = result
            logging.info(f"Successfully processed {len(result)} companies")
            return result
        except Exception as e:
            logging.error(f"Error fetching companies: {e}", exc_info=True)
            raise

    def get_sn_count(self, collection, company_id):
        try:
            sn_collection = self.db.collection(collection).document(company_id).collection('SN')
            return len(sn_collection.get())
        except Exception as e:
            logging.error(f"Error getting SN count for company {company_id}: {e}")
            return 0

    def get_company(self, collection, company_id):
        logging.info(f"Fetching company details - Collection: {collection}, ID: {company_id}")
        try:
            # First, try to get the document directly by its Firestore ID
            doc_ref = self.db.collection(collection).document(company_id)
            doc = doc_ref.get()

            if doc.exists:
                company_data = doc.to_dict()
                company_data['firestore_id'] = doc.id
                logging.info(f"Successfully fetched company data for Firestore ID: {company_id}")
                return company_data
            else:
                # If not found, try querying by the 'Id' field
                query = self.db.collection(collection).where('Id', '==', company_id).limit(1)
                docs = query.get()

                if docs:
                    company_data = docs[0].to_dict()
                    company_data['firestore_id'] = docs[0].id
                    logging.info(f"Successfully fetched company data for ID: {company_id}")
                    return company_data
                else:
                    logging.warning(f"No company found with ID: {company_id} in collection: {collection}")
                    return None
        except Exception as e:
            logging.error(f"Error fetching company details: {e}", exc_info=True)
            return None

    def generate_id(self):
        new_id = str(int(time.time() * 1000))
        logging.info(f"Generated new ID: {new_id}")
        return new_id

    def get_sn_list(self, company_id):
        logging.info(f"Fetching SN list for company ID: {company_id}")
        try:
            sn_collection = self.db.collection("Company_Install").document(company_id).collection('SN')
            sn_docs = sn_collection.get()
            sn_list = [doc.to_dict()['SN'] for doc in sn_docs if 'SN' in doc.to_dict()]
            logging.info(f"Fetched {len(sn_list)} SN entries for company {company_id}")
            return sn_list
        except Exception as e:
            logging.error(f"Error fetching SN list for company {company_id}: {e}", exc_info=True)
            return []

    def add_company(self, collection, data):
        try:
            new_doc_ref = self.db.collection(collection).document()
            sn_list = data.pop('SN', [])  # Remove SN from main data
            data['LastModified'] = self.server_timestamp()
            data['LastAdded'] = self.server_timestamp()  # Set LastAdded when creating a new company
            data['CreatedAt'] = self.server_timestamp()
            new_doc_ref.set(data)

            # Add SN documents to subcollection
            for sn in sn_list:
                new_doc_ref.collection('SN').add({'SN': sn})

            return new_doc_ref.id
        except Exception as e:
            logging.error(f"Error adding company: {e}")
            raise

    def update_company(self, collection, company_id, data):
        try:
            # First, try to get the document directly by its Firestore ID
            doc_ref = self.db.collection(collection).document(company_id)
            doc = doc_ref.get()

            if not doc.exists:
                # If not found, try querying by the 'Id' field
                query = self.db.collection(collection).where('Id', '==', company_id).limit(1)
                docs = query.get()

                if not docs:
                    raise ValueError(f"No company found with ID: {company_id}")
                doc_ref = docs[0].reference

            sn_list = data.pop('SN', None)  # Remove SN from main data
            data['LastModified'] = self.server_timestamp()

            # Preserve LastAdded if it exists, otherwise set it
            if 'LastAdded' not in doc_ref.get().to_dict():
                data['LastAdded'] = self.server_timestamp()

            doc_ref.update(self.prepare_data_for_save(data))

            # Update SN list if provided
            if sn_list is not None:
                self.update_sn_list(company_id, sn_list)

            return True
        except Exception as e:
            logging.error(f"Error updating company: {e}")
            raise

    def update_sn_list(self, company_id, sn_list):
        try:
            company_ref = self.db.collection("Company_Install").document(company_id)

            # Delete existing SN documents
            existing_sn_docs = company_ref.collection('SN').get()
            for doc in existing_sn_docs:
                doc.reference.delete()

            # Add new SN documents
            for sn in sn_list:
                company_ref.collection('SN').add({'SN': sn})

            logging.info(f"Successfully updated SN list for company {company_id}")
        except Exception as e:
            logging.error(f"Error updating SN list for company {company_id}: {e}", exc_info=True)
            raise

    def prepare_data_for_save(self, data):
        updated_data = {}
        for key, value in data.items():
            if key in ['Id', 'LastModified']:
                updated_data[key] = value  # Keep these fields but don't modify them
            elif key == 'quantity':
                if value == "":
                    updated_data[key] = None
                elif value is not None:
                    try:
                        updated_data[key] = int(value)
                    except ValueError:
                        updated_data[key] = None  # If conversion fails, set to None
                else:
                    updated_data[key] = None
            elif isinstance(value, bool):
                updated_data[key] = value
            elif value == "Van":
                updated_data[key] = True
            elif value == "Nincs":
                updated_data[key] = False
            elif value is None:
                updated_data[key] = ""  # Convert None to empty string
            else:
                updated_data[key] = value
        return updated_data

    def delete_company(self, collection, company_id):
        logging.info(f"Deleting company - Collection: {collection}, ID: {company_id}")
        try:
            self.db.collection(collection).document(company_id).delete()
            logging.info(f"Successfully deleted company with ID: {company_id}")
        except Exception as e:
            logging.error(f"Error deleting company: {e}", exc_info=True)
            raise

    def add_comment(self, collection, company_id, comment_data):
        logging.info(f"Adding comment - Collection: {collection}, ID: {company_id}")
        logging.debug(f"Comment data: {comment_data}")
        try:
            company_ref = self.db.collection(collection).document(company_id)
            company_ref.update({
                "comments": firestore.ArrayUnion([comment_data])
            })
            logging.info(f"Successfully added comment to company with ID: {company_id}")
        except Exception as e:
            logging.error(f"Error adding comment: {e}", exc_info=True)
            raise

    def server_timestamp(self):
        return firestore.SERVER_TIMESTAMP

    def check_id_exists(self, collection, param):
        pass